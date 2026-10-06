# -*- coding: utf-8 -*-
"""Reproduce the E13 split-category outputs. 复现 E13 类别拆分实验的全部结果表。

This driver chains the split-target dataset construction (``ofns_split.py``) with the
robustness, ablation, count-model, exposure and temporal-window experiments that the
manuscript reports in Supplementary S3.

用法::

    python code/analysis/e13_suite.py                 # 全部步骤
    python code/analysis/e13_suite.py --steps data    # 只重建数据集
    python code/analysis/e13_suite.py --steps temporal

产物（experiments/E13_split_categories/）：
    data/ny_cells_split_r300.csv, ny_cells_drug_alcohol_r{100..500}.csv,
         ny_cells_drug_alcohol_year_r300.csv
    results/drug_alcohol_multiscale.csv, drug_alcohol_robustness.csv,
            drug_alcohol_diagnostics.csv, drug_alcohol_full_diagnostics.csv,
            drug_alcohol_ablation.csv, drug_alcohol_count_models.csv,
            drug_alcohol_exposure.csv, drug_alcohol_temporal.csv,
            drug_alcohol_temporal_bootstrap.csv, split_targets_r300{,_withcoords}.csv,
            split_targets_r300.json
"""
import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
for _p in (REPO / "code", REPO / "code" / "02_features", REPO / "code" / "03_modeling",
           REPO / "code" / "analysis"):
    sys.path.insert(0, str(_p))

import ofns_split as sp  # noqa: E402
from config.settings import RADII  # noqa: E402
from extra_analyses import morans_i, shap_stability  # noqa: E402
from robustness_suite import run_random, run_spatial_blocks, split_features  # noqa: E402
from s6s5_suite import (calibration_pr, count_models, fit_eval,  # noqa: E402
                        feature_groups, matrix, paired_bootstrap)

E13 = REPO / "experiments" / "E13_split_categories"
DATA, RES = E13 / "data", E13 / "results"
SEED = 42
TARGET = "y_drug_alcohol"
MULTISCALE_COLS = ["target", "cells", "zero_ratio", "pos_rate", "AUC", "PR_AUC",
                    "Recall", "R2_pos", "MAE_pos", "AUC_spatial_mean", "radius"]


def cells_path(name, radius):
    return DATA / ("ny_cells_%s_r%d.csv" % (name, radius))


def load_cells(name, radius):
    path = cells_path(name, radius)
    if not path.exists():
        raise SystemExit("missing %s; run --steps data first" % path)
    return pd.read_csv(path)


def write_table(df, name):
    RES.mkdir(parents=True, exist_ok=True)
    path = RES / name
    df.to_csv(path, index=False, encoding="utf-8-sig")
    print("  written: %s" % path, flush=True)
    return path


# ------------------------------------------------------------------- 1. data
def step_data(force=False):
    print("== [1/5] 重建拆分数据集", flush=True)
    # 事件点只读取一次，六个半径共用（按半径分箱的计数互不影响）
    events = sp.load_group_events(("a", "b"))
    for radius in RADII:
        if force or not cells_path("drug_alcohol", radius).exists():
            sp.write_cells(sp.build_cells(radius, groups=("a",), events=events),
                           "drug_alcohol", radius)
        if radius == 300 and (force or not cells_path("split", 300).exists()):
            sp.write_cells(sp.build_cells(300, groups=("a", "b"), events=events),
                           "split", 300)
    print("== [1/5] 完成", flush=True)


# -------------------------------------------------------------- 2. 多尺度
def step_multiscale():
    print("== [2/5] 多尺度与稳健性", flush=True)
    rows, rob = [], []
    for radius in RADII:
        cells = load_cells("drug_alcohol", radius)
        X, _ = split_features(cells)
        y = pd.to_numeric(cells[TARGET], errors="coerce").fillna(0)
        # 多尺度表：与增补 S3 同口径（随机 80/20 + 空间分块均值）
        row = sp.evaluate(cells, TARGET, extra={"radius": radius})
        rows.append({k: row[k] for k in MULTISCALE_COLS})
        # 稳健性表：逐尺度随机划分的完整指标（与 E01 的 run_random 同列）
        r = run_random(X, y, "xgb")
        r["radius"] = radius
        rob.append(r)
        print("  r=%d 随机 AUC=%.4f PR=%.4f 空间分块=%.4f" % (
            radius, r["AUC"], r["PR_AUC"], rows[-1]["AUC_spatial_mean"]), flush=True)
    write_table(pd.DataFrame(rows), "drug_alcohol_multiscale.csv")
    write_table(pd.DataFrame(rob), "drug_alcohol_robustness.csv")


def step_diagnostics():
    print("== 空间诊断与 SHAP 稳定性", flush=True)
    import xgboost as xgb
    from sklearn.model_selection import train_test_split

    diag, full = [], []
    for radius in RADII:
        cells = load_cells("drug_alcohol", radius)
        X, _ = split_features(cells)
        y = pd.to_numeric(cells[TARGET], errors="coerce").fillna(0)
        coords = cells[["school_lon", "school_lat"]].to_numpy()
        m = run_random(X, y, "xgb")
        sp_mean = float(np.mean([s["AUC"] for s in
                                 run_spatial_blocks(X, y, coords, 5, "xgb")]))
        idx = np.arange(len(X))
        tr, te = train_test_split(idx, test_size=0.2, random_state=SEED)
        pos_tr = y.iloc[tr] > 0
        reg = xgb.XGBRegressor(n_estimators=300, max_depth=6, learning_rate=0.05,
                               subsample=0.8, colsample_bytree=0.8, random_state=SEED,
                               n_jobs=-1, objective="count:poisson")
        reg.fit(X.iloc[tr][pos_tr], y.iloc[tr][pos_tr])
        resid = y.iloc[te].to_numpy() - reg.predict(X.iloc[te])
        mi, mp = morans_i(cells[["cell_x", "cell_y"]].to_numpy()[te], resid)
        stab, nf = shap_stability(cells.assign(event_count=y), radius)
        diag.append({"radius": radius, "AUC_spatial_mean": sp_mean,
                     "morans_I_resid": mi, "morans_p": mp,
                     "shap_spearman_mean": stab, "shap_folds": nf,
                     "zero_ratio": float((y == 0).mean()), "cells": len(cells)})
        full.append({"radius": radius, "cells": len(cells),
                     "zero_ratio": float((y == 0).mean()),
                     "AUC": m["AUC"], "PR_AUC": m["PR_AUC"],
                     "AUC_spatial_mean": sp_mean,
                     "morans_I_resid": mi, "morans_p": mp,
                     "shap_spearman": stab, "shap_folds": nf})
        print("  r=%d AUC=%.4f 空间=%.4f Moran=%.4f(p=%.3f) SHAP秩=%.3f" % (
            radius, m["AUC"], sp_mean, mi, mp, stab), flush=True)
    write_table(pd.DataFrame(diag), "drug_alcohol_diagnostics.csv")
    write_table(pd.DataFrame(full), "drug_alcohol_full_diagnostics.csv")


# ------------------------------------------------- 3. 消融 / 计数 / 暴露量
def step_ablation():
    print("== [3/5] 消融、计数模型与暴露量（300 m）", flush=True)
    cells = load_cells("drug_alcohol", 300)
    # 逐年计数列必须剔除，否则第一阶段的特征里会混入历史标签造成泄漏
    X, _ = split_features(cells)
    y = pd.to_numeric(cells[TARGET], errors="coerce").fillna(0)

    # 与增补 S3 同口径：坐标组只含原始经纬度（cell_x/cell_y 属格网编号，不进入模型）
    groups = feature_groups(cells.drop(columns=["cell_x", "cell_y"]), None)
    # 拆分因变量没有“前期同类事件”可用，因此去掉历史基线与历史+宏观两组
    for drop in ("G1_history_only", "G6_history_plus_macro"):
        groups.pop(drop, None)
    rows = []
    prob_full = None
    test_idx = None
    for name, cols in groups.items():
        if not cols:
            continue
        m, prob, extra = fit_eval(matrix(cells, cols, None), y)
        if not m:
            continue
        m.update({"group": name, "n_features": len(cols)})
        rows.append(m)
        if name == "G7_full":
            prob_full, test_idx = prob, extra[0]
        print("  %-24s AUC=%.4f" % (name, m["AUC"]), flush=True)
    write_table(pd.DataFrame(rows), "drug_alcohol_ablation.csv")
    if prob_full is not None:
        fig = calibration_pr("ny", 300, y.iloc[test_idx], prob_full, "drug_alcohol")
        print("  calibration figure: %s" % fig, flush=True)

    cm = count_models(X, y, "ny", 300)
    write_table(cm, "drug_alcohol_count_models.csv")

    road = pd.to_numeric(cells["road_r300"], errors="coerce").replace(0, np.nan)
    rate = (y / road).fillna(0)
    import xgboost as xgb
    from sklearn.metrics import mean_absolute_error, r2_score
    from sklearn.model_selection import train_test_split
    idx = np.arange(len(X))
    tr, te = train_test_split(idx, test_size=0.2, random_state=SEED)
    exp = []
    for name, target in (("count", y), ("rate", rate)):
        pos_tr, pos_te = target.iloc[tr] > 0, target.iloc[te] > 0
        reg = xgb.XGBRegressor(n_estimators=300, max_depth=6, learning_rate=0.05, subsample=0.8,
                               colsample_bytree=0.8, random_state=SEED, n_jobs=-1,
                               objective="count:poisson")
        reg.fit(X.iloc[tr][pos_tr], target.iloc[tr][pos_tr])
        pred = reg.predict(X.iloc[te][pos_te])
        exp.append({"target": name, "R2": float(r2_score(target.iloc[te][pos_te], pred)),
                    "MAE": float(mean_absolute_error(target.iloc[te][pos_te], pred))})
    write_table(pd.DataFrame(exp), "drug_alcohol_exposure.csv")


# --------------------------------------------- 4. 拆分对比表（两个口径）
def step_targets():
    print("== [4/5] 拆分对比表（同格网、同特征）", flush=True)
    cells = load_cells("split", 300)
    coords = cells[["school_lon", "school_lat"]].to_numpy()
    cols = ["target", "cells", "zero_ratio", "pos_rate", "AUC", "PR_AUC", "Recall",
            "R2_pos", "MAE_pos", "AUC_spatial_mean"]
    tables = {}
    for tag, use_main_features in (("", True), ("_withcoords", False)):
        rows = []
        for target in ("y_drug_alcohol", "y_traffic"):
            if use_main_features:
                X, _ = split_features(cells)
                y = pd.to_numeric(cells[target], errors="coerce").fillna(0)
            else:
                X, y = sp.feature_matrix(cells, target, with_coords=True)
            m, _, _ = fit_eval(X, y)
            m.update({"target": target, "cells": len(X),
                      "zero_ratio": float((y == 0).mean()),
                      "pos_rate": float((y > 0).mean()),
                      "n_features": int(X.shape[1]),
                      "AUC_spatial_mean": sp.spatial_auc_mean(X, y, coords),
                      "events": int(y.sum())})
            rows.append(m)
            print("  %-16s AUC=%.4f R2=%.4f spatial=%.4f (n_feat=%d)" % (
                target, m["AUC"], m["R2_pos"], m["AUC_spatial_mean"], m["n_features"]),
                flush=True)
        table = pd.DataFrame(rows)
        tables[tag] = table
        write_table(table[cols], "split_targets_r300%s.csv" % tag)
    if tables[""].shape[0] == 2:
        payload = {r["target"]: {k: r[k] for k in cols if k != "target"}
                   for _, r in tables[""].iterrows()}
        RES.mkdir(parents=True, exist_ok=True)
        (RES / "split_targets_r300.json").write_text(
            json.dumps(payload, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
        print("  written: %s" % (RES / "split_targets_r300.json"), flush=True)


# --------------------------------------------------- 5. 时间窗与配对 bootstrap
def step_temporal():
    print("== [5/5] 时间窗切分与配对 bootstrap", flush=True)
    events = sp.load_group_events(("a",), with_year=True)
    cells, grid = sp.build_grid(300)
    for year in sorted(events["year"].unique()):
        for col, values in sp.count_groups(events, grid, ("a",), year=int(year)).items():
            cells["count_%d" % int(year)] = values
    cells[TARGET] = cells[[c for c in cells.columns if c.startswith("count_")]].sum(axis=1)
    feats = load_cells("drug_alcohol", 300)
    keep = ["school_id", "cell_x", "cell_y"] + [
        c for c in feats.columns if c not in cells.columns and c != "school_id"]
    cells = cells.merge(feats[keep], on=["school_id", "cell_x", "cell_y"],
                        how="left", validate="one_to_one")
    print("  cells=%d zero=%.3f events=%d" % (
        len(cells), float((cells[TARGET] == 0).mean()), int(cells[TARGET].sum())), flush=True)
    cells.to_csv(DATA / "ny_cells_drug_alcohol_year_r300.csv", index=False,
                 encoding="utf-8-sig")
    print("  written: %s (%d rows)" % (DATA / "ny_cells_drug_alcohol_year_r300.csv",
                                       len(cells)), flush=True)

    # 逐年计数列必须剔除，否则第一阶段的特征里会混入历史标签造成泄漏
    X, _ = split_features(cells.drop(columns=[c for c in cells.columns
                                              if c.startswith("count_")]))
    years = [c for c in cells.columns if c.startswith("count_")]
    early = [c for c in years if int(c.split("_")[1]) <= 2018]
    late = [c for c in years if int(c.split("_")[1]) > 2018]
    y_tr, y_te = cells[early].sum(axis=1), cells[late].sum(axis=1)
    import xgboost as xgb
    from sklearn.metrics import average_precision_score, roc_auc_score
    from sklearn.model_selection import train_test_split
    params = dict(n_estimators=300, max_depth=6, learning_rate=0.05, subsample=0.8,
                  colsample_bytree=0.8, random_state=SEED, n_jobs=-1, eval_metric="logloss")

    # 全样本口径：全样本拟合早期标签、全样本预测后期标签（与 robustness_suite.run_temporal 一致）
    p_full = xgb.XGBClassifier(**params).fit(X, (y_tr > 0).astype(int)).predict_proba(X)[:, 1]
    hist = y_tr.to_frame("history")
    p_hist = xgb.XGBClassifier(**params).fit(hist, (y_tr > 0).astype(int)).predict_proba(hist)[:, 1]
    lab_te = (y_te > 0).astype(int)
    auc_full = float(roc_auc_score(lab_te, p_full))
    auc_hist = float(roc_auc_score(lab_te, p_hist))
    delta_all, p_all = paired_bootstrap(lab_te, p_full, p_hist)

    # 80/20 子集口径
    idx = np.arange(len(X))
    tr, te = train_test_split(idx, test_size=0.2, random_state=SEED)
    clf = xgb.XGBClassifier(**params).fit(X.iloc[tr], (y_tr.iloc[tr] > 0).astype(int))
    p_sub_full = clf.predict_proba(X.iloc[te])[:, 1]
    clf_h = xgb.XGBClassifier(**params).fit(hist.iloc[tr], (y_tr.iloc[tr] > 0).astype(int))
    p_sub_hist = clf_h.predict_proba(hist.iloc[te])[:, 1]
    lab_sub = (y_te.iloc[te] > 0).astype(int)
    delta_sub, p_sub = paired_bootstrap(lab_sub, p_sub_full, p_sub_hist)

    boot = pd.DataFrame([
        {"scheme": "temporal_<=2018", "scope": "all_cells", "AUC_full": auc_full,
         "AUC_history_only": auc_hist, "delta": delta_all, "bootstrap_p": p_all,
         "n_eval": int(len(lab_te))},
        {"scheme": "temporal_<=2018", "scope": "random_80_20_subset",
         "AUC_full": float(roc_auc_score(lab_sub, p_sub_full)),
         "AUC_history_only": float(roc_auc_score(lab_sub, p_sub_hist)),
         "delta": delta_sub, "bootstrap_p": p_sub, "n_eval": int(len(lab_sub))},
    ])
    write_table(boot, "drug_alcohol_temporal_bootstrap.csv")
    write_table(pd.DataFrame([
        {"scheme": "random_80_20", "AUC": float(run_random(X, cells[TARGET], "xgb")["AUC"]),
         "PR_AUC": np.nan, "Recall": np.nan},
        {"scheme": "temporal_<=2018", "AUC": auc_full,
         "PR_AUC": float(average_precision_score(lab_te, p_full)), "Recall": np.nan},
    ]), "drug_alcohol_temporal.csv")
    print(boot.round(4).to_string(index=False), flush=True)


STEPS = {"data": step_data, "multiscale": step_multiscale, "diagnostics": step_diagnostics,
         "ablation": step_ablation, "targets": step_targets, "temporal": step_temporal}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--steps", default="all",
                        help="data,multiscale,diagnostics,ablation,targets,temporal 或 all")
    parser.add_argument("--force", action="store_true", help="重建已存在的数据集")
    args = parser.parse_args()
    steps = list(STEPS) if args.steps == "all" else [s.strip() for s in args.steps.split(",")]
    for name in steps:
        if name not in STEPS:
            raise SystemExit("unknown step: %s" % name)
        if name == "data":
            STEPS[name](force=args.force)
        else:
            STEPS[name]()
    print("done", flush=True)


if __name__ == "__main__":
    main()
