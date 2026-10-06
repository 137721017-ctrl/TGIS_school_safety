# -*- coding: utf-8 -*-
"""Batch driver: rebuild street-view, incident and raster features at 100–500 m and refit models.
多尺度批量驱动：重算 100—500 m 特征并重新建模。
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

from config.settings import INPUTS, SVI_INDEX_COLUMNS, out_dir  # noqa: E402
from ms_svi_aggregate import load_schools, load_svi  # noqa: E402
from ms_event_counts import load_events  # noqa: E402
from ms_raster_stats import project_schools, zonal_means  # noqa: E402
from cell_level_pipeline import build_cells, model as cell_model  # noqa: E402
from robustness_suite import (run_random, run_spatial_blocks, run_temporal,  # noqa: E402
                              vif_table, split_features)

TARGET_RADII = [100, 200, 400, 500]
MAX_R = 500


def project(lon, lat, epsg):
    from pyproj import Transformer
    t = Transformer.from_crs("EPSG:4326", "EPSG:%d" % epsg, always_xy=True)
    x, y = t.transform(lon, lat)
    return np.asarray(x), np.asarray(y)


def neighbour_pairs(tree, xy, max_r):
    lists = tree.query_ball_point(xy, max_r)
    counts = np.fromiter((len(l) for l in lists), dtype=np.int64, count=len(lists))
    pt = np.repeat(np.arange(len(lists)), counts)
    if counts.sum() == 0:
        return pt, np.array([], dtype=np.int64), np.array([])
    sch = np.concatenate([np.asarray(l, dtype=np.int64) for l in lists])
    d = np.linalg.norm(tree.data[sch] - xy[pt], axis=1)
    return pt, sch, d


def svi_all(city, sx, sy, radii):
    svi = load_svi(city)
    px, py = project(svi["view_lon"].to_numpy(), svi["view_lat"].to_numpy(),
                     INPUTS[city]["utm_epsg"])
    tree = cKDTree(np.column_stack([sx, sy]))
    pt, sch, dist = neighbour_pairs(tree, np.column_stack([px, py]), MAX_R)
    vals = {}
    for name, classes in SVI_INDEX_COLUMNS.items():
        cols = [c for c in classes if c in svi.columns]
        if cols:
            vals[name] = svi[cols].sum(axis=1).to_numpy(dtype=float)[pt]
    out = {}
    for r in radii:
        m = dist <= r
        cnt = np.bincount(sch[m], minlength=len(sx))
        rec = {}
        for name, v in vals.items():
            rec["ratio_%s_r%d" % (name, r)] = np.bincount(sch[m], weights=v[m],
                                                          minlength=len(sx)) / np.maximum(cnt, 1)
        rec["svi_count_r%d" % r] = cnt
        out[r] = pd.DataFrame(rec)
        print("  SVI r=%d 完成：影像-学校对 %d" % (r, int(m.sum())), flush=True)
    return out


def events_all(city, sx, sy, radii):
    events = load_events(city)
    ex, ey = project(events["event_lon"].to_numpy(), events["event_lat"].to_numpy(),
                     INPUTS[city]["utm_epsg"])
    tree = cKDTree(np.column_stack([sx, sy]))
    pt, sch, dist = neighbour_pairs(tree, np.column_stack([ex, ey]), MAX_R)
    years = events["year"].to_numpy() if "year" in events.columns else None
    out = {}
    for r in radii:
        m = dist <= r
        rec = {"event_count_r%d" % r: np.bincount(sch[m], minlength=len(sx))}
        if years is not None:
            ys = years[pt][m]
            for year in np.unique(ys[~pd.isna(ys)]):
                rec["count_%d_r%d" % (int(year), r)] = np.bincount(sch[m][ys == year],
                                                                   minlength=len(sx))
        out[r] = pd.DataFrame(rec)
        print("  事件 r=%d 完成：事件-学校对 %d" % (r, int(m.sum())), flush=True)
    return out


def raster_all(city, schools, radii):
    import rasterio
    cfg = INPUTS[city]
    out = {r: {} for r in radii}
    for name, filename in cfg["rasters"].items():
        path = Path(filename)
        if not path.is_absolute():
            path = Path(cfg["rasters_dir"]) / filename
        if not path.exists():
            print("  [缺失] %s" % path, flush=True)
            continue
        with rasterio.open(path) as src:
            arr, transform, nodata, crs = src.read(1), src.transform, src.nodata, src.crs
        xs, ys = project_schools(city, schools, crs)
        geo = bool(crs and crs.is_geographic)
        for r in radii:
            out[r]["%s_r%d" % (name, r)] = zonal_means(
                arr, transform, xs, ys, r, nodata, geo, schools["school_lat"].to_numpy())
        print("  栅格 %s 完成（%d 个半径）" % (name, len(radii)), flush=True)
        del arr
    return {r: pd.DataFrame(v) for r, v in out.items()}


def main():
    summary = []
    for city in ("ny", "hk"):
        print("================ %s ================" % city.upper(), flush=True)
        schools = load_schools(city)
        sx, sy = project(schools["school_lon"].to_numpy(), schools["school_lat"].to_numpy(),
                         INPUTS[city]["utm_epsg"])
        base = schools[["school_id", "school_lon", "school_lat"]].copy()
        svi = svi_all(city, sx, sy, TARGET_RADII)
        ev = events_all(city, sx, sy, TARGET_RADII)
        ras = raster_all(city, schools, TARGET_RADII)
        for r in TARGET_RADII:
            school = pd.concat([base, svi[r], ev[r], ras[r]], axis=1)
            # 规范的学校级特征表：底表 + 街景 + 事件 + 栅格
            school.to_csv(out_dir(city) / ("%s_school_features_r%d.csv" % (city, r)),
                          index=False, encoding="utf-8-sig")
            # 兼容旧文件名：历史上把合并表写进了 *_svi_*，保留同名副本以免打断既有脚本
            school.to_csv(out_dir(city) / ("%s_svi_r%d.csv" % (city, r)),
                          index=False, encoding="utf-8-sig")
            (out_dir(city) / ("%s_raster_r%d.csv" % (city, r))).unlink(missing_ok=True)
            cells = build_cells(city, r)
            cell_model(city, r)
            X, _ = split_features(cells)
            y = pd.to_numeric(cells["event_count"], errors="coerce").fillna(0)
            rows = []
            rr = run_random(X, y, "xgb")
            if rr:
                rows.append(rr)
            rows.extend(run_spatial_blocks(X, y, cells[["school_lon", "school_lat"]].to_numpy(), 5, "xgb"))
            t = run_temporal(cells, r, 2017 if city == "hk" else 2018, "xgb")
            if t:
                rows.append(t)
            tbl = pd.DataFrame(rows)
            tbl["city"], tbl["radius"] = city, r
            tbl.to_csv(out_dir(city, "results") / ("%s_robustness_r%d.csv" % (city, r)),
                       index=False, encoding="utf-8-sig")
            vif_table(X).to_csv(out_dir(city, "results") / ("%s_vif_r%d.csv" % (city, r)),
                                index=False, encoding="utf-8-sig")
            summary.append({
                "city": city, "radius": r, "cells": len(cells),
                "zero_ratio": float((y == 0).mean()),
                "random_AUC": float(tbl.loc[tbl.scheme == "random_80_20", "AUC"].mean()),
                "spatial_AUC": float(tbl.loc[tbl.scheme.str.startswith("spatial"), "AUC"].mean()),
                "temporal_AUC": float(tbl.loc[tbl.scheme.str.startswith("temporal"), "AUC"].mean()) if t else np.nan})
            print("  完成 %s r=%d cells=%d zero=%.3f" % (city, r, len(cells),
                                                        float((y == 0).mean())), flush=True)
    # 汇总交给 assemble_summary.py，保证基准尺度 300 m 也被纳入（本脚本只覆盖其余半径）
    from assemble_summary import main as assemble_summary
    assemble_summary()


if __name__ == "__main__":
    main()
