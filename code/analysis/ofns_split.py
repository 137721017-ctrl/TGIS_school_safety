# -*- coding: utf-8 -*-
"""OFNS split-target datasets for New York (E13). 纽约 OFNS_DESC 分组因变量数据集。

The published New York dependent variable merges eleven NYPD ``OFNS_DESC`` offence
descriptions into one "Drugs, Alcohol and Traffic" category.  This module rebuilds that
category as two separate groups and counts them into the same 100 m grid cells used by the
main analysis, so that the split-target results reported in Supplementary S3 can be
regenerated from the raw arrest records.

分组定义见 ``config.settings.OFNS_GROUPS``：
    group_a -> 毒品与酒精类（5 项）
    group_b -> 交通类（6 项，含酒驾／毒驾）

用法（示例）::

    python code/analysis/ofns_split.py --radii 300 --groups a,b --name split
    python code/analysis/ofns_split.py --radii 100,200,300,400,500 --groups a --name drug_alcohol

输出写入 ``experiments/E13_split_categories/data/``：
    --groups a,b -> ny_cells_split_r{radius}.csv      （含 y_drug_alcohol 与 y_traffic）
    --groups a   -> ny_cells_drug_alcohol_r{radius}.csv
"""
import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.spatial import cKDTree

REPO = Path(__file__).resolve().parents[2]
for _p in (REPO / "code", REPO / "code" / "02_features"):
    sys.path.insert(0, str(_p))

from config.settings import INPUTS, OFNS_GROUPS, out_dir  # noqa: E402
from ms_svi_aggregate import load_schools  # noqa: E402

STEP = 100.0
E13 = REPO / "experiments" / "E13_split_categories"
KEY = ["school_id", "cell_x", "cell_y"]
GROUP_COL = {"a": "y_drug_alcohol", "b": "y_traffic"}


# --------------------------------------------------------------------- events
def load_group_events(groups=("a", "b"), with_year=False):
    """Arrest records of the selected OFNS groups, with projected coordinates."""
    from pyproj import Transformer

    cfg = INPUTS["ny"]
    wanted = {ofns: gid for gid, names in OFNS_GROUPS.items() if gid in groups for ofns in names}
    transformer = Transformer.from_crs("EPSG:4326", "EPSG:32618", always_xy=True)
    frames = []
    for year in cfg["event_years"]:
        path = Path(cfg["events_dir"]) / cfg["events_pattern"].format(year=year)
        if not path.exists():
            continue
        d = pd.read_csv(path, low_memory=False,
                        usecols=lambda c: c in ("OFNS_DESC", "Latitude", "Longitude",
                                                "latitude", "longitude"))
        d.columns = [c.lower() for c in d.columns]
        ofns = d["ofns_desc"].astype(str).str.strip().str.upper()
        keep = ofns.isin(wanted)
        if not keep.any():
            continue
        d = d[keep].copy()
        d["group"] = ofns[keep].map(wanted).to_numpy()
        d["year"] = year
        frames.append(d[["longitude", "latitude", "group", "year"]].dropna())
    if not frames:
        raise SystemExit("no OFNS records found under %s" % cfg["events_dir"])
    events = pd.concat(frames, ignore_index=True)
    x, y = transformer.transform(events["longitude"].to_numpy(), events["latitude"].to_numpy())
    events["x"], events["y"] = np.asarray(x), np.asarray(y)
    counts = events["group"].value_counts().to_dict()
    print("  OFNS 事件点 %d：%s" % (len(events), counts), flush=True)
    return events if with_year else events.drop(columns=["year"])


# ----------------------------------------------------------------------- grid
def build_grid(radius):
    """100 m cell centres within ``radius`` of the nearest school (same rule as E01)."""
    schools = load_schools("ny")
    from pyproj import Transformer

    transformer = Transformer.from_crs("EPSG:4326", "EPSG:32618", always_xy=True)
    sx, sy = transformer.transform(schools["school_lon"].to_numpy(),
                                   schools["school_lat"].to_numpy())
    sx, sy = np.asarray(sx), np.asarray(sy)
    left = np.floor((sx.min() - radius) / STEP) * STEP
    bottom = np.floor((sy.min() - radius) / STEP) * STEP
    right = np.ceil((sx.max() + radius) / STEP) * STEP
    top = np.ceil((sy.max() + radius) / STEP) * STEP
    gx = np.arange(left + STEP / 2, right, STEP)
    gy = np.arange(bottom + STEP / 2, top, STEP)
    gxx, gyy = np.meshgrid(gx, gy)
    cx, cy = gxx.ravel(), gyy.ravel()
    dist, idx = cKDTree(np.column_stack([sx, sy])).query(np.column_stack([cx, cy]), k=1)
    keep = dist <= radius
    cells = pd.DataFrame({
        "school_id": idx[keep], "cell_x": cx[keep], "cell_y": cy[keep],
        "dist_to_school": dist[keep],
        "school_lon": schools["school_lon"].to_numpy()[idx[keep]],
        "school_lat": schools["school_lat"].to_numpy()[idx[keep]],
    })
    ncol = int(np.ceil((right - left) / STEP)) + 2
    nrow = int(np.ceil((top - bottom) / STEP)) + 2
    col = np.floor((cx - left) / STEP).astype(np.int64)
    row = np.floor((cy - bottom) / STEP).astype(np.int64)
    flat = (row * ncol + col)[keep]
    return cells, (left, bottom, ncol, nrow, flat)


def count_groups(events, grid, groups=("a", "b"), year=None):
    """Event counts per cell for each OFNS group (optionally restricted to one year)."""
    left, bottom, ncol, nrow, cell_flat = grid
    ecol = np.floor((events["x"].to_numpy() - left) / STEP).astype(np.int64)
    erow = np.floor((events["y"].to_numpy() - bottom) / STEP).astype(np.int64)
    valid = (ecol >= 0) & (erow >= 0) & (ecol < ncol) & (erow < nrow)
    eflat = erow * ncol + ecol
    counts = {}
    for gid in groups:
        mask = valid & (events["group"].to_numpy() == gid)
        if year is not None:
            mask &= events["year"].to_numpy() == year
        counts[GROUP_COL[gid]] = np.bincount(eflat[mask], minlength=nrow * ncol)[cell_flat]
    return counts


def load_radius_features(radius):
    """School-level feature table for one radius (SVI + rasters), keyed by school_id."""
    candidates = ["ny_school_features_r%d.csv" % radius,
                  "ny_svi_r%d.csv" % radius,
                  "ny_raster_r%d.csv" % radius]
    frames = [pd.read_csv(out_dir("ny") / name) for name in candidates
              if (out_dir("ny") / name).exists()]
    if not frames:
        raise SystemExit("missing school-level features for radius %d; run the E01 scripts first"
                         % radius)
    feats = frames[0]
    for extra in frames[1:]:
        new = [c for c in extra.columns if c not in feats.columns or c == "school_id"]
        feats = feats.merge(extra[new], on="school_id", how="outer")
    drop = [c for c in feats.columns if c.startswith(("event_count", "y_", "count_"))]
    return feats.drop(columns=drop, errors="ignore").drop(
        columns=["school_lon", "school_lat"], errors="ignore")


def build_cells(radius, groups=("a", "b"), events=None, with_year=False,
                feature_radius=None):
    """Cell-level dataset for the selected OFNS groups at one radius.

    ``feature_radius`` 控制学校级特征取自哪个缓冲半径，默认与 ``radius`` 相同。
    历史版本的 E13 非基准半径数据集（r100/200/400/500）实际复用了 300 m 的学校级
    特征表，如需复现那批文件可传 ``feature_radius=300``。
    """
    if events is None:
        events = load_group_events(groups, with_year=with_year)
    cells, grid = build_grid(radius)
    for col, values in count_groups(events, grid, groups).items():
        cells[col] = values
    # 数据集始终携带两个目标列；未纳入本次统计的分组填 0（与历史版本的列结构一致）
    for gid, col in GROUP_COL.items():
        if col not in cells.columns:
            cells[col] = 0
    cells = cells.merge(load_radius_features(feature_radius or radius),
                        on="school_id", how="left")
    print("  r=%d：%d 个格网，零值比例 %s" % (
        radius, len(cells), {c: round(float((cells[c] == 0).mean()), 3) for c in cells
                             if c.startswith("y_")}), flush=True)
    return cells


# ------------------------------------------------------------------ evaluation
def feature_matrix(cells, target, with_coords=False):
    """模型特征矩阵；默认与正文格网级模型同口径（不含原始经纬度）。"""
    drop = [c for c in cells.columns if c.startswith(("y_", "count_"))] + [
        "event_count", "school_id", "cell_x", "cell_y", "dist_to_school"]
    if not with_coords:
        drop += ["school_lon", "school_lat"]
    X = cells.drop(columns=[c for c in drop if c in cells.columns]).apply(
        pd.to_numeric, errors="coerce")
    y = pd.to_numeric(cells[target], errors="coerce").fillna(0)
    return X.fillna(X.median(numeric_only=True)), y


def spatial_auc_mean(X, y, coords, n_blocks=5):
    import xgboost as xgb
    from sklearn.cluster import KMeans
    from sklearn.metrics import roc_auc_score

    labels = KMeans(n_clusters=n_blocks, n_init=10, random_state=42).fit_predict(coords)
    params = dict(n_estimators=300, max_depth=6, learning_rate=0.05, subsample=0.8,
                  colsample_bytree=0.8, random_state=42, n_jobs=-1, eval_metric="logloss")
    aucs = []
    for fold in range(n_blocks):
        te = np.where(labels == fold)[0]
        tr = np.where(labels != fold)[0]
        if len(te) < 30 or (y.iloc[tr] > 0).nunique() < 2:
            continue
        clf = xgb.XGBClassifier(**params).fit(X.iloc[tr], (y.iloc[tr] > 0).astype(int))
        prob = clf.predict_proba(X.iloc[te])[:, 1]
        aucs.append(roc_auc_score((y.iloc[te] > 0).astype(int), prob))
    return float(np.mean(aucs)) if aucs else np.nan


def evaluate(cells, target, with_spatial=True, extra=None):
    """Random 80/20 metrics (and optionally the spatially blocked mean) for one target."""
    from s6s5_suite import fit_eval

    X, y = feature_matrix(cells, target)
    m, _, _ = fit_eval(X, y)
    if m is None:
        return None
    m.update({"target": target, "cells": len(X),
              "zero_ratio": float((y == 0).mean()),
              "pos_rate": float((y > 0).mean()),
              "events": int(y.sum()),
              "n_features": int(X.shape[1])})
    if with_spatial:
        m["AUC_spatial_mean"] = spatial_auc_mean(
            X, y, cells[["school_lon", "school_lat"]].to_numpy())
    m.update(extra or {})
    return m


# -------------------------------------------------------------------- writing
def output_path(name, radius):
    return E13 / "data" / ("ny_cells_%s_r%d.csv" % (name, radius))


def write_cells(cells, name, radius):
    E13.joinpath("data").mkdir(parents=True, exist_ok=True)
    path = output_path(name, radius)
    cells.to_csv(path, index=False, encoding="utf-8-sig")
    print("  written: %s (%d rows)" % (path, len(cells)), flush=True)
    return path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--radii", default="300")
    parser.add_argument("--groups", default="a,b", help="a=毒品与酒精类，b=交通类")
    parser.add_argument("--name", default=None, help="输出文件名中的标签，默认按分组推断")
    parser.add_argument("--no-eval", action="store_true", help="只写数据集，不跑评估")
    parser.add_argument("--feature-radius", type=int, default=None,
                        help="学校级特征的缓冲半径；默认与每个格网半径一致")
    args = parser.parse_args()

    groups = tuple(g.strip() for g in args.groups.split(",") if g.strip())
    name = args.name or ("split" if len(groups) > 1 else "drug_alcohol")
    radii = [int(r) for r in args.radii.split(",")]
    rows = []
    for radius in radii:
        cells = build_cells(radius, groups, feature_radius=args.feature_radius)
        write_cells(cells, name, radius)
        if not args.no_eval:
            for gid in groups:
                row = evaluate(cells, GROUP_COL[gid], extra={"radius": radius})
                if row:
                    rows.append(row)
    if rows:
        E13.joinpath("results").mkdir(parents=True, exist_ok=True)
        table = pd.DataFrame(rows)
        table.to_csv(E13 / "results" / ("%s_multiscale.csv" % name),
                     index=False, encoding="utf-8-sig")
        print(table.round(4).to_string(index=False), flush=True)


if __name__ == "__main__":
    main()
