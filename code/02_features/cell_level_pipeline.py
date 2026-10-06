# -*- coding: utf-8 -*-
"""100 m grid cell dataset construction and two-stage Hurdle modelling. 100 m 格网数据集与两阶段建模。"""
import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve()
sys.path.insert(0, str(HERE.parents[1]))            # code/  -> config.settings
sys.path.insert(0, str(HERE.parents[0]))            # code/02_features -> ms_*
sys.path.insert(0, str(HERE.parents[1] / "03_modeling"))
from config.settings import INPUTS, RADII, out_dir  # noqa: E402
from ms_svi_aggregate import load_schools  # noqa: E402
from ms_event_counts import load_events  # noqa: E402
from run_radius_models import fit_evaluate  # noqa: E402

GRID = 100.0


def project(lon, lat, epsg):
    from pyproj import Transformer
    t = Transformer.from_crs("EPSG:4326", "EPSG:%d" % epsg, always_xy=True)
    return np.asarray(t.transform(lon, lat))


def build_cells(city: str, radius: int) -> pd.DataFrame:
    from scipy.spatial import cKDTree
    print("== %s: build cell-level dataset, radius %d m" % (city.upper(), radius), flush=True)
    cfg = INPUTS[city]
    epsg = cfg["utm_epsg"]
    schools = load_schools(city)
    sx, sy = project(schools["school_lon"].to_numpy(), schools["school_lat"].to_numpy(), epsg)
    step = GRID
    left = np.floor((sx.min() - radius) / step) * step
    bottom = np.floor((sy.min() - radius) / step) * step
    right = np.ceil((sx.max() + radius) / step) * step
    top = np.ceil((sy.max() + radius) / step) * step
    gx = np.arange(left + step / 2, right, step)
    gy = np.arange(bottom + step / 2, top, step)
    gxx, gyy = np.meshgrid(gx, gy)
    cx, cy = gxx.ravel(), gyy.ravel()
    print("  candidate cells: %d" % len(cx), flush=True)
    tree = cKDTree(np.column_stack([sx, sy]))
    dist, idx = tree.query(np.column_stack([cx, cy]), k=1)
    keep = dist <= radius
    cx, cy, dist, idx = cx[keep], cy[keep], dist[keep], idx[keep]
    print("  cells within radius: %d (%.1f per school)" % (len(cx), len(cx) / max(len(schools), 1)), flush=True)
    cells = pd.DataFrame({
        "school_id": idx, "cell_x": cx, "cell_y": cy, "dist_to_school": dist,
        "school_lon": schools["school_lon"].to_numpy()[idx],
        "school_lat": schools["school_lat"].to_numpy()[idx],
    })
    events = load_events(city)
    ex, ey = project(events["event_lon"].to_numpy(), events["event_lat"].to_numpy(), epsg)
    ncol = int(np.ceil((right - left) / step)) + 2
    nrow = int(np.ceil((top - bottom) / step)) + 2
    col = np.floor((ex - left) / step).astype(np.int64)
    row = np.floor((ey - bottom) / step).astype(np.int64)
    flat = row * ncol + col
    valid = (flat >= 0) & (row < nrow) & (col < ncol)
    counts = np.bincount(flat[valid], minlength=nrow * ncol)
    cell_col = np.floor((cx - left) / step).astype(np.int64)
    cell_row = np.floor((cy - bottom) / step).astype(np.int64)
    cells["event_count"] = counts[cell_row * ncol + cell_col]
    # 按年计数（用于时间窗切分验证）
    if "year" in events.columns:
        years = events["year"].to_numpy()
        for year in sorted(pd.Series(years).dropna().unique()):
            m = valid & (years == year)
            yc = np.bincount(flat[m], minlength=nrow * ncol)
            cells["y_%d" % int(year)] = yc[cell_row * ncol + cell_col]
            cells["y_%d" % int(year)] = pd.to_numeric(cells["y_%d" % int(year)], errors="coerce").fillna(0)
        print("  year columns: %d" % len([c for c in cells.columns if c.startswith("y_")]), flush=True)
    print("  events in cells: %d, zero-cell ratio %.3f"
          % (int(cells["event_count"].sum()), float((cells["event_count"] == 0).mean())), flush=True)
    # 学校级特征：优先读取合并表 school_features，缺失时退回街景表 + 栅格表
    combined = out_dir(city) / ("%s_school_features_r%d.csv" % (city, radius))
    if combined.exists():
        feature_files = [combined]
    else:
        feature_files = [out_dir(city) / ("%s_svi_r%d.csv" % (city, radius)),
                         out_dir(city) / ("%s_raster_r%d.csv" % (city, radius))]
    for path in feature_files:
        if not path.exists():
            print("  [warn] missing feature file: %s" % path, flush=True)
            continue
        feat = pd.read_csv(path).drop(columns=["school_lon", "school_lat"], errors="ignore")
        cells = cells.merge(feat, on="school_id", how="left")
    target = out_dir(city) / ("%s_cells_r%d.csv" % (city, radius))
    cells.to_csv(target, index=False, encoding="utf-8-sig")
    print("  written: %s (%d rows)" % (target, len(cells)), flush=True)
    return cells


def model(city: str, radius: int, spatial_cv: int = 0):
    path = out_dir(city) / ("%s_cells_r%d.csv" % (city, radius))
    if not path.exists():
        raise SystemExit("missing cell dataset: %s" % path)
    data = pd.read_csv(path)
    y = pd.to_numeric(data["event_count"], errors="coerce").fillna(0)
    drop = ["event_count", "school_id", "cell_x", "cell_y", "dist_to_school"]
    year_cols = [c for c in data.columns if c.startswith("y_")]
    X = data.drop(columns=drop + year_cols, errors="ignore").apply(pd.to_numeric, errors="coerce")
    X = X.fillna(X.median(numeric_only=True))
    metrics = fit_evaluate(X, y, spatial_cv)
    metrics.update({"city": city, "radius": radius, "level": "cell_100m", "spatial_cv": spatial_cv})
    result = pd.DataFrame([metrics])
    target = out_dir(city, "results") / ("%s_cell_model_r%d.csv" % (city, radius))
    result.to_csv(target, index=False, encoding="utf-8-sig")
    print(result.to_string(index=False), flush=True)
    print("  written: %s" % target, flush=True)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--city", choices=["ny", "hk"], required=True)
    parser.add_argument("--radius", default="all")
    parser.add_argument("--skip-build", action="store_true")
    parser.add_argument("--spatial-cv", type=int, default=0)
    args = parser.parse_args()
    radii = RADII if args.radius == "all" else [int(args.radius)]
    for r in radii:
        if not args.skip_build:
            build_cells(args.city, r)
        model(args.city, r, args.spatial_cv)


if __name__ == "__main__":
    main()
