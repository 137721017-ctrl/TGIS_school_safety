# -*- coding: utf-8 -*-
"""Incident counts per school within each buffer radius. 各缓冲半径内的学校事件计数。"""
import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from config.settings import INPUTS, RADII, out_dir  # noqa: E402
from ms_svi_aggregate import CHUNK, load_schools, pair_distances, read_csv_any  # noqa: E402


def pick_column(df: pd.DataFrame, candidates, fallback=None):
    lower = {c.lower(): c for c in df.columns}
    for cand in candidates:
        if cand.lower() in lower:
            return lower[cand.lower()]
    return fallback


def load_events(city: str) -> pd.DataFrame:
    cfg = INPUTS[city]
    frames = []
    if cfg.get("events_dir") and cfg.get("events_pattern"):
        folder = Path(cfg["events_dir"])
        for year in cfg["event_years"]:
            path = folder / cfg["events_pattern"].format(year=year)
            if not path.exists():
                continue
            df = read_csv_any(path, low_memory=False)
            lon = pick_column(df, ["longitude", "lon", "x"])
            lat = pick_column(df, ["latitude", "lat", "y"])
            if lon is None or lat is None:
                continue
            keep = pd.DataFrame({"event_lon": pd.to_numeric(df[lon], errors="coerce"),
                                 "event_lat": pd.to_numeric(df[lat], errors="coerce")})
            keep["year"] = year
            klass = pick_column(df, ["crime_class", "CrimeType", "crime_type", "class"])
            if klass is not None:
                keep["crime_class"] = df[klass].astype(str)
            frames.append(keep.dropna(subset=["event_lon", "event_lat"]))
            print("  载入 %d 年：%d 条" % (year, len(keep)))
    if not frames:
        path = Path(cfg["events_combined"])
        df = read_csv_any(path, low_memory=False)
        lon = pick_column(df, ["longitude", "lon", "x", "LONGITUDE"])
        lat = pick_column(df, ["latitude", "lat", "y", "LATITUDE"])
        keep = pd.DataFrame({"event_lon": pd.to_numeric(df[lon], errors="coerce"),
                             "event_lat": pd.to_numeric(df[lat], errors="coerce")})
        date_col = pick_column(df, ["date", "Date", "date_time", "Date_Time"])
        if date_col is not None:
            keep["year"] = pd.to_datetime(df[date_col], errors="coerce").dt.year
        frames.append(keep.dropna(subset=["event_lon", "event_lat"]))
    events = pd.concat(frames, ignore_index=True)
    print("  事件点合计：%d" % len(events))
    return events


def count_events(city: str, radius: int) -> Path:
    print("== %s：事件计数，半径 %d m" % (city.upper(), radius))
    schools = load_schools(city)
    events = load_events(city)
    n_school = len(schools)

    total = np.zeros(n_school)
    by_year, by_class = {}, {}
    elon = events["event_lon"].to_numpy()
    elat = events["event_lat"].to_numpy()
    years = events["year"].to_numpy() if "year" in events.columns else None
    classes = events["crime_class"].to_numpy() if "crime_class" in events.columns else None

    for start in range(0, len(events), CHUNK):
        stop = min(start + CHUNK, len(events))
        inside = pair_distances(schools["school_lon"], schools["school_lat"],
                                elon[start:stop], elat[start:stop]) <= radius
        total += inside.sum(axis=1)
        if years is not None:
            for year in np.unique(years[start:stop]):
                if pd.isna(year):
                    continue
                by_year.setdefault(int(year), np.zeros(n_school))
                by_year[int(year)] += inside[:, years[start:stop] == year].sum(axis=1)
        if classes is not None:
            for klass in np.unique(classes[start:stop]):
                by_class.setdefault(str(klass), np.zeros(n_school))
                by_class[str(klass)] += inside[:, classes[start:stop] == klass].sum(axis=1)
        print("  处理事件 %d/%d" % (stop, len(events)), flush=True)

    result = schools[["school_id", "school_lon", "school_lat"]].copy()
    result["event_count_r%d" % radius] = total.astype(int)
    for year, arr in sorted(by_year.items()):
        result["count_%d_r%d" % (year, radius)] = arr.astype(int)
    for klass, arr in sorted(by_class.items()):
        safe = klass.replace(" ", "_").replace("/", "_")[:40]
        result["count_%s_r%d" % (safe, radius)] = arr.astype(int)

    target = out_dir(city) / ("%s_events_r%d.csv" % (city, radius))
    result.to_csv(target, index=False, encoding="utf-8-sig")
    print("  已写出：%s（事件总数 %d）" % (target, int(total.sum())))
    return target


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--city", choices=["ny", "hk"], required=True)
    parser.add_argument("--radius", default="all")
    args = parser.parse_args()
    radii = RADII if args.radius == "all" else [int(args.radius)]
    for r in radii:
        count_events(args.city, r)


if __name__ == "__main__":
    main()
