# -*- coding: utf-8 -*-
"""Grid-level incident counts for a NYPD crime class. 按 NYPD 犯罪类别构建 100 m 格网事件计数。

Reads the per-year classified arrest files under SCHOOLSAFETY_ROOT, counts the events of one
Crime_classification group into 100 m grid cells within the school buffer, merges the
environmental features of the matching E01 grid table and writes a cell-level dataset.

用法: python split_categories_by_class.py --class-name "Property crimes" --col y_property
"""
import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from pyproj import Transformer
from scipy.spatial import cKDTree

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "code"))
sys.path.insert(0, str(REPO / "code" / "02_features"))
from config.settings import INPUTS  # noqa: E402
from ms_svi_aggregate import load_schools  # noqa: E402

E01 = REPO / "experiments" / "E01_multiscale_buffer" / "data"
E13 = REPO / "experiments" / "E13_split_categories" / "data"
STEP = 100.0
KEY = ["school_id", "cell_x", "cell_y"]


def grid(radius):
    """Candidate 100 m cell centres within `radius` of the nearest school."""
    tr = Transformer.from_crs("EPSG:4326", "EPSG:32618", always_xy=True)
    schools = load_schools("ny")
    sx, sy = tr.transform(schools["school_lon"].to_numpy(), schools["school_lat"].to_numpy())
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
    cells = pd.DataFrame({"school_id": idx[keep], "cell_x": cx[keep], "cell_y": cy[keep],
                          "dist_to_school": dist[keep]})
    ncol = int(np.ceil((right - left) / STEP)) + 2
    nrow = int(np.ceil((top - bottom) / STEP)) + 2
    cell_flat = (np.floor((cy - bottom) / STEP).astype(np.int64) * ncol
                 + np.floor((cx - left) / STEP).astype(np.int64))[keep]
    return cells, tr, ncol, nrow, left, bottom, cell_flat


def class_events(class_name, tr, ncol, nrow, left, bottom):
    """Bin the events of one crime class into the grid; returns flat cell counts."""
    cfg = INPUTS["ny"]
    counts = np.zeros(nrow * ncol)
    for year in cfg["event_years"]:
        path = Path(cfg["events_dir"]) / cfg["events_pattern"].format(year=year)
        if not path.exists():
            continue
        d = pd.read_csv(path, low_memory=False,
                        usecols=lambda c: c in ("Crime_classification", "Latitude", "Longitude",
                                                "latitude", "longitude"))
        d.columns = [c.lower() for c in d.columns]
        m = (d["crime_classification"].astype(str).str.strip().eq(class_name)
             & d["longitude"].notna() & d["latitude"].notna())
        if not m.any():
            continue
        ex, ey = tr.transform(d.loc[m, "longitude"].to_numpy(), d.loc[m, "latitude"].to_numpy())
        ecol = np.floor((ex - left) / STEP).astype(np.int64)
        erow = np.floor((ey - bottom) / STEP).astype(np.int64)
        ok = (ecol >= 0) & (erow >= 0) & (ecol < ncol) & (erow < nrow)
        counts += np.bincount(erow[ok] * ncol + ecol[ok], minlength=nrow * ncol)
    return counts


def build(class_name, col, radius, name):
    cells, tr, ncol, nrow, left, bottom, cell_flat = grid(radius)
    cells[col] = class_events(class_name, tr, ncol, nrow, left, bottom)[cell_flat]
    feat = pd.read_csv(E01 / ("ny_cells_r%d.csv" % radius))
    feat = feat[KEY + [c for c in feat.columns
                       if c not in KEY + ["event_count", "dist_to_school"]
                       and not c.startswith(("y_", "count_"))]]
    cells = cells.merge(feat, on=KEY, how="left", validate="one_to_one")
    out = E13 / ("ny_cells_%s_r%d.csv" % (name, radius))
    cells.to_csv(out, index=False, encoding="utf-8-sig")
    print("%s r=%d: %d cells, %d events, zero ratio %.3f -> %s"
          % (class_name, radius, len(cells), int(cells[col].sum()),
             float((cells[col] == 0).mean()), out))
    return cells


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--class-name", default="Property crimes")
    p.add_argument("--col", default="y_property")
    p.add_argument("--radii", default="300")
    p.add_argument("--name", default="property")
    a = p.parse_args()
    E13.mkdir(parents=True, exist_ok=True)
    for r in [int(x) for x in a.radii.split(",")]:
        build(a.class_name, a.col, r, a.name)


if __name__ == "__main__":
    main()
