# -*- coding: utf-8 -*-
"""Street-view indicators aggregated by school and buffer radius. 按学校与缓冲半径聚合街景指标。"""
import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from config.settings import INPUTS, RADII, SVI_INDEX_COLUMNS, out_dir  # noqa: E402

CHUNK = 20000


def read_csv_any(path, **kwargs):
    """按常见中文编码依次尝试读取 CSV。"""
    last = None
    for enc in ("utf-8-sig", "utf-8", "gb18030", "gbk", "latin-1"):
        try:
            return pd.read_csv(path, encoding=enc, **kwargs)
        except UnicodeDecodeError as exc:
            last = exc
            continue
    raise last


def load_schools(city: str) -> pd.DataFrame:
    path = Path(INPUTS[city]["schools"])
    if not path.exists():
        path = Path(INPUTS[city]["schools_alt"])
    df = read_csv_any(path)
    lower = {c.lower(): c for c in df.columns}
    lon = next(lower[k] for k in ("lon", "longitude", "x", "经度", "point_x") if k in lower)
    lat = next(lower[k] for k in ("lat", "latitude", "y", "纬度", "point_y") if k in lower)
    out = df.rename(columns={lon: "school_lon", lat: "school_lat"})[["school_lon", "school_lat"]].copy()
    out.insert(0, "school_id", np.arange(len(out)))
    return out.dropna().reset_index(drop=True)


def load_svi(city: str) -> pd.DataFrame:
    cfg = INPUTS[city]
    views_path = Path(cfg["svi_views"])
    if views_path.suffix.lower() == ".shp" and views_path.exists():
        import geopandas as gpd
        views = gpd.read_file(views_path)
        key = cfg["svi_join_key"]
        if key not in views.columns:
            candidates = [c for c in views.columns if c.lower() in ("panoid", "svid", "id", "pano_id")]
            key = candidates[0] if candidates else views.columns[0]
        views = pd.DataFrame({cfg["svi_join_key"]: views[key].astype(str),
                              "view_lon": views.geometry.x, "view_lat": views.geometry.y})
    else:
        views = pd.read_csv(views_path.with_suffix(".csv"))
    ratios = read_csv_any(cfg["svi_ratios"])
    ratios = ratios.rename(columns={cfg["svi_ratio_key"]: cfg["svi_join_key"]})
    ratios[cfg["svi_join_key"]] = ratios[cfg["svi_join_key"]].astype(str)
    raw_rows = len(ratios)
    # 论文口径：同一全景的多行记录（通常 4 个朝向）先取均值，得到「每张全景一个值」
    numeric_cols = [c for c in ratios.columns if c != cfg["svi_join_key"]]
    ratios = ratios.groupby(cfg["svi_join_key"], as_index=False)[numeric_cols].mean()
    print("  影像级比例表：%d 行 → 全景级 %d 行（按 svid 取均值）" % (raw_rows, len(ratios)))
    merged = views.merge(ratios, on=cfg["svi_join_key"], how="inner")
    print("  影像点位 %d，比例表 %d，合并后 %d" % (len(views), len(ratios), len(merged)))
    return merged


def to_xyz(lon, lat):
    lon = np.radians(np.asarray(lon, dtype=float))
    lat = np.radians(np.asarray(lat, dtype=float))
    return np.cos(lat) * np.cos(lon), np.cos(lat) * np.sin(lon), np.sin(lat)


def pair_distances(clon, clat, vlon, vlat):
    """(n_school, n_view) 的球面距离（米），用单位向量点积换算。"""
    sx, sy, sz = to_xyz(clon, clat)
    vx, vy, vz = to_xyz(vlon, vlat)
    dot = np.outer(sx, vx) + np.outer(sy, vy) + np.outer(sz, vz)
    dot = np.clip(dot, -1.0, 1.0)
    return 6371000.0 * np.arccos(dot)


def aggregate(city: str, radius: int) -> Path:
    print("== %s：街景指标聚合，半径 %d m" % (city.upper(), radius))
    schools = load_schools(city)
    svi = load_svi(city)
    n_school = len(schools)

    sums = {name: np.zeros(n_school) for name in SVI_INDEX_COLUMNS}
    counts = np.zeros(n_school)
    class_cols = {}
    for name, classes in SVI_INDEX_COLUMNS.items():
        cols = [c for c in classes if c in svi.columns]
        class_cols[name] = cols
        if not cols:
            print("  [跳过] %s 无对应类别" % name)

    values = {name: svi[cols].sum(axis=1).to_numpy(dtype=float)
              for name, cols in class_cols.items() if cols}
    vlon = svi["view_lon"].to_numpy()
    vlat = svi["view_lat"].to_numpy()

    for start in range(0, len(svi), CHUNK):
        stop = min(start + CHUNK, len(svi))
        dist = pair_distances(schools["school_lon"], schools["school_lat"],
                              vlon[start:stop], vlat[start:stop])
        inside = dist <= radius
        counts += inside.sum(axis=1)
        for name, arr in values.items():
            block = np.where(inside, arr[start:stop][None, :], np.nan)
            sums[name] += np.nansum(block, axis=1)
        print("  处理影像 %d/%d" % (stop, len(svi)), flush=True)

    result = schools[["school_id", "school_lon", "school_lat"]].copy()
    for name in SVI_INDEX_COLUMNS:
        if name in sums:
            with np.errstate(invalid="ignore", divide="ignore"):
                result["ratio_%s_r%d" % (name, radius)] = np.where(counts > 0, sums[name] / counts, np.nan)
    result["svi_count_r%d" % radius] = counts.astype(int)

    target = out_dir(city) / ("%s_svi_r%d.csv" % (city, radius))
    result.to_csv(target, index=False, encoding="utf-8-sig")
    print("  已写出：%s（%d 所学校，平均每校 %d 张影像）"
          % (target, len(result), int(counts.mean())))
    return target


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--city", choices=["ny", "hk"], required=True)
    parser.add_argument("--radius", default="all")
    args = parser.parse_args()
    radii = RADII if args.radius == "all" else [int(args.radius)]
    for r in radii:
        aggregate(args.city, r)


if __name__ == "__main__":
    main()
