# E01 多尺度缓冲敏感性（100—500 m）

**目标**：用原始点位数据重算 100/200/300/400/500 m 五种缓冲半径下的街景、事件与栅格变量，
重训两阶段 Hurdle 模型，检验主要结论对分析尺度的敏感性（对应审稿意见 R1-2.4、R2-第3条、R4-第3条）。

## 为什么必须重算

论文现有数据全部按 300 m 缓冲区裁剪：街景影像点位（`view_school_*`）、事件分类结果
（`*_school_crime_class.csv`）、栅格（`*_clipped.tif`）都是 300 m 版本的产物。
因此不能靠缩放现有栅格得到其他尺度，必须回到原始点位与未裁剪栅格重算。

## 输入清单（已确认存在）

| 用途 | 文件 | 位置 |
| --- | --- | --- |
| 学校点位（纽约） | `school_NY.csv` | `data/_linked_raw/stage3_processing/over/` |
| 学校点位（香港） | `school_HK.csv` | 同上 |
| 街景影像点位（全部） | `view_all_NY.shp` / `view_all.shp` | `data/01_base/shared/ToYH/...` |
| 街景要素比例（影像级） | `sv_elements_ratio.csv`（NY 268 MB、HK 142 MB） | 同上 |
| 事件点（纽约，按年） | `{year}_school_crime_class.csv`（2006—2024） | `data/_linked_raw/ny_raw/Arrests/犯罪分类结果/` |
| 事件点（香港） | `hongkong_accidents.csv` | `data/02_paper/HK_dependent_variable/` |
| 未裁剪连续栅格 | `NY_*_density_kernel.tif`、`HK_*_density_kernel.tif`、`*_road_*.tif`、`*_person*.tif` | `data/_linked_raw/stage3_processing/tif_file/` |
| 可达性栅格（多阈值） | `*_within_500m/1000m/2000m.tif` | 同上 |

> 可达性目前只有 500/1000/2000 m 三个阈值版本，100/200/400 m 需要用
> `code/02_features/accessibility_road_network_entropy.ipynb` 中的阈值参数重新生成。

## 运行顺序

```powershell
cd F:\schoolsafety\experiments\E01_multiscale_buffer

# 1) 街景指标：全部影像 → 每所学校在各半径内的均值
python ..\..\code\02_features\ms_svi_aggregate.py --city ny --radius all
python ..\..\code\02_features\ms_svi_aggregate.py --city hk --radius all

# 2) 因变量：各半径内的事件计数
python ..\..\code\02_features\ms_event_counts.py --city ny --radius all
python ..\..\code\02_features\ms_event_counts.py --city hk --radius all

# 3) 连续栅格：各半径内的均值
python ..\..\code\02_features\ms_raster_stats.py --city ny --radius all
python ..\..\code\02_features\ms_raster_stats.py --city hk --radius all

# 4) 建模：各半径的两阶段 Hurdle 模型
python ..\..\code\03_modeling\run_radius_models.py --city ny --radius all
python ..\..\code\03_modeling\run_radius_models.py --city hk --radius all --spatial-cv 5
```

## 产出

- `data/{city}_svi_r{r}.csv`、`{city}_events_r{r}.csv`、`{city}_raster_r{r}.csv`
- `results/{city}_model_r{r}.csv`：AUC、Recall、R²、MAE、样本量、零值比例
- 汇总表 `results/multiscale_summary.csv`（由 `run_all.py` 生成）

## 校验方法（重要）

1. **300 m 复现校验**：新算的 300 m 街景指标应与论文变量
   `ratio_NY_plus_Enclosure_degree_clipped` 等高度一致（相关系数 > 0.9）。
   若差异明显，说明原流程的聚合方式与本文假设不同（见 docs/07 的“待确认”一节）。
2. **事件计数校验**：300 m 事件计数应与 `NY_dependent_variable/newyork_arrests.csv`
   的缓冲计数、`HK_Total_Accidents_Frequency` 对应。
3. 校验通过后再运行其他半径，否则先修正聚合口径。

## 正文落点

按《补充实验执行方案》的判定规则：波动 ≤0.02 时正文一句话＋小表；0.02—0.05 写明区间并限定尺度；
大于 0.05 或方向反转需在正文专段说明并收窄结论。完整三算法 × 五尺度结果放增补 S6。
