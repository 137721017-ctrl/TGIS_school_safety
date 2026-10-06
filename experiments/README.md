# 实验结果目录说明

`experiments/` 保存论文使用的派生数据集与结果表。原始输入（逮捕记录、街景影像、栅格）不随仓库分发，
见 `../data/README.md`。每个子目录都能由 `code/` 下的脚本重新生成。

| 目录 | 内容 | 生成脚本 |
| --- | --- | --- |
| `E01_multiscale_buffer/` | 100—500 m 五个尺度的学校级特征表、100 m 格网数据集、两阶段 Hurdle 模型与稳健性结果 | `code/02_features/` 与 `code/03_modeling/` 下的脚本，见该目录 README |
| `E11_scenario_simulation/` | 干预情景模拟的逐实现结果、汇总表与两张图 | `code/analysis/scenario_simulation.py` |
| `E13_split_categories/` | 纽约"毒品与酒精类 / 交通类"拆分因变量的数据集与全部结果表 | `code/analysis/ofns_split.py`、`code/analysis/e13_suite.py` |

## 结果文件与论文的对应

| 论文位置 | 结果文件 |
| --- | --- |
| 正文表 1、增补表 1.2（多尺度稀疏性与性能） | `E01_multiscale_buffer/results/multiscale_summary.csv` |
| 正文表 2（验证策略与空间残差） | `E01_multiscale_buffer/results/{ny,hk}_robustness_r300.csv`、`diagnostics_scale_table.csv` |
| 正文表 3、表 4（模型性能） | `E01_multiscale_buffer/results/{ny,hk}_cell_model_r*.csv`、`{ny,hk}_robustness_r*.csv` |
| 正文表 5、表 6（消融） | `E01_multiscale_buffer/results/ablation_scale_table.csv` |
| 正文表 7（配对 bootstrap） | `E01_multiscale_buffer/results/ablation_scale_table.csv`（`G7_vs_G1_delta` 行） |
| 增补表 2.1、2.2（三算法与诊断） | `E01_multiscale_buffer/results/algo_scale_table.csv`、`diagnostics_scale_table.csv` |
| 增补表 2.3（暴露量调整） | `E01_multiscale_buffer/results/exposure_second_stage.csv` |
| 增补表 5.1（计数模型比较） | `E01_multiscale_buffer/results/count_model_comparison.csv` |
| 增补表 6.2（VIF） | `E01_multiscale_buffer/results/{ny,hk}_vif_r*.csv` |
| 增补表 7.1（纽约多算法与消融） | `E01_multiscale_buffer/results/ablation_scale_table.csv`、`algo_scale_table.csv` |
| 增补表 9.1、正文表 6（情景模拟） | `E11_scenario_simulation/results/scenario_summary.csv`、`scenario_results_raw.csv` |
| 正文图 5（校准与 PR 曲线）、增补 S3 拆分口径曲线 | `E01_multiscale_buffer/results/figures/` |
| 正文图 10（情景效应） | `E11_scenario_simulation/results/figures/fig_scenario_main.png` |
| 增补 S3 表 3.2（拆分对比） | `E13_split_categories/results/split_targets_r300.csv` |
| 增补 S3 说明段（多尺度、诊断、暴露量、时间窗） | `E13_split_categories/results/drug_alcohol_*.csv` |

## 复现顺序

见仓库根目录 `README.md` 第 4 节。整体顺序是：先跑通 E01 主干（特征 → 格网数据集 → 模型 → 稳健性），
再跑 E13 拆分口径与 E11 情景模拟。单机全流程约 1—2 小时。
