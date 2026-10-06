# Code and data for the TGIS manuscript / 论文代码与数据集

Micro-scale environmental correlates of school-area crime and traffic incidents:
street-view evidence from New York and Hong Kong

## 1. 仓库内容

| 目录 | 内容 |
| --- | --- |
| `code/` | 全部实验代码：预处理、特征构建、两阶段 Hurdle 建模与稳健性分析 |
| `experiments/` | 论文使用的派生数据集与结果表（E01 多尺度、E11 情景模拟、E13 拆分因变量） |
| `DATA_DICTIONARY.md` | 数据字典：核心数据集说明与逐文件清单 |
| `data/` | 原始输入，因许可与体量限制未随库分发，见 `data/README.md` |

仓库约 180 MB、162 个文件，最大单文件约 21 MB，直接 push 即可，不需要 Git LFS；
原始输入（约 130 GB）不随仓库分发。逐文件说明与「结果 ↔ 论文图表」对应表见
[`experiments/README.md`](experiments/README.md)。

## 2. 运行环境

Python 3.11；依赖版本见 `requirements.txt`（原始项目使用 conda 环境 `geoKD_final`）。

## 3. 代码结构

```
code/
  config/settings.py       路径与参数；根目录默认为仓库根，可用 SCHOOLSAFETY_ROOT 覆盖
  01_preprocess/           事件分类、学校空间处理、POI 与人口栅格化（notebook，已去除输出）
  02_features/             街景聚合、事件计数、栅格统计、格网数据集、稳健性套件、诊断与补充分析；
                           assemble_summary.py 汇总 100—500 m 的 multiscale_summary.csv
  03_modeling/             按缓冲半径的两阶段 Hurdle 模型
  analysis/                OFNS 拆分数据集与拆分实验套件、类别拆分、时间窗切分、干预情景模拟
```

## 4. 复现顺序

1. 把原始输入按 `data/README.md` 的布局放入 `data/`，或设置 `SCHOOLSAFETY_ROOT` 指向含原始数据的项目根；
2. **E01 主干**（以纽约为例；香港把 `--city` 与 `--split-year` 换成 hk / 2017）：
   `ms_svi_aggregate.py` → `ms_event_counts.py` → `ms_raster_stats.py` → `cell_level_pipeline.py`
   → `robustness_suite.py --radius 300` → `run_multiscale_all.py` → `s6s5_suite.py`
   → `extra_analyses.py` → `assemble_summary.py`；
3. **E13 拆分口径**：`python code/analysis/e13_suite.py` —— 重建“毒品与酒精类 / 交通类”数据集、
   多尺度与稳健性、消融、计数模型、暴露量、时间窗与配对 bootstrap、拆分对比表；
4. **E11 干预情景模拟**：`python code/analysis/scenario_simulation.py`
   （可用 `SC_SEEDS`、`SC_ALGOS`、`SC_NBOOT`、`SC_OUT` 覆盖默认设置）；
5. 其他可选脚本：`split_categories_by_class.py`（按 `Crime_classification` 大类拆分）、
   `temporal_window_split.py`（单一拆分目标的时间窗验证）。

## 4.1 运行提示

- 全流程在单机上约需 1—2 小时：`ms_event_counts.py` 对每个半径都会重新读取全部事件点，
  `ms_svi_aggregate.py` 对每个半径都会重新聚合全部街景比例表；`run_multiscale_all.py` 只读一次、
  速度更快，但仅覆盖 100/200/400/500 m，基准尺度 300 m 需单独运行。
- 空间分块交叉验证使用 `sklearn.cluster.KMeans`。在受限沙箱或无桌面会话中，`threadpoolctl`
  可能因无法加载 MKL/OpenMP 动态库而抛出 `OSError 0xc06d007f`；改用普通交互会话运行即可。
- 学校级合并表同时写出 `{city}_school_features_r{r}.csv`（规范名）与 `{city}_svi_r{r}.csv`
  （旧名，向后兼容）。

## 5. 数据来源

| 数据 | 来源 | 时段 |
| --- | --- | --- |
| 纽约安全事件 | NYPD Arrest Data (Historic)，NYC Open Data | 2006—2024 |
| 香港交通事件 | 香港特别行政区政府运输署交通事故统计 | 2014—2019 |
| 街景影像 | 谷歌街景（纽约）、腾讯地图街景 API（香港） | 2007—2025 / 2008—2025 |
| POI 与路网 | OpenStreetMap | 2019 年 7 月 |
| 人口 | LandScan USA 2021 昼/夜人口栅格 | 2021 |

## 6. 原始数据与获取方式

仓库只包含代码、派生数据集与结果表，原始输入因许可与体量限制未随库分发：

| 数据 | 获取方式 |
| --- | --- |
| 纽约逮捕记录（2006—2024） | NYC Open Data 的 NYPD Arrest Data (Historic) 公开数据集 |
| 香港交通事故（2014—2019） | 香港特别行政区政府运输署；再分发受限，仓库只提供聚合后的 100 m 格网计数 |
| 街景影像 | Google Street View API（纽约）、腾讯地图街景 API（香港），按各自服务条款获取 |
| POI 与路网 | OpenStreetMap（2019 年 7 月快照，ODbL） |
| 人口栅格 | LandScan USA 2021（纽约）；香港使用配套的 10 m 人口栅格 |

把原始文件按 `data/README.md` 的布局放好后即可运行。`code/01_preprocess/` 下的 notebook 是论文
原始工作副本，内部保留了当时的绝对路径（`E:/chuli/...`、`F:/schoolsafety/...`），如需重跑可批量替换：

```powershell
Get-ChildItem code -Recurse -Include *.ipynb | ForEach-Object {
  (Get-Content $_ -Raw) -replace 'F:/schoolsafety/data', 'D:/myrepo/data' | Set-Content $_ -Encoding UTF8
}
```

## 7. 说明

- 代码注释为中文，必要处保留英文术语；如需英文注释版本可另行处理。
- 情景模拟输出的是模型在假设设计状态下的隐含变化，不等同于干预效果估计。
- `experiments/E13_split_categories/results/e13_格网构建bug修正记录.md` 记录了格网级时间窗脚本中
  特征合并键错误与输出文件名硬编码两个 bug 的修正过程与逐格网核对结果。
- 基准尺度 300 m 的核心规模：纽约 26,375 个格网、3,962,951 起事件；香港 15,564 个格网、63,831 起事故。
