# -*- coding: utf-8 -*-
"""Zonal means of continuous rasters per school and radius. 各学校与半径的栅格缓冲均值。"""
import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from config.settings import INPUTS, RADII, out_dir  # noqa: E402
from ms_svi_aggregate import load_schools  # noqa: E402


def project_schools(city, schools, crs):
    from pyproj import Transformer
    transformer = Transformer.from_crs("EPSG:4326", crs, always_xy=True)
    x, y = transformer.transform(schools["school_lon"].to_numpy(), schools["school_lat"].to_numpy())
    return np.asarray(x), np.asarray(y)


def zonal_means(array, transform, xs, ys, radius, nodata, geographic, school_lat):
    """对每个 (x, y) 计算半径内像元均值。

    栅格为经纬度时把半径换算为度（按纬度做经度收缩），投影坐标系则直接用米。
    """
    inv = ~transform
    out = np.full(len(xs), np.nan)
    height, width = array.shape
    px_size = abs(transform.a)
    py_size = abs(transform.e)
    for i, (x, y) in enumerate(zip(xs, ys)):
        if geographic:
            dlat = radius / 111320.0
            dlon = radius / (111320.0 * max(np.cos(np.radians(school_lat[i])), 1e-6))
        else:
            dlat = dlon = radius
        px, py = inv * (x, y)
        col, row = int(px), int(py)
        half_c = int(np.ceil(dlon / px_size)) + 1
        half_r = int(np.ceil(dlat / py_size)) + 1
        r0, r1 = max(0, row - half_r), min(height, row + half_r + 1)
        c0, c1 = max(0, col - half_c), min(width, col + half_c + 1)
        if r1 <= r0 or c1 <= c0:
            continue
        block = array[r0:r1, c0:c1].astype("float32")
        rows, cols = np.mgrid[r0:r1, c0:c1]
        bx = transform.c + (cols + 0.5) * transform.a
        by = transform.f + (rows + 0.5) * transform.e
        mask = ((bx - x) / dlon) ** 2 + ((by - y) / dlat) ** 2 <= 1.0
        if nodata is not None:
            mask &= block != nodata
        mask &= np.isfinite(block)
        if mask.any():
            out[i] = float(block[mask].mean())
    return out


def process(city: str, radius: int) -> Path:
    import rasterio
    print("== %s：栅格统计，半径 %d m" % (city.upper(), radius), flush=True)
    cfg = INPUTS[city]
    schools = load_schools(city)
    result = schools[["school_id", "school_lon", "school_lat"]].copy()
    for name, filename in cfg["rasters"].items():
        path = Path(filename)
        if not path.is_absolute():
            path = Path(cfg["rasters_dir"]) / filename
        if not path.exists():
            print("  [缺失] %s" % path, flush=True)
            continue
        with rasterio.open(path) as src:
            array = src.read(1)
            transform = src.transform
            nodata = src.nodata
            crs = src.crs
        xs, ys = project_schools(city, schools, crs)
        geographic = bool(crs and crs.is_geographic)
        values = zonal_means(array, transform, xs, ys, radius, nodata, geographic,
                             schools["school_lat"].to_numpy())
        result["%s_r%d" % (name, radius)] = values
        print("  %-26s 有效 %4d/%d，均值 %.4f" % (
            name, int(np.isfinite(values).sum()), len(values), np.nanmean(values)), flush=True)
        del array
    target = out_dir(city) / ("%s_raster_r%d.csv" % (city, radius))
    result.to_csv(target, index=False, encoding="utf-8-sig")
    print("  已写出：%s" % target, flush=True)
    return target


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--city", choices=["ny", "hk"], required=True)
    parser.add_argument("--radius", default="all")
    args = parser.parse_args()
    radii = RADII if args.radius == "all" else [int(args.radius)]
    for r in radii:
        process(args.city, r)


if __name__ == "__main__":
    main()
