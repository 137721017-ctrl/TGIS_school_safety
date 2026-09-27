# -*- coding: utf-8 -*-
"""Ablation and significance tests, count-model comparison, calibration/PR curves, exposure models.
消融与显著性检验、计数模型比较、校准与 PR 曲线、暴露量模型。
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

CODE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(CODE))
sys.path.insert(0, str(CODE / "02_features"))
from config.settings import out_dir  # noqa: E402

RADII = [100, 200, 300, 400, 500]
SPLIT = {"ny": 2018, "hk": 2017}
SEED = 42


def load_cells(city, radius):
    p = out_dir(city) / ("%s_cells_r%d.csv" % (city, radius))
    if not p.exists():
        return None
    return pd.read_csv(p)


def build_targets(cells, city):
    """时间切分：早期年份作历史特征，后期年份作预测目标。"""
    split = SPLIT[city]
    ycols = [c for c in cells.columns if c.startswith("y_")]
    years = {c: int(c.split("_")[1]) for c in ycols}
    early = [c for c, v in years.items() if v <= split]
    late = [c for c, v in years.items() if v > split]
    hist = cells[early].sum(axis=1) if early else None
    y = cells[late].sum(axis=1) if late else pd.to_numeric(cells["event_count"])
    return hist, y, early, late


def feature_groups(cells, hist):
    cols = list(cells.columns)
    sv = [c for c in cols if c.startswith("ratio_")]
    pop = [c for c in cols if c.startswith(("person", "landscan"))]
    dens = [c for c in cols if c.startswith(("busStation", "crossing", "shop", "street_lamp",
                                             "traffic_signals", "speed_camera", "road", "access"))]
    coord = [c for c in cols if c in ("school_lon", "school_lat", "cell_x", "cell_y")]
    groups = {
        "G1_history_only": (["__history__"] if hist is not None else []),
        "G2_coords_only": coord,
        "G3_population_only": pop,
        "G4_density_access_only": dens,
        "G5_streetview_only": sv,
        "G6_history_plus_macro": (["__history__"] + pop + dens) if hist is not None else (pop + dens),
        "G7_full": (["__history__"] + coord + pop + dens + sv) if hist is not None else (coord + pop + dens + sv),
    }
    return groups


def matrix(cells, cols, hist):
    data = {}
    for c in cols:
        if c == "__history__":
            data["history"] = hist
        else:
            data[c] = pd.to_numeric(cells[c], errors="coerce")
    X = pd.DataFrame(data)
    return X.fillna(X.median(numeric_only=True))


def fit_eval(X, y, seed=SEED):
    import xgboost as xgb
    from sklearn.model_selection import train_test_split
    from sklearn.metrics import roc_auc_score, average_precision_score, recall_score
    idx = np.arange(len(X))
    tr, te = train_test_split(idx, test_size=0.2, random_state=seed)
    yb = (y > 0).astype(int)
    if yb.iloc[tr].nunique() < 2:
        return None, None, None
    clf = xgb.XGBClassifier(n_estimators=300, max_depth=6, learning_rate=0.05,
                            subsample=0.8, colsample_bytree=0.8, random_state=seed,
                            n_jobs=-1, eval_metric="logloss")
    clf.fit(X.iloc[tr], yb.iloc[tr])
    prob = clf.predict_proba(X.iloc[te])[:, 1]
    yb_te = yb.iloc[te].to_numpy()
    m = {"AUC": float(roc_auc_score(yb_te, prob)),
         "PR_AUC": float(average_precision_score(yb_te, prob)),
         "Recall": float(recall_score(yb_te, (prob >= 0.5).astype(int), zero_division=0)),
         "n_test": int(len(te))}
    # 第二阶段：正样本回归
    pos_tr, pos_te = y.iloc[tr] > 0, y.iloc[te] > 0
    if pos_tr.sum() > 20 and pos_te.sum() > 5:
        from sklearn.metrics import r2_score, mean_absolute_error
        reg = xgb.XGBRegressor(n_estimators=300, max_depth=6, learning_rate=0.05,
                               subsample=0.8, colsample_bytree=0.8, random_state=seed,
                               n_jobs=-1, objective="count:poisson")
        reg.fit(X.iloc[tr][pos_tr], y.iloc[tr][pos_tr])
        pred = reg.predict(X.iloc[te][pos_te])
        m["R2_pos"] = float(r2_score(y.iloc[te][pos_te], pred))
        m["MAE_pos"] = float(mean_absolute_error(y.iloc[te][pos_te], pred))
    return m, prob, (te, clf)


def paired_bootstrap(y, prob_a, prob_b, n=500, seed=SEED):
    from sklearn.metrics import roc_auc_score
    rng = np.random.default_rng(seed)
    yb = (y > 0).astype(int).to_numpy()
    diffs = []
    for _ in range(n):
        idx = rng.integers(0, len(yb), len(yb))
        if yb[idx].min() == yb[idx].max():
            continue
        diffs.append(roc_auc_score(yb[idx], prob_a[idx]) - roc_auc_score(yb[idx], prob_b[idx]))
    diffs = np.asarray(diffs)
    return float(diffs.mean()), float((diffs <= 0).mean())


def count_models(X, y, city, radius, max_rows=8000, n_feat=12):
    """Hurdle vs Poisson/NB/ZIP/ZINB/单阶段树：全样本 MAE、RMSE、泊松偏差。"""
    import statsmodels.api as sm
    from sklearn.model_selection import train_test_split
    import xgboost as xgb
    rng = np.random.default_rng(SEED)
    sub = X if len(X) <= max_rows else X.iloc[rng.choice(len(X), max_rows, replace=False)]
    ys = y.loc[sub.index]
    # 选方差较大的前 n_feat 个特征，标准化后用于 GLM
    std = sub.std().sort_values(ascending=False)
    use = list(std.index[:n_feat])
    Z = (sub[use] - sub[use].mean()) / (sub[use].std() + 1e-9)
    Z = sm.add_constant(Z)
    rows = []

    def deviance(y_true, mu):
        mu = np.clip(mu, 1e-6, None)
        yv = np.asarray(y_true, dtype=float)
        term = np.where(yv > 0, yv * np.log(yv / mu), 0.0)
        return float(np.mean(2 * (term - (yv - mu))))

    tr_idx, te_idx = train_test_split(np.arange(len(Z)), test_size=0.2, random_state=SEED)
    Xtr, Xte = Z.iloc[tr_idx], Z.iloc[te_idx]
    ytr, yte = ys.iloc[tr_idx], ys.iloc[te_idx]

    def evaluate(name, mu_all, extra=None):
        mu = np.asarray(mu_all, dtype=float)
        rows.append({"model": name,
                     "MAE": float(np.mean(np.abs(yte.to_numpy() - mu))),
                     "RMSE": float(np.sqrt(np.mean((yte.to_numpy() - mu) ** 2))),
                     "Poisson_deviance": deviance(yte.to_numpy(), mu),
                     **(extra or {})})

    for name, family in (("Poisson_GLM", sm.families.Poisson()),
                         ("NegBin_GLM", sm.families.NegativeBinomial())):
        try:
            res = sm.GLM(ytr, Xtr, family=family).fit(maxiter=200)
            evaluate(name, res.predict(Xte))
        except Exception as exc:  # noqa: BLE001
            print("    %s 失败: %s" % (name, str(exc)[:60]), flush=True)
    for name, cls in (("ZIP", sm.ZeroInflatedPoisson), ("ZINB", sm.ZeroInflatedNegativeBinomialP)):
        try:
            res = cls(ytr, Xtr, exog_infl=Xtr, inflation="logit").fit(maxiter=200)
            evaluate(name, res.predict(Xte, exog_infl=Xte))
        except Exception as exc:  # noqa: BLE001
            print("    %s 失败: %s" % (name, str(exc)[:60]), flush=True)
    # 单阶段树
    try:
        reg = xgb.XGBRegressor(n_estimators=300, max_depth=6, learning_rate=0.05,
                               subsample=0.8, colsample_bytree=0.8, random_state=SEED,
                               n_jobs=-1, objective="count:poisson")
        reg.fit(Xtr, ytr)
        evaluate("SingleStage_XGB", reg.predict(Xte))
    except Exception as exc:  # noqa: BLE001
        print("    单阶段树失败: %s" % str(exc)[:60], flush=True)
    # Hurdle：分类概率 × 条件期望
    try:
        clf = xgb.XGBClassifier(n_estimators=300, max_depth=6, learning_rate=0.05,
                                subsample=0.8, colsample_bytree=0.8, random_state=SEED,
                                n_jobs=-1, eval_metric="logloss")
        clf.fit(Xtr, (ytr > 0).astype(int))
        p = clf.predict_proba(Xte)[:, 1]
        pos = ytr > 0
        reg = xgb.XGBRegressor(n_estimators=300, max_depth=6, learning_rate=0.05,
                               subsample=0.8, colsample_bytree=0.8, random_state=SEED,
                               n_jobs=-1, objective="count:poisson")
        reg.fit(Xtr[pos], ytr[pos])
        cond = reg.predict(Xte)
        evaluate("Hurdle_XGB", p * cond)
    except Exception as exc:  # noqa: BLE001
        print("    Hurdle 失败: %s" % str(exc)[:60], flush=True)
    return pd.DataFrame(rows).assign(city=city, radius=radius,
                                     n_train=len(tr_idx), n_test=len(te_idx))


def calibration_pr(city, radius, y, prob, tag):
    """保存校准曲线与 PR 曲线的数据点与图件。"""
    from sklearn.calibration import calibration_curve
    from sklearn.metrics import precision_recall_curve
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    yb = (y > 0).astype(int).to_numpy()
    fig_dir = out_dir(city, "results") / "figures"
    fig_dir.mkdir(parents=True, exist_ok=True)
    frac_pos, mean_pred = calibration_curve(yb, prob, n_bins=10, strategy="quantile")
    pd.DataFrame({"mean_predicted": mean_pred, "fraction_positive": frac_pos}).to_csv(
        fig_dir / ("%s_calibration_r%d_%s.csv" % (city, radius, tag)), index=False, encoding="utf-8-sig")
    prec, rec, _ = precision_recall_curve(yb, prob)
    pd.DataFrame({"recall": rec, "precision": prec}).to_csv(
        fig_dir / ("%s_pr_r%d_%s.csv" % (city, radius, tag)), index=False, encoding="utf-8-sig")
    fig, axes = plt.subplots(1, 2, figsize=(10, 4))
    axes[0].plot(mean_pred, frac_pos, marker="o")
    axes[0].plot([0, 1], [0, 1], "--", color="gray")
    axes[0].set_xlabel("Predicted probability"); axes[0].set_ylabel("Observed frequency")
    axes[0].set_title("Calibration (%s r=%d)" % (city, radius))
    axes[1].plot(rec, prec); axes[1].set_xlabel("Recall"); axes[1].set_ylabel("Precision")
    axes[1].set_title("Precision-Recall (%s r=%d)" % (city, radius))
    fig.tight_layout()
    fig.savefig(fig_dir / ("%s_curves_r%d_%s.png" % (city, radius, tag)), dpi=200)
    plt.close(fig)
    return str(fig_dir / ("%s_curves_r%d_%s.png" % (city, radius, tag)))


def exposure_second_stage(cells, city, radius, hist):
    """暴露量：计数目标 vs 事件率目标的第二阶段 R²/MAE。"""
    import xgboost as xgb
    from sklearn.model_selection import train_test_split
    from sklearn.metrics import r2_score, mean_absolute_error
    X = matrix(cells, ["__history__"] + [c for c in cells.columns if c.startswith("ratio_")], hist)
    y = pd.to_numeric(cells["event_count"], errors="coerce").fillna(0)
    road = pd.to_numeric(cells["road_r%d" % radius], errors="coerce").replace(0, np.nan)
    rate = (y / road).fillna(0)
    idx = np.arange(len(X))
    tr, te = train_test_split(idx, test_size=0.2, random_state=SEED)
    out = {}
    for name, target in (("count", y), ("rate", rate)):
        pos_tr = target.iloc[tr] > 0
        pos_te = target.iloc[te] > 0
        if pos_tr.sum() < 20 or pos_te.sum() < 5:
            out[name] = (np.nan, np.nan)
            continue
        reg = xgb.XGBRegressor(n_estimators=300, max_depth=6, learning_rate=0.05,
                               subsample=0.8, colsample_bytree=0.8, random_state=SEED,
                               n_jobs=-1, objective="count:poisson")
        reg.fit(X.iloc[tr][pos_tr], target.iloc[tr][pos_tr])
        pred = reg.predict(X.iloc[te][pos_te])
        out[name] = (float(r2_score(target.iloc[te][pos_te], pred)),
                     float(mean_absolute_error(target.iloc[te][pos_te], pred)))
    return out


def main():
    ab_rows, model_rows, exp_rows, curve_rows = [], [], [], []
    for city in ("ny", "hk"):
        for radius in RADII:
            cells = load_cells(city, radius)
            if cells is None:
                continue
            hist, y, early, late = build_targets(cells, city)
            print("== %s r=%d: 历史年份 %d 个，目标年份 %d 个" % (city, radius, len(early), len(late)), flush=True)
            groups = feature_groups(cells, hist)
            probs = {}
            for gname, cols in groups.items():
                cols = [c for c in cols if c != "__history__" or hist is not None]
                if not cols:
                    continue
                X = matrix(cells, cols, hist)
                m, prob, extra = fit_eval(X, y)
                if not m:
                    continue
                m.update({"city": city, "radius": radius, "group": gname,
                          "n_features": len(cols)})
                ab_rows.append(m)
                if gname == "G7_full":
                    probs["full"] = (prob, extra)
                print("    %-24s AUC=%.4f PR=%.4f" % (gname, m["AUC"], m["PR_AUC"]), flush=True)
            if "full" in probs:
                fig = calibration_pr(city, radius, y.iloc[probs["full"][1][0]], probs["full"][0], "full")
                curve_rows.append({"city": city, "radius": radius, "figure": fig})
            # 显著性：全模型 vs 仅历史
            if "G1_history_only" in groups and "G7_full" in groups:
                Xh = matrix(cells, ["__history__"], hist)
                mh, ph, eh = fit_eval(Xh, y)
                if ph is not None and "full" in probs:
                    te_same = probs["full"][1][0]
                    if np.array_equal(te_same, eh[0]):
                        diff, p = paired_bootstrap(y.iloc[te_same], probs["full"][0], ph)
                        ab_rows.append({"city": city, "radius": radius, "group": "G7_vs_G1_delta",
                                        "AUC": diff, "bootstrap_p_le0": p, "n_test": len(te_same)})
                        print("    全模型-仅历史 AUC 差 %.4f（bootstrap p=%.3f）" % (diff, p), flush=True)
            # 计数模型比较与暴露量
            Xfull = matrix(cells, groups["G7_full"], hist)
            model_rows.append(count_models(Xfull, y, city, radius))
            exp = exposure_second_stage(cells, city, radius, hist)
            exp_rows.append({"city": city, "radius": radius,
                             "count_R2": exp["count"][0], "count_MAE": exp["count"][1],
                             "rate_R2": exp["rate"][0], "rate_MAE": exp["rate"][1]})
            print("    暴露量：计数 R2=%.3f MAE=%.3f；事件率 R2=%.3f MAE=%.4f"
                  % (exp["count"][0], exp["count"][1], exp["rate"][0], exp["rate"][1]), flush=True)

    res = out_dir("ny", "results")
    pd.DataFrame(ab_rows).to_csv(res / "ablation_scale_table.csv", index=False, encoding="utf-8-sig")
    pd.concat(model_rows, ignore_index=True).to_csv(res / "count_model_comparison.csv",
                                                    index=False, encoding="utf-8-sig")
    pd.DataFrame(exp_rows).to_csv(res / "exposure_second_stage.csv", index=False, encoding="utf-8-sig")
    pd.DataFrame(curve_rows).to_csv(res / "curve_files.csv", index=False, encoding="utf-8-sig")
    print("written: ablation_scale_table.csv / count_model_comparison.csv / exposure_second_stage.csv",
          flush=True)


if __name__ == "__main__":
    main()
