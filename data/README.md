# 原始输入数据说明（未随库分发）

本目录用于存放原始输入。由于数据许可与体量限制，仓库只包含派生数据集与结果表；
复现全部实验需要把下列原始文件按 `code/config/settings.py` 中的 `INPUTS` 布局放入本目录，
或把环境变量 `SCHOOLSAFETY_ROOT` 指向本地含原始数据的项目根目录。

## 需要的原始输入

| 变量 | 说明 | 在 settings.py 中的键 |
| --- | --- | --- |
| 学校点位 | 纽约 `school_NY.csv`、香港 `school_HK.csv`（含经纬度） | `schools` |
| 纽约事件 | 按年分类的逮捕记录 `{year}_school_crime_class.csv`（2006—2024，含 `Crime_classification`、经纬度） | `events_dir` / `events_pattern` |
| 香港事件 | 交通事故合并表 `hongkong_accidents.csv`（2014—2019） | `events_combined` |
| 街景点位与比例 | `view_all_*.shp` 与 `sv_elements_ratio.csv`（影像级语义要素比例） | `svi_views` / `svi_ratios` |
| 连续栅格 | 公交站、过街、商店、路灯、信号灯、测速相机核密度与路网栅格（10 m） | `rasters` |
| 人口 | LandScan USA 2021 昼/夜人口栅格 | `rasters` |

数据来源与时段见仓库根目录 `README.md` 第 5 节。
