# E11 情景模拟 运行配置
- 脚本：code/03_modeling/scenario_simulation.py（工作副本 .workbuddy/st27/）
- 运行：run_env.bat（geoKD_final）
- 因变量（3 组）：纽约财产犯罪、纽约暴力犯罪（均按 Crime_classification 现场重建格网计数）、香港交通事故
- 单元：100 m 格网，300 m 缓冲区
- 特征：纽约 19 个、香港 17 个环境特征（split_features），不含历史事件与经纬度
- 模型：两阶段 Hurdle（XGBoost / LightGBM / 随机森林）
- 种子：42, 7, 2024, 101, 555；每个实现 80/20 划分
- 主口径：分位数整改版（>P75 -> 中位数）；辅助口径：±1SD（P1-P99 截断）
- bootstrap：500 次格网级配对重抽样（XGBoost/seed=42）
- 输出：results/scenario_summary.csv、scenario_results_raw.csv、scenario_note.md、
  ny_cells_property_r300.csv、ny_cells_violent_r300.csv、figures/fig_scenario_effects.png
- 复现：环境变量 SC_SEEDS / SC_ALGOS / SC_NBOOT / SC_OUT
