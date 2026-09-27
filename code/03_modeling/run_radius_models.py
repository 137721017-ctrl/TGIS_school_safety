# -*- coding: utf-8 -*-
"""Two-stage Hurdle models by buffer radius, with optional spatial block cross-validation.
按缓冲半径运行两阶段 Hurdle 模型，支持空间分块交叉验证。
"""
import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from config.settings import RADII, out_dir  # noqa: E402


def merge_inputs(city: str, radius: int) -> pd.DataFrame:
    folder = out_dir(city)
    parts = [folder / ("%s_svi_r%d.csv" % (city, radius)),
             folder / ("%s_events_r%d.csv" % (city, radius)),
             folder / ("%s_raster_r%d.csv" % (city, radius))]
    frames = []
    for path in parts:
        if path.exists():
            frames.append(pd.read_csv(path))
        else:
            print("  [警告] 缺少输入：%s" % path)
    if not frames:
        raise SystemExit("没有可用输入，请先运行 ms_svi_aggregate / ms_event_counts / ms_raster_stats")
    data = frames[0]
    for frame in frames[1:]:
        data = data.merge(frame, on=["school_id", "school_lon", "school_lat"], how="outer")
    return data


def spatial_blocks(lon, lat, n_blocks=5):
    """按经纬度 KMeans 分块，用于空间分块交叉验证。"""
    from sklearn.cluster import KMeans
    coords = np.column_stack([lon, lat])
    labels = KMeans(n_clusters=n_blocks, n_init=10, random_state=42).fit_predict(coords)
    return labels


def fit_evaluate(X, y, spatial_cv=0):
    from sklearn.model_selection import train_test_split, KFold
    from sklearn.metrics import roc_auc_score, recall_score, r2_score, mean_absolute_error
    import xgboost as xgb

    def split_indices(idx):
        if spatial_cv and spatial_cv > 1:
            labels = spatial_blocks(X.iloc[idx]["school_lon"], X.iloc[idx]["school_lat"], spatial_cv)
            kf = KFold(n_splits=spatial_cv, shuffle=True, random_state=42)
            return [(idx[tr], idx[te]) for tr, te in kf.split(labels)]
        tr, te = train_test_split(idx, test_size=0.2, random_state=42)
        return [(tr, te)]

    idx_all = np.arange(len(X))
    aucs, recalls, r2s, maes = [], [], [], []
    for tr, te in split_indices(idx_all):
        X_tr, X_te = X.iloc[tr], X.iloc[te]
        y_tr, y_te = y.iloc[tr], y.iloc[te]
        # 第一阶段
        clf = xgb.XGBClassifier(n_estimators=200, max_depth=5, learning_rate=0.05,
                                random_state=42, n_jobs=-1, eval_metric="logloss")
        y_bin = (y_tr > 0).astype(int)
        if y_bin.nunique() < 2:
            continue
        clf.fit(X_tr, y_bin)
        prob = clf.predict_proba(X_te)[:, 1]
        pred = clf.predict(X_te)
        if y_te.gt(0).nunique() > 1:
            aucs.append(roc_auc_score(y_te > 0, prob))
        recalls.append(recall_score(y_te > 0, pred, zero_division=0))
        # 第二阶段（仅正样本）
        pos_tr, pos_te = y_tr > 0, y_te > 0
        if pos_tr.sum() > 10 and pos_te.sum() > 5:
            reg = xgb.XGBRegressor(n_estimators=200, max_depth=5, learning_rate=0.05,
                                   random_state=42, n_jobs=-1, objective="count:poisson")
            reg.fit(X_tr[pos_tr], y_tr[pos_tr])
            pred_pos = reg.predict(X_te[pos_te])
            r2s.append(r2_score(y_te[pos_te], pred_pos))
            maes.append(mean_absolute_error(y_te[pos_te], pred_pos))
    return {
        "AUC": float(np.mean(aucs)) if aucs else np.nan,
        "Recall": float(np.mean(recalls)) if recalls else np.nan,
        "R2": float(np.mean(r2s)) if r2s else np.nan,
        "MAE": float(np.mean(maes)) if maes else np.nan,
        "n_samples": int(len(X)),
        "n_positive": int((y > 0).sum()),
        "zero_ratio": float((y == 0).mean()),
    }


def run(city: str, radius: int, spatial_cv: int = 0, target: str = "event_count"):
    print("== %s：建模，半径 %d m" % (city.upper(), radius))
    data = merge_inputs(city, radius)
    y_col = "%s_r%d" % (target, radius)
    if y_col not in data.columns:
        candidates = [c for c in data.columns if c.startswith("event_count")]
        if not candidates:
            raise SystemExit("找不到因变量列：%s" % y_col)
        y_col = candidates[0]
    feature_cols = [c for c in data.columns
                    if c not in ("school_id", "school_lon", "school_lat", y_col)
                    and not c.startswith("count_") and not c.startswith("y_")]
    X = data[feature_cols].apply(pd.to_numeric, errors="coerce")
    X = X.fillna(X.median(numeric_only=True))
    y = pd.to_numeric(data[y_col], errors="coerce").fillna(0)

    metrics = fit_evaluate(X, y, spatial_cv)
    metrics.update({"city": city, "radius": radius, "spatial_cv": spatial_cv, "target": y_col})
    result = pd.DataFrame([metrics])
    target_path = out_dir(city, "results") / ("%s_model_r%d.csv" % (city, radius))
    result.to_csv(target_path, index=False, encoding="utf-8-sig")
    print(result.to_string(index=False))
    print("  已写出：%s" % target_path)
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--city", choices=["ny", "hk"], required=True)
    parser.add_argument("--radius", default="all")
    parser.add_argument("--spatial-cv", type=int, default=0)
    parser.add_argument("--target", default="event_count")
    args = parser.parse_args()
    radii = RADII if args.radius == "all" else [int(args.radius)]
    for r in radii:
        run(args.city, r, args.spatial_cv, args.target)


if __name__ == "__main__":
    main()
