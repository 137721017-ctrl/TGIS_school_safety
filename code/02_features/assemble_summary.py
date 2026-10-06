# -*- coding: utf-8 -*-
"""Assemble the 100-500 m multiscale summary table (E01).

由各半径的稳健性结果表汇总出 multiscale_summary.csv（城市 x 五个缓冲半径）。
run_multiscale_all.py 只覆盖 100/200/400/500 m，基准尺度 300 m 由
cell_level_pipeline.py 与 robustness_suite.py 单独生成，因此需要本脚本把
300 m 一并纳入汇总，否则汇总表会缺少基准尺度的两行。

用法::

    python code/02_features/assemble_summary.py
"""
import sys
from pathlib import Path

import pandas as pd

HERE = Path(__file__).resolve()
sys.path.insert(0, str(HERE.parents[1]))
from config.settings import RADII, out_dir  # noqa: E402


def summary_row(city, radius):
    """从 {city}_robustness_r{radius}.csv 与格网数据集汇总一行。"""
    rob_path = out_dir(city, "results") / ("%s_robustness_r%d.csv" % (city, radius))
    cells_path = out_dir(city) / ("%s_cells_r%d.csv" % (city, radius))
    if not rob_path.exists() or not cells_path.exists():
        print("  [跳过] %s r=%d：缺少 %s" % (
            city.upper(), radius,
            rob_path.name if not rob_path.exists() else cells_path.name), flush=True)
        return None
    rob = pd.read_csv(rob_path)
    cells = pd.read_csv(cells_path, usecols=["event_count"])
    y = pd.to_numeric(cells["event_count"], errors="coerce").fillna(0)
    return {
        "city": city,
        "radius": radius,
        "cells": int(len(cells)),
        "zero_ratio": float((y == 0).mean()),
        "random_AUC": float(rob.loc[rob.scheme == "random_80_20", "AUC"].mean()),
        "spatial_AUC": float(rob.loc[rob.scheme.str.startswith("spatial"), "AUC"].mean()),
        "temporal_AUC": float(rob.loc[rob.scheme.str.startswith("temporal"), "AUC"].mean()),
    }


def main():
    rows = []
    for city in ("ny", "hk"):
        for radius in RADII:
            row = summary_row(city, radius)
            if row:
                rows.append(row)
    if not rows:
        raise SystemExit("no robustness tables found; run the E01 pipeline first")
    table = pd.DataFrame(rows).sort_values(["city", "radius"]).reset_index(drop=True)
    target = out_dir("ny", "results") / "multiscale_summary.csv"
    table.to_csv(target, index=False, encoding="utf-8-sig")
    print(table.to_string(index=False), flush=True)
    print("written: %s (%d rows)" % (target, len(table)), flush=True)


if __name__ == "__main__":
    main()
