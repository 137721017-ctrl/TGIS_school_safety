# -*- coding: utf-8 -*-
"""Intervention scenario simulation (E11). 干预情景模拟。

Quantile-remediation scenarios for the two-stage Hurdle models, evaluated on held-out
cells over five seeds x three algorithms. 分位数整改情景，在留出格网上评估，5 种子 x 3 算法。

Env overrides: SC_SEEDS / SC_ALGOS / SC_NBOOT / SC_OUT.
"""
import json
import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd

CODE = Path(__file__).resolve().parents[1]
for p in (CODE, CODE / "02_features", CODE / "03_modeling"):
    sys.path.insert(0, str(p))
from config.settings import INPUTS  # noqa: E402
from ms_svi_aggregate import load_schools  # noqa: E402
from robustness_suite import split_features  # noqa: E402

REPO = Path(__file__).resolve().parents[2]
E01 = REPO / "experiments" / "E01_multiscale_buffer" / "data"
E11 = Path(os.environ.get("SC_OUT", REPO / "experiments" / "E11_scenario_simulation"))
RES = E11 / "results"
FIG = RES / "figures"
RES.mkdir(parents=True, exist_ok=True)
FIG.mkdir(parents=True, exist_ok=True)
STEP, RADIUS = 100.0, 300
SEEDS = [int(s) for s in os.environ.get("SC_SEEDS", "42,7,2024,101,555").split(",")]
ALGOS = os.environ.get("SC_ALGOS", "xgb,lgbm,rf").split(",")
NBOOT = int(os.environ.get("SC_NBOOT", "500"))

NY_LEVERS = [("ratio_Enclosure_degree_r300", "down", "降低围合度（改善视觉通透性）"),
             ("ratio_Street_furniture_r300", "down", "清理占道人行道的设施"),
             ("shop_density_r300", "down", "减少沿街商业外摆与停车占用")]
HK_LEVERS = [("ratio_Street_furniture_r300", "down", "清理占道人行道的设施"),
             ("shop_density_r300", "down", "减少沿街商业外摆与停车占用")]


# ------------------------------------------------------------------ 造格网
def build_ny_cells(class_name, col):
    from pyproj import Transformer
    from scipy.spatial import cKDTree
    cfg = INPUTS["ny"]
    schools = load_schools("ny")
    tr = Transformer.from_crs("EPSG:4326", "EPSG:32618", always_xy=True)
    sx, sy = tr.transform(schools["school_lon"].to_numpy(), schools["school_lat"].to_numpy())
    left = np.floor((sx.min() - RADIUS) / STEP) * STEP
    bottom = np.floor((sy.min() - RADIUS) / STEP) * STEP
    right = np.ceil((sx.max() + RADIUS) / STEP) * STEP
    top = np.ceil((sy.max() + RADIUS) / STEP) * STEP
    gx = np.arange(left + STEP / 2, right, STEP)
    gy = np.arange(bottom + STEP / 2, top, STEP)
    gxx, gyy = np.meshgrid(gx, gy)
    cx, cy = gxx.ravel(), gyy.ravel()
    tree = cKDTree(np.column_stack([sx, sy]))
    dist, idx = tree.query(np.column_stack([cx, cy]), k=1)
    keep = dist <= RADIUS
    cells = pd.DataFrame({"school_id": idx[keep], "cell_x": cx[keep], "cell_y": cy[keep],
                          "dist_to_school": dist[keep]})
    ncol = int(np.ceil((right - left) / STEP)) + 2
    nrow = int(np.ceil((top - bottom) / STEP)) + 2
    cell_flat = (np.floor((cy - bottom) / STEP).astype(np.int64) * ncol
                 + np.floor((cx - left) / STEP).astype(np.int64))[keep]
    prop = np.zeros(nrow * ncol)
    years = {}
    for year in cfg["event_years"]:
        path = Path(cfg["events_dir"]) / cfg["events_pattern"].format(year=year)
        if not path.exists():
            continue
        d = pd.read_csv(path, low_memory=False,
                        usecols=lambda c: c in ("Crime_classification", "Latitude", "Longitude",
                                                "latitude", "longitude"))
        d.columns = [c.lower() for c in d.columns]
        cls = d["crime_classification"].astype(str).str.strip()
        m = cls.eq(class_name) & d["longitude"].notna() & d["latitude"].notna()
        if not m.any():
            continue
        ex, ey = tr.transform(d.loc[m, "longitude"].to_numpy(), d.loc[m, "latitude"].to_numpy())
        ecol = np.floor((ex - left) / STEP).astype(np.int64)
        row = np.floor((ey - bottom) / STEP).astype(np.int64)
        good = (ecol >= 0) & (row >= 0) & (ecol < ncol) & (row < nrow)
        prop += np.bincount(row[good] * ncol + ecol[good], minlength=nrow * ncol)
        years[year] = np.bincount(row[good] * ncol + ecol[good], minlength=nrow * ncol)
    cells[col] = prop[cell_flat]
    assert int(cells[col].sum()) > 0
    return cells


def features_with_target(cells, target):
    X, _ = split_features(cells)
    y = pd.to_numeric(cells[target], errors="coerce").fillna(0)
    bad = [c for c in X.columns if c.endswith(("_x", "_y"))]
    assert not bad, "特征合并产生重名列：%s" % bad
    assert X.shape[1] >= 17, "特征数异常：%d" % X.shape[1]
    return X, y


# ------------------------------------------------------------------ 模型
def fit_models(Xtr, ytr, algo, seed):
    import xgboost as xgb
    if algo == "xgb":
        clf = xgb.XGBClassifier(n_estimators=300, max_depth=6, learning_rate=0.05, subsample=0.8,
                                colsample_bytree=0.8, random_state=seed, n_jobs=-1, eval_metric="logloss")
        reg = xgb.XGBRegressor(n_estimators=300, max_depth=6, learning_rate=0.05, subsample=0.8,
                               colsample_bytree=0.8, random_state=seed, n_jobs=-1, objective="count:poisson")
    elif algo == "lgbm":
        import lightgbm as lgb
        clf = lgb.LGBMClassifier(n_estimators=300, num_leaves=31, learning_rate=0.05, subsample=0.8,
                                 colsample_bytree=0.8, random_state=seed, n_jobs=-1, verbose=-1)
        reg = lgb.LGBMRegressor(n_estimators=300, num_leaves=31, learning_rate=0.05, subsample=0.8,
                                colsample_bytree=0.8, random_state=seed, n_jobs=-1, verbose=-1,
                                objective="poisson")
    else:
        from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
        clf = RandomForestClassifier(n_estimators=300, max_depth=12, random_state=seed, n_jobs=-1)
        reg = RandomForestRegressor(n_estimators=300, max_depth=12, random_state=seed, n_jobs=-1)
    yb = (ytr > 0).astype(int)
    if yb.nunique() < 2:
        return None, None
    clf.fit(Xtr, yb)
    pos = ytr > 0
    reg.fit(Xtr[pos], ytr[pos])
    return clf, reg


def predict_two_stage(clf, reg, Xte):
    p1 = clf.predict_proba(Xte)[:, 1]
    m = np.clip(reg.predict(Xte), 0, None)
    return p1, m


def perturb(X, lever, direction, kind, thr=None):
    """返回 (扰动后的 X, 受影响格网数, 越界比例)。thr 由训练集算出后传入。"""
    X2 = X.copy()
    v = X[lever]
    if kind == "quartile":
        lo_q, hi_q, target = thr["lo"], thr["hi"], thr["median"]
        if direction == "down":
            mask = v > hi_q
        else:
            mask = v < lo_q
        X2.loc[mask, lever] = target
        return X2, int(mask.sum()), 0.0
    shift = direction == "up" and 1 or -1
    raw = v + shift * thr["sd"]
    clipped = int(((raw < thr["p1"]) | (raw > thr["p99"])).sum())
    X2[lever] = raw.clip(thr["p1"], thr["p99"])
    return X2, len(v), clipped / max(len(v), 1)


def run_city(city, cells, target, levers):
    X, y = features_with_target(cells, target)
    idx = np.arange(len(X))
    rows = []
    for algo in ALGOS:
        for seed in SEEDS:
            rng = np.random.default_rng(seed)
            perm = rng.permutation(idx)
            cut = int(len(idx) * 0.8)
            tr, te = perm[:cut], perm[cut:]
            Xtr, ytr, Xte, yte = X.iloc[tr], y.iloc[tr], X.iloc[te], y.iloc[te]
            clf, reg = fit_models(Xtr, ytr, algo, seed)
            if clf is None:
                continue
            p1_0, m_0 = predict_two_stage(clf, reg, Xte)
            base = p1_0 * m_0
            thr = {}
            for lever, direction, _ in levers:
                v = Xtr[lever]
                thr[lever] = {"lo": float(v.quantile(0.25)), "hi": float(v.quantile(0.75)),
                              "median": float(v.median()), "sd": float(v.std()),
                              "p1": float(v.quantile(0.01)), "p99": float(v.quantile(0.99))}
            for kind in ("quartile", "sd"):
                # 单杠杆
                for lever, direction, label in levers:
                    Xs, n_aff, clipped = perturb(Xte, lever, direction, kind, thr[lever])
                    p1_s, m_s = predict_two_stage(clf, reg, Xs)
                    rows.append(summarise(city, target, label, kind, algo, seed, base, p1_0, m_0,
                                          p1_s, m_s, Xs, Xte, lever, direction, n_aff, clipped))
                # 组合整改（同一 kind 下所有杠杆同时施加）
                Xs = Xte.copy()
                aff = 0
                cl = 0.0
                for lever, direction, _ in levers:
                    Xs, n_aff, cc = perturb(Xs, lever, direction, kind, thr[lever])
                    aff += n_aff
                    cl = max(cl, cc)
                p1_s, m_s = predict_two_stage(clf, reg, Xs)
                rows.append(summarise(city, target, "组合情景（全部措施）", kind, algo, seed,
                                      base, p1_0, m_0, p1_s, m_s, Xs, Xte, None, None, aff, cl))
    return pd.DataFrame(rows)


def summarise(city, target, label, kind, algo, seed, base, p1_0, m_0, p1_s, m_s,
              Xs, Xte, lever, direction, n_aff, clipped):
    scen = p1_s * m_s
    d = scen - base
    d_p1 = (p1_s - p1_0) * m_0
    d_m = p1_0 * (m_s - m_0)
    return {"city": city, "target": target, "scenario": label, "method": kind,
            "algo": algo, "seed": seed,
            "n_test": int(len(d)), "n_cells_affected": int(n_aff),
            "baseline_mean": float(base.mean()), "scenario_mean": float(scen.mean()),
            "delta_mean": float(d.mean()),
            "delta_pct": float(100 * d.mean() / base.mean()),
            "delta_pct_extensive": float(100 * d_p1.mean() / base.mean()),
            "delta_pct_intensive": float(100 * d_m.mean() / base.mean()),
            "share_cells_reduced": float((d < 0).mean()), "clipped_share": float(clipped)}


def bootstrap_ci(city, cells, target, levers):
    """对 XGBoost、seed=42 的代表性实现做格网级配对 bootstrap。"""
    X, y = features_with_target(cells, target)
    rng = np.random.default_rng(42)
    perm = rng.permutation(np.arange(len(X)))
    tr, te = perm[:int(len(X) * 0.8)], perm[int(len(X) * 0.8):]
    Xtr, ytr, Xte = X.iloc[tr], y.iloc[tr], X.iloc[te]
    clf, reg = fit_models(Xtr, ytr, "xgb", 42)
    p1_0, m_0 = predict_two_stage(clf, reg, Xte)
    base = p1_0 * m_0
    thr = {lv: {"lo": float(Xtr[lv].quantile(0.25)), "hi": float(Xtr[lv].quantile(0.75)),
                "median": float(Xtr[lv].median()), "sd": float(Xtr[lv].std()),
                "p1": float(Xtr[lv].quantile(0.01)), "p99": float(Xtr[lv].quantile(0.99))}
           for lv, _, _ in levers}
    out = []
    cases = [(lab, kind) for kind in ("quartile", "sd")
             for lab in [l for _, _, l in levers] + ["组合情景（全部措施）"]]
    for label, kind in cases:
        if label == "组合情景（全部措施）":
            Xs = Xte.copy()
            for lv, d, _ in levers:
                Xs, _, _ = perturb(Xs, lv, d, kind, thr[lv])
        else:
            lv, d = [(a, b) for a, b, c in levers if c == label][0]
            Xs, _, _ = perturb(Xte, lv, d, kind, thr[lv])
        p1_s, m_s = predict_two_stage(clf, reg, Xs)
        delta = p1_s * m_s - base
        b = np.empty(NBOOT)
        n = len(delta)
        for i in range(NBOOT):
            s = rng.integers(0, n, n)
            b[i] = 100 * delta[s].mean() / base[s].mean()
        out.append({"city": city, "scenario": label, "method": kind,
                    "delta_pct": float(100 * delta.mean() / base.mean()),
                    "ci_lo": float(np.percentile(b, 2.5)), "ci_hi": float(np.percentile(b, 97.5))})
    return pd.DataFrame(out)


def pdp_direction(cells, target, levers):
    """用 seed=42 的 XGBoost 实现检查每个杠杆对 E[Y] 的整体作用方向。"""
    X, y = features_with_target(cells, target)
    rng = np.random.default_rng(42)
    perm = rng.permutation(len(X))
    tr, te = perm[:int(len(X) * 0.8)], perm[int(len(X) * 0.8):]
    clf, reg = fit_models(X.iloc[tr], y.iloc[tr], "xgb", 42)
    Xte = X.iloc[te]
    out = []
    for lever, direction, label in levers:
        grid = np.quantile(X.iloc[tr][lever], np.linspace(0.02, 0.98, 25))
        curve = []
        for g in grid:
            Xs = Xte.copy()
            Xs[lever] = g
            p1, m = predict_two_stage(clf, reg, Xs)
            curve.append(float((p1 * m).mean()))
        curve = np.asarray(curve)
        lo, hi = curve[:5].mean(), curve[-5:].mean()
        d = "上升" if hi > lo * 1.005 else ("下降" if hi < lo * 0.995 else "基本平坦")
        out.append({"scenario": label, "pdp_direction": d,
                    "pdp_low": float(lo), "pdp_high": float(hi)})
    return pd.DataFrame(out)


def make_figure(summary):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    en = {"降低围合度（改善视觉通透性）": "Reduce enclosure",
          "清理占道人行道的设施": "Clear street furniture",
          "减少沿街商业外摆与停车占用": "Limit shop frontage",
          "组合情景（全部措施）": "Combined package"}
    en_city = {"纽约·财产犯罪": "New York: property crime",
               "纽约·暴力犯罪": "New York: violent crime",
               "香港·交通事故": "Hong Kong: traffic accidents"}
    q = summary[summary["method"] == "quartile"]
    cases = [c for c in en_city if c in set(q.city)]
    fig, axes = plt.subplots(1, len(cases), figsize=(5.6 * len(cases), 4.4), squeeze=False)
    for ax, city in zip(axes[0], cases):
        sub = q[q.city == city].sort_values("delta_pct")
        y = np.arange(len(sub))
        err = np.vstack([sub.delta_pct - sub.delta_pct_min, sub.delta_pct_max - sub.delta_pct])
        ax.barh(y, sub.delta_pct, xerr=err, color="#4C72B0", alpha=.85, height=.55,
                error_kw=dict(ecolor="#333", lw=1, capsize=3))
        ax.set_yticks(y)
        ax.set_yticklabels([en.get(s, s) for s in sub.scenario])
        ax.axvline(0, color="#888", lw=.8)
        ax.set_xlabel("Change in predicted events (%)")
        ax.set_title(en_city[city])
        for i, v in enumerate(sub.delta_pct):
            ax.text(v, i, " %.1f%%" % v, va="center",
                    ha="left" if v < 0 else "right", fontsize=8)
    fig.suptitle("Bars = mean of 15 models (5 seeds x 3 algorithms); whiskers = min-max",
                 fontsize=9)
    fig.tight_layout()
    fig.savefig(FIG / "fig_scenario_effects.png", dpi=200)
    plt.close(fig)
    print("  figure:", FIG / "fig_scenario_effects.png", flush=True)


def make_main_figure(agg):
    """正文用两面板图：左纽约暴力犯罪、右香港交通事故（分位数整改口径）。"""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    en_scenario = {
        "清理占道人行道的设施": "Clear space-occupying sidewalk facilities",
        "减少沿街商业外摆与停车占用": "Limit shop frontage and parking",
        "降低围合度（改善视觉通透性）": "Reduce enclosure (enhance visibility)",
        "组合情景（全部措施）": "Combined package",
    }
    cases = [
        ("纽约·暴力犯罪", "New York: violent crime",
         ["清理占道人行道的设施", "减少沿街商业外摆与停车占用",
          "降低围合度（改善视觉通透性）", "组合情景（全部措施）"]),
        ("香港·交通事故", "Hong Kong: traffic accidents",
         ["清理占道人行道的设施", "减少沿街商业外摆与停车占用", "组合情景（全部措施）"]),
    ]
    q = agg[agg["method"] == "quartile"]
    fig, axes = plt.subplots(1, 2, figsize=(11.2, 4.2))
    for ax, (city, title, order) in zip(axes, cases):
        sub = q[q.city == city].set_index("scenario").loc[order].reset_index()
        y = np.arange(len(sub))
        err = np.vstack([sub.delta_pct - sub.delta_pct_min,
                         sub.delta_pct_max - sub.delta_pct])
        ax.barh(y, sub.delta_pct, xerr=err, color="#4C72B0", alpha=.85, height=.55,
                error_kw=dict(ecolor="#444", lw=1, capsize=3))
        ax.set_yticks(y)
        ax.set_yticklabels([en_scenario.get(s, s) for s in sub.scenario], fontsize=9)
        ax.axvline(0, color="#888", lw=.8)
        ax.set_xlabel("Change in predicted incidents (%)", fontsize=9)
        ax.set_title(title, fontsize=10)
        lim = max(abs(sub.delta_pct_min).max(), abs(sub.delta_pct_max).max()) * 1.4 + 1
        ax.set_xlim(-lim, lim)
        for i, v in enumerate(sub.delta_pct):
            ax.text(v + (0.3 if v >= 0 else -0.3), i, "%+.1f%%" % v, va="center",
                    ha="left" if v >= 0 else "right", fontsize=8)
    fig.suptitle("Bars = mean of 15 models (5 seeds x 3 algorithms); whiskers = min-max",
                 fontsize=9, y=0.02)
    fig.tight_layout(rect=(0, 0.05, 1, 1))
    fig.savefig(FIG / "fig_scenario_main.png", dpi=220)
    plt.close(fig)
    print("  figure:", FIG / "fig_scenario_main.png", flush=True)


def main():
    feat = pd.read_csv(E01 / "ny_cells_r300.csv")
    key = ["school_id", "cell_x", "cell_y"]
    feats_only = feat[["school_id", "cell_x", "cell_y"]
                      + [c for c in feat.columns
                         if c not in ("school_id", "cell_x", "cell_y", "event_count",
                                      "dist_to_school")
                         and not c.startswith(("y_", "count_"))]]
    ny_prop = None
    ny_viol = None
    for class_name, col, fname, tag in (
            ("Property crimes", "y_property", "ny_cells_property_r300.csv", "财产犯罪"),
            ("Violent crimes", "y_violent", "ny_cells_violent_r300.csv", "暴力犯罪")):
        print("== 构建纽约%s格网 ==" % tag, flush=True)
        cells = build_ny_cells(class_name, col)
        cells = cells.merge(feats_only, on=key, how="left", validate="one_to_one")
        cells.to_csv(RES / fname, index=False, encoding="utf-8-sig")
        print("  %s：%d 行，合计 %d 起，零值比例 %.3f"
              % (tag, len(cells), int(cells[col].sum()), float((cells[col] == 0).mean())),
              flush=True)
        if col == "y_property":
            ny_prop = cells
        else:
            ny_viol = cells

    hk = pd.read_csv(E01 / "hk_cells_r300.csv")
    print("  香港交通格网 %d 行，合计 %d 起，零值比例 %.3f"
          % (len(hk), int(hk.event_count.sum()), float((hk.event_count == 0).mean())), flush=True)

    print("== 情景模拟 ==", flush=True)
    CASES = [("纽约·财产犯罪", ny_prop, "y_property", NY_LEVERS),
             ("纽约·暴力犯罪", ny_viol, "y_violent", NY_LEVERS),
             ("香港·交通事故", hk, "event_count", HK_LEVERS)]
    all_rows = pd.concat([run_city(tag, c, t, lv) for tag, c, t, lv in CASES],
                         ignore_index=True)
    all_rows.to_csv(RES / "scenario_results_raw.csv", index=False, encoding="utf-8-sig")

    agg = all_rows.groupby(["city", "scenario", "method"]).agg(
        delta_pct=("delta_pct", "mean"), delta_pct_min=("delta_pct", "min"),
        delta_pct_max=("delta_pct", "max"),
        share_cells_reduced=("share_cells_reduced", "mean"),
        delta_pct_extensive=("delta_pct_extensive", "mean"),
        delta_pct_intensive=("delta_pct_intensive", "mean"),
        baseline_mean=("baseline_mean", "mean"),
        clipped_share=("clipped_share", "mean")).reset_index()
    ci = pd.concat([bootstrap_ci(tag, c, t, lv) for tag, c, t, lv in CASES], ignore_index=True)
    ci = ci.rename(columns={"delta_pct": "delta_pct_seed42"})
    agg = agg.merge(ci, on=["city", "scenario", "method"], how="left")
    alg = (all_rows[all_rows["method"] == "quartile"]
           .pivot_table(index=["city", "scenario"], columns="algo", values="delta_pct",
                        aggfunc="mean").round(2).reset_index())
    agg = agg.merge(alg, on=["city", "scenario"], how="left")
    pdp = pd.concat([pdp_direction(c, t, lv).assign(city=tag) for tag, c, t, lv in CASES],
                    ignore_index=True)
    agg = agg.merge(pdp, on=["city", "scenario"], how="left")
    agg["sd_reliable"] = (agg["clipped_share"] < 0.20)
    agg.to_csv(RES / "scenario_summary.csv", index=False, encoding="utf-8-sig")
    print(agg.round(2).to_string(index=False), flush=True)
    make_figure(agg)
    make_main_figure(agg)
    write_note(agg)
    (RES / "scenario_manifest.json").write_text(json.dumps(
        {"seeds": SEEDS, "algos": ALGOS, "n_boot": NBOOT, "radius": RADIUS,
         "cases": [{"case": tag, "target": t,
                    "scenarios": [{"lever": l, "direction": d, "label": x} for l, d, x in lv]}
                   for tag, c, t, lv in CASES]},
        ensure_ascii=False, indent=2), encoding="utf-8")
    print("done", flush=True)


def write_note(agg):
    q = agg[agg["method"] == "quartile"].sort_values(["city", "delta_pct"])
    lines = ["# 情景模拟结果摘要（自动生成）", "",
             "主口径：分位数整改版——把杠杆取值高于第 75 百分位的格网下调到中位数水平。",
             "辅助口径：全局 ±1 标准差（对高度零膨胀变量会越出观测支撑，见 clipped_share 列）。",
             "模型：两阶段 Hurdle，5 个种子 × 3 种算法 = 15 个实现，指标在留出 20% 格网上计算；",
             "因变量：纽约财产犯罪、纽约暴力犯罪、香港交通事故。", "",
             "## 主口径结果", "",
             "| 城市 | 情景 | 预测事件变化（15 个实现均值） | 实现间范围 | XGBoost | LightGBM | 随机森林 | "
             "预测下降格网占比 | 广度边际 | 强度边际 | PDP 方向 |",
             "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |"]
    for _, r in q.iterrows():
        lines.append("| %s | %s | %+.1f%% | %+.1f ~ %+.1f | %+.1f%% | %+.1f%% | %+.1f%% | "
                     "%.0f%% | %+.1f%% | %+.1f%% | %s |"
                     % (r.city, r.scenario, r.delta_pct, r.delta_pct_min, r.delta_pct_max,
                        r.xgb, r.lgbm, r.rf,
                        100 * r.share_cells_reduced, r.delta_pct_extensive,
                        r.delta_pct_intensive, r.pdp_direction))
    lines += ["", "## 辅助口径（±1SD，仅参考）", "",
              "| 城市 | 情景 | 预测事件变化 | 越界被截断的格网占比 |", "| --- | --- | --- | --- |"]
    for _, r in agg[agg["method"] == "sd"].sort_values(["city", "delta_pct"]).iterrows():
        lines.append("| %s | %s | %+.1f%% | %.0f%% |"
                     % (r.city, r.scenario, r.delta_pct, 100 * r.clipped_share))
    ny = agg[(agg["method"] == "quartile") & (agg["scenario"] == "组合情景（全部措施）")
             & (agg["city"].str.startswith("纽约"))]
    lines += ["", "## 纽约两类因变量的对比（组合措施）", "",
              "| 因变量 | 均值 | 实现间范围 | XGBoost | LightGBM | 随机森林 | 算法一致性 |",
              "| --- | --- | --- | --- | --- | --- | --- |"]
    for _, r in ny.iterrows():
        s = [np.sign(r.xgb), np.sign(r.lgbm), np.sign(r.rf)]
        agree = sum(1 for x in s if x == s[0])
        lines.append("| %s | %+.1f%% | %+.1f ~ %+.1f | %+.1f%% | %+.1f%% | %+.1f%% | %d/3 同号%s |"
                     % (r.city, r.delta_pct, r.delta_pct_min, r.delta_pct_max,
                        r.xgb, r.lgbm, r.rf, agree, "（稳健）" if agree == 3 else "（不稳健）"))
    (RES / "scenario_note.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("  note:", RES / "scenario_note.md", flush=True)


if __name__ == "__main__":
    main()
