# E01 多尺度缓冲敏感性（100—500 m）

**目标**：在 100/200/300/400/500 m 五种学校缓冲半径下重算街景、事件与栅格变量，重建 100 m 格网数据集并重训
两阶段 Hurdle 模型，检验主要结论对分析尺度的敏感性。

## 为什么必须重算

论文的原始数据全部按 300 m 缓冲裁剪：街景点位（`view_school_*`）、事件分类结果（`*_school_crime_class.csv`）、
栅格（`*_clipped.tif`）都是 300 m 版本的产物。因此不能靠缩放现有栅格得到其他尺度，必须回到原始点位与
未裁剪栅格重算。E13 拆分口径也一样：非基准半径的特征已随半径重算，不再复用 300 m 的街景比例。

## 输入清单（放在 `data/`，或在 `code/config/settings.py` 中改 `INPUTS`）

| 用途 | 文件 | 位置 |
| --- | --- | --- |
| 学校点位 | `school_NY.csv`、`school_HK.csv` | `data/_linked_raw/stage3_processing/over/` |
| 街景影像点位 | `view_all_NY.shp`、`view_all.shp` | `data/01_base/shared/ToYH/` |
| 街景要素比例（影像级） | `sv_elements_ratio.csv` | 同上 |
| 事件点（纽约，按年） | `{year}_school_crime_class.csv`（2006—2024） | `data/_linked_raw/ny_raw/Arrests/犯罪分类结果/` |
| 事件点（香港） | `hongkong_accidents.csv` | `data/02_paper/HK_dependent_variable/` |
| 未裁剪连续栅格 | `*_density_kernel.tif`、`*_road_*.tif`、`*_person*.tif`、LandScan 昼夜人口 | `data/_linked_raw/stage3_processing/tif_file/` |

## 运行顺序

```bash
# 1) 学校级特征
python code/02_features/ms_svi_aggregate.py --city ny --radius all
python code/02_features/ms_event_counts.py  --city ny --radius all
python code/02_features/ms_raster_stats.py  --city ny --radius all

# 2) 100 m 格网数据集与两阶段模型
python code/02_features/cell_level_pipeline.py --city ny --radius all
python code/03_modeling/run_radius_models.py   --city ny --radius all

# 3) 稳健性与诊断
python code/02_features/robustness_suite.py --city ny --radius 300 --split-year 2018
python code/02_features/s6s5_suite.py        # 消融、计数模型、校准曲线、暴露量
python code/02_features/extra_analyses.py    # 三算法表、Moran's I、Top-k、SHAP 稳定性

# 4) 其余半径的批量重建与汇总
python code/02_features/run_multiscale_all.py
python code/02_features/assemble_summary.py

# 香港：把 --city 换成 hk、--split-year 换成 2017 重复一遍
```

## 产出

- `data/`：各半径的学校级特征表（`{city}_school_features_r{r}.csv` 为规范名，`{city}_svi_r{r}.csv` 为旧名兼容）、
  事件计数表、100 m 格网数据集；
- `results/`：逐半径模型指标、稳健性表、VIF，以及汇总表 `multiscale_summary.csv`；
- `results/figures/`：各尺度的校准曲线与 PR 曲线数据与图件。

## 校验方法

1. **300 m 复现校验**：新算的街景指标应与论文变量（`ratio_NY_plus_*`）高度一致（相关系数 > 0.9）；
2. **事件计数校验**：300 m 事件计数应与 `newyork_arrests.csv` 的缓冲计数、香港事故栅格合计（64,871 起）对应，
   学校缓冲区内分别为 3,962,951 与 63,831 起；
3. 校验通过后再扩展到其他半径。
