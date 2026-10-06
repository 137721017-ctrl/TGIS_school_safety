# -*- coding: utf-8 -*-
"""Paths and parameters. Root defaults to the repository root; override with SCHOOLSAFETY_ROOT.
路径与参数配置；根目录默认为仓库根，可用环境变量 SCHOOLSAFETY_ROOT 覆盖。
"""
import os
from pathlib import Path

ROOT = Path(os.environ.get("SCHOOLSAFETY_ROOT",
                        Path(__file__).resolve().parents[2]))
DATA = ROOT / "data"
RAW = DATA / "_linked_raw"

# ---------------------------------------------------------------- 输入数据
INPUTS = {
    "ny": {
        "schools": RAW / "stage3_processing" / "over" / "school_NY.csv",
        "schools_alt": DATA / "01_base" / "_stage1_processed" / "newyorkschool_Fromshp.csv",
        # 事件点（按年份的犯罪分类结果，含坐标与类别）
        "events_dir": RAW / "ny_raw" / "Arrests" / "犯罪分类结果",
        "events_pattern": "{year}_school_crime_class.csv",
        "event_years": list(range(2006, 2025)),
        "events_combined": DATA / "02_paper" / "NY_dependent_variable" / "newyork_arrests.csv",
        # 街景：全部影像点位 + 每个影像的语义要素比例
        "svi_views": DATA / "01_base" / "shared" / "ToYH" / "New York SVI" / "view_all_NY.shp",
        "svi_ratios": DATA / "01_base" / "shared" / "ToYH" / "New York SVI" / "sv_elements_ratio.csv",
        "svi_join_key": "panoid",          # 视图点位中的关联键
        "svi_ratio_key": "svid",           # 比例表中的关联键
        # 连续栅格（尺度无关的密度/人口/路网表面）
        "rasters_dir": RAW / "stage3_processing" / "tif_file",
        "rasters": {
            "busStation_density": "NY_busStation_cut_density_kernel.tif",
            "crossing_density": "NY_crossing_cut_density_kernel.tif",
            "shop_density": "NY_shop_cut_density_kernel.tif",
            "street_lamp_density": "NY_street_lamp_cut_density_kernel.tif",
            "traffic_signals_density": "NY_traffic_signals_cut_density_kernel.tif",
            "speed_camera_density": "NY_speed_camera_cut_density_kernel.tif",
            "road": "NY_road_cut_raster.tif",
            "person": r"F:\schoolsafety\data\02_paper\NY_independent_variable\NY_person_clipped_clipped.tif",
            "landscan_day": r"F:\schoolsafety\data\02_paper\NY_independent_variable\landscan-usa-2021-conus-day_ny_clipped_clipped.tif",
            "landscan_night": r"F:\schoolsafety\data\02_paper\NY_independent_variable\landscan-usa-2021-conus-night_ny_clipped_clipped.tif",
        },
        # 需要按半径重算的可达性栅格（现有多阈值版本）
        "accessibility": {
            "shop_within_500m": "NY_school_to_shop_accessibility_10m_within_500m.tif",
            "shop": "NY_school_to_shop_accessibility_10m.tif",
            "bus_within_500m": "NY_school_to_bus_accessibility_10m_within_500m.tif",
            "bus": "NY_school_to_bus_accessibility_10m.tif",
        },
        "utm_epsg": 32618,
    },
    "hk": {
        "schools": RAW / "stage3_processing" / "over" / "school_HK.csv",
        "events_combined": DATA / "02_paper" / "HK_dependent_variable" / "hongkong_accidents.csv",
        "events_dir": RAW / "stage3_processing" / "road_acc",
        "events_pattern": None,
        "event_years": list(range(2014, 2020)),
        "svi_views": DATA / "01_base" / "shared" / "ToYH" / "Hong Kong" / "view_all.shp",
        "svi_ratios": DATA / "01_base" / "shared" / "ToYH" / "Hong Kong" / "sv_elements_ratio.csv",
        "svi_join_key": "panoid",
        "svi_ratio_key": "svid",
        "rasters_dir": RAW / "stage3_processing" / "tif_file",
        "rasters": {
            "busStation_density": "HK_busStation_density_kernel.tif",
            "crossing_density": "HK_crossing_density_kernel.tif",
            "shop_density": "HK_shop_density_kernel.tif",
            "street_lamp_density": "HK_street_lamp_density_kernel.tif",
            "traffic_signals_density": "HK_traffic_signals_density_kernel.tif",
            "speed_camera_density": "HK_speed_camera_density_kernel.tif",
            "road": "HK_road_raster.tif",
            "person": r"F:\schoolsafety\data\02_paper\HK_independent_variable\HK_person_clipped_clipped.tif",
        },
        "accessibility": {
            "shop_within_500m": "HK_school_to_shop_accessibility_10m_within_500m.tif",
            "shop": "HK_school_to_shop_accessibility_10m.tif",
            "bus_within_500m": "HK_school_bus_accessibility_within_500m.tif",
            "bus": "HK_school_bus_accessibility.tif",
        },
        "utm_epsg": 32650,
    },
}

# ---------------------------------------------------------------- 参数
RADII = [100, 200, 300, 400, 500]          # 敏感性分析使用的缓冲半径（米）
BASELINE_RADIUS = 300                      # 论文正文使用的基准半径
SVI_INDEX_COLUMNS = {                      # 街景指标 → 原始分割类别
    "Enclosure_degree": ["building", "fence", "wall", "bridge", "ceiling", "railing", "house", "tower"],
    "Greening_degree": ["tree", "grass", "plant"],
    "Openness": ["sky"],
    "Pedestrian_density": ["person"],
    "Protection": ["awning", "canopy", "booth", "shelter"],
    "Street_furniture": ["bench", "streetlight", "pole", "signboard", "box", "lamp", "ashcan", "bicycle"],
    "Surveillance_and_lighting": ["light", "streetlight"],
    "Traffic_flow": ["car", "truck", "van", "bus", "minibike", "traffic"],
}
EVENT_CLASS_COLUMN = "crime_class"          # 纽约事件表的犯罪类型列（若列名不同请修改）
EVENT_YEAR_COLUMN = "ARREST_DATE"
EVENT_LON_COLUMN = "longitude"
EVENT_LAT_COLUMN = "latitude"

# ---------------------------------------------- E13 拆分因变量的 OFNS 分组
# 论文正文把 NYPD 的 11 个 OFNS_DESC 类别合并为“毒品、酒精与交通类违法”。
# E13 拆分分析把该合并类别还原为两组：group_a 为毒品与酒精类，group_b 为交通类
# （含酒驾与毒驾）。分组口径与增补 S3 表 3.1、表 3.2 完全一致。
OFNS_GROUPS = {
    "a": ["DANGEROUS DRUGS",
          "CANNABIS RELATED OFFENSES",
          "ALCOHOLIC BEVERAGE CONTROL LAW",
          "LOITERING FOR DRUG PURPOSES",
          "UNDER THE INFLUENCE, DRUGS"],
    "b": ["VEHICLE AND TRAFFIC LAWS",
          "MOVING INFRACTIONS",
          "OTHER TRAFFIC INFRACTION",
          "PARKING OFFENSES",
          "INTOXICATED & IMPAIRED DRIVING",
          "INTOXICATED/IMPAIRED DRIVING"],
}
OFNS_GROUP_LABELS = {"a": "y_drug_alcohol", "b": "y_traffic"}


def out_dir(city: str, kind: str = "data") -> Path:
    """返回实验输出目录：experiments/E01_multiscale_buffer/<kind>/"""
    base = ROOT / "experiments" / "E01_multiscale_buffer"
    path = base / kind
    path.mkdir(parents=True, exist_ok=True)
    return path
