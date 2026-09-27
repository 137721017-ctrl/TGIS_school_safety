# -*- coding: utf-8 -*-
"""Validation and robustness suite: random split, spatial block CV, temporal split, VIF.
随机划分、空间分块、时间窗验证与共线性诊断。
"""
import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve()
sys.path.insert(0, str(HERE.parents[1]))
sys.path.insert(0, str(HERE.parents[0]))
from config.settings import RADII, out_dir  # noqa: E402


def load(city, radius):
    path = out_dir(city) / ("%s_cells_r%d.csv" % (city, radius))
    if not path.exists():
        raise SystemExit("missing %s" % path)
    return pd.read_csv(path)


def split_features(data):
    drop_prefix = ("event_count", "y_")
    feats = [c for c in data.columns
             if not c.startswith(drop_prefix) and c not in
             ("school_id", "cell_x", "cell_y", "dist_to_school", "school_lon", "school_lat")]
    X = data[feats].apply(pd.to_numeric, errors="coerce")
    X = X.fillna(X.median(numeric_only=True))
    return X, feats


def metrics(y_true, prob, pred=None):
    from sklearn.metrics import roc_auc_score, recall_score, average_precision_score, brier_score_loss
    y_bin = (np.asarray(y_true) > 0).astype(int)
    pred = (prob >= 0.5).astype(int) if pred is None else pred
    out = {"n": int(len(y_bin)), "n_pos": int(y_bin.sum()), "zero_ratio": float((y_bin == 0).mean())}
    out["AUC"] = float(roc_auc_score(y_bin, prob)) if y_bin.min() != y_bin.max() else np.nan
    out["Recall"] = float(recall_score(y_bin, pred, zero_division=0))
    out["PR_AUC"] = float(average_precision_score(y_bin, prob)) if y_bin.sum() else np.nan
    out["Brier"] = float(brier_score_loss(y_bin, np.clip(prob, 0, 1)))
    k = max(1, int(len(prob) * 0.05))
    top = np.argsort(-prob)[:k]
    out["top5_hit"] = float(y_bin[top].mean())
    return out


def fit_one(X_tr, y_tr, X_te, y_te, algo="xgb"):
    if algo == "xgb":
        import xgboost as xgb
        clf = xgb.XGBClassifier(n_estimators=300, max_depth=6, learning_rate=0.05,
                                subsample=0.8, colsample_bytree=0.8, min_child_weight=1,
                                random_state=42, n_jobs=-1, eval_metric="logloss")
        reg = xgb.XGBRegressor(n_estimators=300, max_depth=6, learning_rate=0.05,
                               subsample=0.8, colsample_bytree=0.8, random_state=42,
                               n_jobs=-1, objective="count:poisson")
    elif algo == "lgbm":
        import lightgbm as lgb
        clf = lgb.LGBMClassifier(n_estimators=300, num_leaves=31, learning_rate=0.05,
                                 subsample=0.8, colsample_bytree=0.8, random_state=42,
                                 n_jobs=-1, verbose=-1)
        reg = lgb.LGBMRegressor(n_estimators=300, num_leaves=31, learning_rate=0.05,
                                random_state=42, n_jobs=-1, verbose=-1, objective="poisson")
    else:
        from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
        clf = RandomForestClassifier(n_estimators=300, max_depth=12, random_state=42, n_jobs=-1)
        reg = RandomForestRegressor(n_estimators=300, max_depth=12, random_state=42, n_jobs=-1)
    y_bin = (y_tr > 0).astype(int)
    if y_bin.nunique() < 2:
        return None, None, None
    clf.fit(X_tr, y_bin)
    prob = clf.predict_proba(X_te)[:, 1]
    # 第二阶段仅正样本
    pos_tr = y_tr > 0
    r2 = mae = np.nan
    if pos_tr.sum() > 20:
        reg.fit(X_tr[pos_tr], y_tr[pos_tr])
        pos_te = y_te > 0
        if pos_te.sum() > 5:
            from sklearn.metrics import r2_score, mean_absolute_error
            pred_pos = reg.predict(X_te[pos_te])
            r2 = float(r2_score(y_te[pos_te], pred_pos))
            mae = float(mean_absolute_error(y_te[pos_te], pred_pos))
    return prob, (r2, mae), clf


def run_random(X, y, algo="xgb", seed=42):
    from sklearn.model_selection import train_test_split
    idx = np.arange(len(X))
    tr, te = train_test_split(idx, test_size=0.2, random_state=seed)
    prob, (r2, mae), _ = fit_one(X.iloc[tr], y.iloc[tr], X.iloc[te], y.iloc[te], algo)
    if prob is None:
        return {}
    out = metrics(y.iloc[te].to_numpy(), prob)
    out.update({"R2": r2, "MAE": mae, "algo": algo, "scheme": "random_80_20"})
    return out


def run_spatial_blocks(X, y, coords, n_blocks=5, algo="xgb"):
    from sklearn.cluster import KMeans
    labels = KMeans(n_clusters=n_blocks, n_init=10, random_state=42).fit_predict(coords)
    rows = []
    for b in range(n_blocks):
        te = np.where(labels == b)[0]
        tr = np.where(labels != b)[0]
        if len(te) < 30 or len(tr) < 100:
            continue
        prob, (r2, mae), _ = fit_one(X.iloc[tr], y.iloc[tr], X.iloc[te], y.iloc[te], algo)
        if prob is None:
            continue
        m = metrics(y.iloc[te].to_numpy(), prob)
        m.update({"R2": r2, "MAE": mae, "algo": algo, "scheme": "spatial_block_k%d" % n_blocks, "fold": b})
        rows.append(m)
    return rows


def run_temporal(data, radius, split_year, algo="xgb"):
    year_cols = [c for c in data.columns if c.startswith("y_")]
    if not year_cols:
        return None
    years = np.array([int(c.split("_")[1]) for c in year_cols])
    early = [c for c, yr in zip(year_cols, years) if yr <= split_year]
    late = [c for c, yr in zip(year_cols, years) if yr > split_year]
    if not early or not late:
        return None
    X, _ = split_features(data)
    y_tr = data[early].sum(axis=1)
    y_te = data[late].sum(axis=1)
    prob, (r2, mae), _ = fit_one(X, y_tr, X, y_te, algo)
    if prob is None:
        return None
    m = metrics(y_te.to_numpy(), prob)
    m.update({"R2": r2, "MAE": mae, "algo": algo, "scheme": "temporal_<=%d" % split_year})
    return m


def vif_table(X):
    from statsmodels.stats.outliers_influence import variance_inflation_factor
    values = X.to_numpy(dtype=float)
    rows = []
    for i, col in enumerate(X.columns):
        try:
            v = variance_inflation_factor(values, i)
        except Exception:
            v = np.nan
        rows.append({"variable": col, "VIF": float(v)})
    return pd.DataFrame(rows).sort_values("VIF", ascending=False)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--city", choices=["ny", "hk"], required=True)
    parser.add_argument("--radius", type=int, default=300)
    parser.add_argument("--split-year", type=int, default=None)
    args = parser.parse_args()
    split_year = args.split_year or (2017 if args.city == "hk" else 2018)
    data = load(args.city, args.radius)
    X, feats = split_features(data)
    y = pd.to_numeric(data["event_count"], errors="coerce").fillna(0)
    coords = data[["school_lon", "school_lat"]].to_numpy()
    print("cells=%d features=%d zero_ratio=%.3f" % (len(data), len(feats), float((y == 0).mean())), flush=True)

    rows = []
    for algo in ("xgb", "lgbm", "rf"):
        r = run_random(X, y, algo)
        if r:
            rows.append(r)
            print("  random/%s AUC=%.4f PR=%.4f R2=%.3f" % (algo, r["AUC"], r["PR_AUC"], r["R2"]), flush=True)
    for r in run_spatial_blocks(X, y, coords, 5, "xgb"):
        rows.append(r)
        print("  spatial fold%d AUC=%.4f PR=%.4f top5=%.3f" % (r["fold"], r["AUC"], r["PR_AUC"], r["top5_hit"]), flush=True)
    t = run_temporal(data, args.radius, split_year, "xgb")
    if t:
        rows.append(t)
        print("  temporal AUC=%.4f PR=%.4f" % (t["AUC"], t["PR_AUC"]), flush=True)

    result = pd.DataFrame(rows)
    target = out_dir(args.city, "results") / ("%s_robustness_r%d.csv" % (args.city, args.radius))
    result.to_csv(target, index=False, encoding="utf-8-sig")
    vif = vif_table(X)
    vif_target = out_dir(args.city, "results") / ("%s_vif_r%d.csv" % (args.city, args.radius))
    vif.to_csv(vif_target, index=False, encoding="utf-8-sig")
    print("written: %s" % target, flush=True)
    print("written: %s" % vif_target, flush=True)
    print(vif.head(6).to_string(index=False), flush=True)


if __name__ == "__main__":
    main()
