# E11 干预情景模拟

**目标**：把正文 6.2 节的空间更新建议转成可核查的量化推演——把取值最差（高于第 75 百分位）的格网特征
下调到该变量的中位数水平，观察模型预测事件数的变化。

## 设定

| 项目 | 设定 |
| --- | --- |
| 单元 | 100 m 格网、300 m 缓冲区 |
| 因变量 | 纽约财产犯罪、纽约暴力犯罪（按 `Crime_classification` 现场重建格网计数）、香港交通事故 |
| 特征 | 纽约 19 个、香港 17 个环境特征，不含历史事件与经纬度 |
| 模型 | 两阶段 Hurdle（XGBoost / LightGBM / 随机森林） |
| 种子与实现 | 42, 7, 2024, 101, 555 × 3 种算法 = 15 个实现；每个实现 80/20 划分 |
| 主口径 | 分位数整改（> P75 下调到中位数） |
| 辅助口径 | ±1 标准差（仅作参考，零膨胀变量会越界） |
| bootstrap | 500 次格网级配对重抽样 |

## 运行

```bash
python code/analysis/scenario_simulation.py
# 可用环境变量覆盖默认设置：
#   SC_SEEDS / SC_ALGOS / SC_NBOOT / SC_OUT
```

## 产出

- `results/scenario_results_raw.csv`：15 个实现的逐次结果；
- `results/scenario_summary.csv`：按城市 × 情景 × 方法汇总（含逐算法值、实现间区间、bootstrap 置信区间）；
- `results/scenario_note.md`、`scenario_manifest.json`：结果说明与运行清单；
- `results/figures/fig_scenario_main.png`（正文图 10，两面板）、`fig_scenario_effects.png`（三面板）；
- `results/ny_cells_property_r300.csv`、`ny_cells_violent_r300.csv`：情景分析使用的纽约格网数据集。

## 注意事项

- 情景模拟反映的是模型在假设设计特征改变下的**边际预测变化**，不等于干预效果估计，不能替代准实验设计；
- `share_cells_reduced`（预测风险下降的格网占比）对零点附近的微小扰动极敏感，重跑之间可能相差若干个百分点，
  不建议写入论文；
- 单变量整改会生成现实中不存在的特征组合（例如围合度下降而天空开阔度不变），结果只作方向性参考。
