# -*- coding: utf-8 -*-
"""Grid-level year counts and temporal-window validation. 格网级按年计数与时间窗切分验证。

Rebuilds one count column per year for a NYPD crime class, merges the cell-level features on the
composite cell key (school_id, cell_x, cell_y), then trains a two-stage classifier on the early
years and evaluates it on the late years with and without a history-only baseline.

用法: python temporal_window_split.py --radius 300 --split-year 2018
"""
import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
for p in (REPO / "code", REPO / "code" / "02_features", REPO / "code" / "03_modeling"):
    sys.path.insert(0, str(p))
from config.settings import INPUTS  # noqa: E402
from s6s5_suite import paired_bootstrap  # noqa: E402
from split_categories_by_class import grid  # noqa: E402

E13 = REPO / "experiments" / "E13_split_categories"
KEY = ["school_id", "cell_x", "cell_y"]
CLASS = "Drug and traffic crimes"


def year_cells(radius, name):
    """Cell table with one count column per year and features merged on the composite cell key."""
    cells, tr, ncol, nrow, left, bottom, cell_flat = grid(radius)
    cfg = INPUTS["ny"]
    for year in cfg["event_years"]:
        path = Path(cfg["events_dir"]) / cfg["events_pattern"].format(year=year)
        if not path.exists():
            continue
        d = pd.read_csv(path, low_memory=False,
                        usecols=lambda c: c in ("Crime_classification", "Latitude", "Longitude",
                                                "latitude", "longitude"))
        d.columns = [c.lower() for c in d.columns]
        m = (d["crime_classification"].astype(str).str.strip().eq(CLASS)
             & d["longitude"].notna() & d["latitude"].notna())
        if not m.any():
            continue
        ex, ey = tr.transform(d.loc[m, "longitude"].to_numpy(), d.loc[m, "latitude"].to_numpy())
        ecol = np.floor((ex - left) / 100.0).astype(np.int64)
        erow = np.floor((ey - bottom) / 100.0).astype(np.int64)
        ok = (ecol >= 0) & (erow >= 0) & (ecol < ncol) & (erow < nrow)
        counts = np.bincount(erow[ok] * ncol + ecol[ok], minlength=nrow * ncol)
        cells["count_%d" % year] = counts[cell_flat]
    ycols = [c for c in cells.columns if c.startswith("count_")]
    cells["y_%s" % name] = cells[ycols].sum(axis=1)
    base = pd.read_csv(E13 / "data" / ("ny_cells_%s_r%d.csv" % (name, radius)))
    feat = base[[c for c in base.columns if c in KEY or c not in cells.columns]]
    cells = cells.merge(feat, on=KEY, how="left", validate="one_to_one")
    cells.to_csv(E13 / "data" / ("ny_cells_%s_year_r%d.csv" % (name, radius)),
                 index=False, encoding="utf-8-sig")
    return cells


def features(cells, target):
    drop = [c for c in cells.columns if c.startswith(("y_", "count_"))] + [
        "event_count", "school_id", "cell_x", "cell_y", "dist_to_school"]
    X = cells.drop(columns=[c for c in drop if c in cells.columns]).apply(
        pd.to_numeric, errors="coerce")
    y = pd.to_numeric(cells[target], errors="coerce").fillna(0)
    return X.fillna(X.median(numeric_only=True)), y


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--radius", type=int, default=300)
    p.add_argument("--split-year", type=int, default=2018)
    p.add_argument("--name", default="drug_alcohol")
    p.add_argument("--boot", type=int, default=500)
    a = p.parse_args()

    import xgboost as xgb
    from sklearn.metrics import roc_auc_score, average_precision_score

    cells = year_cells(a.radius, a.name)
    X, _ = features(cells, "y_%s" % a.name)
    early = [c for c in cells.columns
             if c.startswith("count_") and int(c.split("_")[1]) <= a.split_year]
    late = [c for c in cells.columns
            if c.startswith("count_") and int(c.split("_")[1]) > a.split_year]
    if not early or not late:
        raise SystemExit("split year leaves an empty window")
    tr_label = (cells[early].sum(axis=1) > 0).astype(int)
    te_label = (cells[late].sum(axis=1) > 0).astype(int)
    params = dict(n_estimators=300, max_depth=6, learning_rate=0.05, subsample=0.8,
                  colsample_bytree=0.8, random_state=42, n_jobs=-1, eval_metric="logloss")
    hist = cells[early].sum(axis=1).to_frame("history")
    p_full = xgb.XGBClassifier(**params).fit(X, tr_label).predict_proba(X)[:, 1]
    p_hist = xgb.XGBClassifier(**params).fit(hist, tr_label).predict_proba(hist)[:, 1]
    diff, pval = paired_bootstrap(te_label, p_full, p_hist, n=a.boot)
    out = pd.DataFrame([{
        "scheme": "temporal_<=%d" % a.split_year, "n_eval": int(len(te_label)),
        "AUC_full": float(roc_auc_score(te_label, p_full)),
        "AUC_history_only": float(roc_auc_score(te_label, p_hist)),
        "PR_AUC_full": float(average_precision_score(te_label, p_full)),
        "delta": diff, "bootstrap_p": pval}])
    (E13 / "results").mkdir(parents=True, exist_ok=True)
    out.to_csv(E13 / "results" / ("%s_temporal_bootstrap.csv" % a.name),
               index=False, encoding="utf-8-sig")
    print(out.round(4).to_string(index=False))


if __name__ == "__main__":
    main()
