# -*- coding: utf-8 -*-
"""Cross-algorithm tables and spatial diagnostics (Moran's I, top-k, exposure, SHAP stability).
三算法汇总表与空间诊断（Moran's I、top-k、暴露量、SHAP 稳定性）。
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.spatial import cKDTree

CODE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(CODE))
sys.path.insert(0, str(CODE / "02_features"))
sys.path.insert(0, str(CODE / "03_modeling"))
from config.settings import out_dir  # noqa: E402
from robustness_suite import split_features  # noqa: E402

RADII = [100, 200, 300, 400, 500]
ALGOS = ["xgb", "lgbm", "rf"]


def make_model(algo):
    if algo == "xgb":
        import xgboost as xgb
        return xgb.XGBClassifier(n_estimators=300, max_depth=6, learning_rate=0.05,
                                 subsample=0.8, colsample_bytree=0.8, random_state=42,
                                 n_jobs=-1, eval_metric="logloss")
    if algo == "lgbm":
        import lightgbm as lgb
        return lgb.LGBMClassifier(n_estimators=300, num_leaves=31, learning_rate=0.05,
                                  subsample=0.8, colsample_bytree=0.8, random_state=42,
                                  n_jobs=-1, verbose=-1)
    from sklearn.ensemble import RandomForestClassifier
    return RandomForestClassifier(n_estimators=300, max_depth=12, random_state=42, n_jobs=-1)


def topk_hit(y_bin, prob, frac):
    k = max(1, int(len(prob) * frac))
    idx = np.argsort(-prob)[:k]
    return float(np.asarray(y_bin)[idx].mean())


def eval_split(X_tr, y_tr, X_te, y_te, algo):
    from sklearn.metrics import (roc_auc_score, average_precision_score, recall_score,
                                 brier_score_loss)
    clf = make_model(algo)
    yb_tr = (y_tr > 0).astype(int)
    if yb_tr.nunique() < 2:
        return None, None
    clf.fit(X_tr, yb_tr)
    prob = clf.predict_proba(X_te)[:, 1]
    yb_te = (y_te > 0).astype(int).to_numpy()
    out = {
        "AUC": float(roc_auc_score(yb_te, prob)) if yb_te.min() != yb_te.max() else np.nan,
        "PR_AUC": float(average_precision_score(yb_te, prob)) if yb_te.sum() else np.nan,
        "Recall": float(recall_score(yb_te, (prob >= 0.5).astype(int), zero_division=0)),
        "Brier": float(brier_score_loss(yb_te, np.clip(prob, 0, 1))),
        "top1_hit": topk_hit(yb_te, prob, 0.01),
        "top5_hit": topk_hit(yb_te, prob, 0.05),
        "top10_hit": topk_hit(yb_te, prob, 0.10),
        "n_test": int(len(yb_te)),
    }
    return out, clf


def morans_i(coords, values, k=8, n_perm=99, max_n=4000, seed=42):
    from scipy.sparse import csr_matrix
    rng = np.random.default_rng(seed)
    n = len(values)
    if n > max_n:
        idx = rng.choice(n, size=max_n, replace=False)
        coords, values = coords[idx], values[idx]
        n = max_n
    z = values - values.mean()
    if not np.isfinite(z).all() or z.std() == 0:
        return np.nan, np.nan
    tree = cKDTree(coords)
    _, ind = tree.query(coords, k=min(k + 1, n))
    rows = np.repeat(np.arange(n), ind.shape[1] - 1)
    cols = ind[:, 1:].ravel()
    w = csr_matrix((np.ones(len(rows)), (rows, cols)), shape=(n, n))
    W = w.sum()

    def stat(v):
        zz = v - v.mean()
        return (n / W) * float(zz @ (w @ zz)) / float(zz @ zz)

    obs = stat(values)
    perm = np.array([stat(rng.permutation(values)) for _ in range(n_perm)])
    p = float((np.abs(perm) >= abs(obs)).mean())
    return float(obs), p


def shap_stability(cells, radius, n_folds=5, seed=42, max_n=8000):
    """用 XGBoost 的 pred_contribs 直接得到 SHAP，比较空间折之间的特征重要度排序。"""
    import xgboost as xgb
    from scipy.stats import spearmanr
    X, feats = split_features(cells)
    y = (pd.to_numeric(cells["event_count"], errors="coerce").fillna(0) > 0).astype(int)
    rng = np.random.default_rng(seed)
    if len(X) > max_n:
        idx = rng.choice(len(X), max_n, replace=False)
        X, y = X.iloc[idx], y.iloc[idx]
    folds = np.arange(len(X)) % n_folds
    imps = []
    for f in range(n_folds):
        tr = folds != f
        if y[tr].nunique() < 2:
            continue
        clf = xgb.XGBClassifier(n_estimators=200, max_depth=6, learning_rate=0.05,
                                subsample=0.8, colsample_bytree=0.8, random_state=42,
                                n_jobs=-1, eval_metric="logloss")
        clf.fit(X[tr], y[tr])
        booster = clf.get_booster()
        contribs = booster.predict(xgb.DMatrix(X[~tr]), pred_contribs=True)
        imps.append(np.abs(contribs[:, :-1]).mean(axis=0))
    if len(imps) < 2:
        return np.nan, len(imps)
    corrs = []
    for i in range(len(imps)):
        for j in range(i + 1, len(imps)):
            corrs.append(spearmanr(imps[i], imps[j]).statistic)
    return float(np.nanmean(corrs)), len(imps)


def exposure_analysis(cells, radius, algo="xgb"):
    """以道路长度（路网栅格均值）为暴露分母，比较计数模型与事件率模型的判别能力。"""
    road_col = "road_r%d" % radius
    if road_col not in cells.columns:
        return np.nan, np.nan
    X, _ = split_features(cells)
    y = pd.to_numeric(cells["event_count"], errors="coerce").fillna(0)
    road = pd.to_numeric(cells[road_col], errors="coerce").replace(0, np.nan)
    rate = (y / road).fillna(0)
    from sklearn.model_selection import train_test_split
    idx = np.arange(len(X))
    tr, te = train_test_split(idx, test_size=0.2, random_state=42)
    _, _ = eval_split(X.iloc[tr], y.iloc[tr], X.iloc[te], y.iloc[te], algo)
    m_count, _ = eval_split(X.iloc[tr], y.iloc[tr], X.iloc[te], y.iloc[te], algo)
    m_rate, _ = eval_split(X.iloc[tr], rate.iloc[tr], X.iloc[te], rate.iloc[te], algo)
    return (m_count["AUC"] if m_count else np.nan), (m_rate["AUC"] if m_rate else np.nan)


def main():
    algo_rows, diag_rows = [], []
    for city in ("ny", "hk"):
        for radius in RADII:
            path = out_dir(city) / ("%s_cells_r%d.csv" % (city, radius))
            if not path.exists():
                continue
            cells = pd.read_csv(path)
            X, _ = split_features(cells)
            y = pd.to_numeric(cells["event_count"], errors="coerce").fillna(0)
            from sklearn.model_selection import train_test_split
            from sklearn.cluster import KMeans
            idx = np.arange(len(X))
            tr, te = train_test_split(idx, test_size=0.2, random_state=42)
            coords = cells[["cell_x", "cell_y"]].to_numpy()
            labels = KMeans(n_clusters=5, n_init=10, random_state=42).fit_predict(
                cells[["school_lon", "school_lat"]].to_numpy())
            for algo in ALGOS:
                m, clf = eval_split(X.iloc[tr], y.iloc[tr], X.iloc[te], y.iloc[te], algo)
                if not m:
                    continue
                m.update({"city": city, "radius": radius, "algo": algo, "scheme": "random_80_20"})
                algo_rows.append(m)
                aucs = []
                for f in range(5):
                    te_f = np.where(labels == f)[0]
                    tr_f = np.where(labels != f)[0]
                    if len(te_f) < 30:
                        continue
                    mf, _ = eval_split(X.iloc[tr_f], y.iloc[tr_f], X.iloc[te_f], y.iloc[te_f], algo)
                    if mf:
                        aucs.append(mf["AUC"])
                algo_rows.append({"city": city, "radius": radius, "algo": algo,
                                  "scheme": "spatial_block_k5",
                                  "AUC": float(np.mean(aucs)) if aucs else np.nan,
                                  "n_test": int(len(te))})
            print("  %s r=%d 三算法完成" % (city, radius), flush=True)

            m_count, _ = eval_split(X.iloc[tr], y.iloc[tr], X.iloc[te], y.iloc[te], "xgb")
            resid_model = None
            try:
                import xgboost as xgb
                reg = xgb.XGBRegressor(n_estimators=300, max_depth=6, learning_rate=0.05,
                                       subsample=0.8, colsample_bytree=0.8, random_state=42,
                                       n_jobs=-1, objective="count:poisson")
                pos = y.iloc[tr] > 0
                reg.fit(X.iloc[tr][pos], y.iloc[tr][pos])
                pred_all = reg.predict(X.iloc[te])
                resid = y.iloc[te].to_numpy() - pred_all
                mi, mp = morans_i(coords[te], resid)
            except Exception as exc:  # noqa: BLE001
                mi, mp = np.nan, np.nan
                print("    Moran 计算失败：%s" % str(exc)[:60], flush=True)
            stab, nf = shap_stability(cells, radius)
            auc_count, auc_rate = exposure_analysis(cells, radius)
            diag_rows.append({
                "city": city, "radius": radius,
                "zero_ratio": float((y == 0).mean()),
                "morans_I_resid": mi, "morans_p": mp,
                "top1_hit": m_count["top1_hit"] if m_count else np.nan,
                "top5_hit": m_count["top5_hit"] if m_count else np.nan,
                "top10_hit": m_count["top10_hit"] if m_count else np.nan,
                "AUC_count_model": auc_count, "AUC_rate_model": auc_rate,
                "shap_spearman_mean": stab, "shap_folds": nf,
            })
            print("    Moran I=%.3f (p=%.3f) top1=%.3f top10=%.3f AUC计数=%.3f 率=%.3f SHAP秩相关=%.3f"
                  % (mi, mp, diag_rows[-1]["top1_hit"], diag_rows[-1]["top10_hit"],
                     auc_count, auc_rate, stab), flush=True)

    algo_tbl = pd.DataFrame(algo_rows)
    algo_tbl.to_csv(out_dir("ny", "results") / "algo_scale_table.csv", index=False, encoding="utf-8-sig")
    diag_tbl = pd.DataFrame(diag_rows)
    diag_tbl.to_csv(out_dir("ny", "results") / "diagnostics_scale_table.csv", index=False, encoding="utf-8-sig")
    print(algo_tbl.round(4).to_string(index=False), flush=True)
    print(diag_tbl.round(4).to_string(index=False), flush=True)


if __name__ == "__main__":
    main()
