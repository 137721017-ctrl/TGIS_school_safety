# Code and data for the TGIS manuscript / 论文代码与数据集

Micro-scale environmental correlates of school-area crime and traffic incidents:
street-view evidence from New York and Hong Kong

## 1. 内容

| 目录 | 内容 |
| --- | --- |
| `code/` | 全部实验代码（预处理、特征构建、建模、分析） |
| `experiments/` | 派生数据集与结果表：E01 多尺度、E13 类别拆分与时间窗、E11 干预情景模拟 |
| `DATA_DICTIONARY.md` | 数据字典（核心数据集说明 + 逐文件清单） |
| `data/` | 原始输入，因许可限制未随库分发，见 `data/README.md` |

## 2. 运行环境

Python 3.11；依赖版本见 `requirements.txt`（原始项目使用 conda 环境 `geoKD_final`）。

## 3. 代码结构

```
code/
  config/settings.py       路径与参数；根目录默认为仓库根，可用 SCHOOLSAFETY_ROOT 覆盖
  01_preprocess/           事件分类、学校空间处理、POI 与人口栅格化（notebook，已去除输出）
  02_features/             街景聚合、事件计数、栅格统计、格网数据集、稳健性套件、诊断与补充分析
  03_modeling/             按缓冲半径的两阶段 Hurdle 模型
  analysis/                类别拆分、时间窗切分、干预情景模拟
```

## 4. 复现顺序

1. 把原始输入按 `data/README.md` 的布局放入 `data/`，或设置 `SCHOOLSAFETY_ROOT` 指向含原始数据的项目根；
2. `python code/02_features/run_multiscale_all.py` —— 重建 100—500 m 特征并训练格网级模型（输出 E01）；
3. `python code/analysis/split_categories_by_class.py --class-name "Property crimes" --col y_property --radii 100,200,300,400,500 --name property` —— E13 类别拆分数据集；
4. `python code/analysis/temporal_window_split.py --radius 300 --split-year 2018` —— 时间窗切分与配对 bootstrap；
5. `python code/analysis/scenario_simulation.py` —— E11 干预情景模拟（可用 `SC_SEEDS`、`SC_ALGOS`、`SC_NBOOT`、`SC_OUT` 覆盖默认设置）。

## 5. 数据来源

| 数据 | 来源 | 时段 |
| --- | --- | --- |
| 纽约安全事件 | NYPD Arrest Data (Historic)，NYC Open Data | 2006—2024 |
| 香港交通事件 | 香港特别行政区政府运输署交通事故统计 | 2014—2019 |
| 街景影像 | 谷歌街景（纽约）、腾讯地图街景 API（香港） | 2007—2025 / 2008—2025 |
| POI 与路网 | OpenStreetMap | 2019 年 7 月 |
| 人口 | LandScan USA 2021 昼/夜人口栅格 | 2021 |

## 6. 说明

- 数据集约 200 MB；如需上传 GitHub，建议使用 Git LFS 或随论文发布 Zenodo release。
- 代码注释为中文，必要处保留英文术语；如需英文注释版本可另行处理。
- 情景模拟输出的是模型在假设设计状态下的隐含变化，不等同于干预效果估计。
- `experiments/E13_split_categories/results/e13_格网构建bug修正记录.md` 记录了格网级时间窗脚本中
  特征合并键错误与输出文件名硬编码两个 bug 的修正过程与逐格网核对结果。
