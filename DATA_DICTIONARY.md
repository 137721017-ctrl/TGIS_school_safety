# Data dictionary. 数据字典

所有派生数据集与结果表都在 `experiments/` 下；原始输入（逮捕记录、街景影像点位、栅格）因许可限制不在库内，见 `data/README.md`。

## 1. 核心数据集

| 路径 | 行 × 列 | 内容 |
| --- | --- | --- |
| `experiments/E01_multiscale_buffer/data/ny_cells_r{100..500}.csv` | 4,155 / 14,374 / 26,375 / 37,617 / 47,147 × 46 | 纽约 100 m 格网级数据集：因变量为缓冲区内全部犯罪事件计数（含逐年列 `y_YYYY`），自变量为 19 个环境特征 |
| `experiments/E01_multiscale_buffer/data/hk_cells_r{100..500}.csv` | 4,431 / 10,516 / 15,564 / 20,263 / 24,743 × 30 | 香港 100 m 格网级数据集：因变量为交通事故计数，自变量为 17 个环境特征 |
| `experiments/E01_multiscale_buffer/data/{ny,hk}_svi_r{r}.csv` | 学校级 | 街景指标按学校与半径聚合（影像级比例→全景→缓冲均值） |
| `experiments/E01_multiscale_buffer/data/{ny,hk}_events_r{r}.csv` | 学校级 | 学校在各半径内的事件计数（含按年与按罪名分解列） |
| `experiments/E01_multiscale_buffer/data/{ny,hk}_raster_r{r}.csv` | 学校级 | 连续栅格（密度核、路网、人口）的缓冲均值 |
| `experiments/E13_split_categories/data/ny_cells_drug_alcohol_r{100..500}.csv` | 同 E01，纽约 | 因变量换为“毒品与酒精相关违法”计数 |
| `experiments/E13_split_categories/data/ny_cells_split_r300.csv` | 26,375 × 28 | 纽约 300 m 格网级拆分数据集（`y_drug_alcohol`、`y_traffic`） |
| `experiments/E13_split_categories/data/ny_cells_property_r300.csv` | 26,375 × 28 | 财产犯罪（`y_property`）格网计数 |
| `experiments/E13_split_categories/data/ny_cells_violent_r300.csv` | 26,375 × 28 | 暴力犯罪（`y_violent`）格网计数 |
| `experiments/E13_split_categories/data/ny_cells_drug_alcohol_year_r300.csv` | 26,375 × 46 | 毒品与酒精类 + 逐年计数（`count_2006`—`count_2024`），用于时间窗验证 |

## 2. 结果表

| 路径 | 内容 |
| --- | --- |
| `experiments/E01_multiscale_buffer/results/multiscale_summary.csv` | 两城 × 五尺度的格网数、零值比例、随机/空间分块/时间窗 AUC |
| `.../results/algo_scale_table.csv` | 三算法 × 五尺度完整指标（含 PR-AUC、Brier、top-k） |
| `.../results/ablation_scale_table.csv` | 七组消融 × 两城 × 五尺度 + 配对 bootstrap |
| `.../results/count_model_comparison.csv` | Hurdle 与 Poisson/NB/ZIP/ZINB/单阶段树比较 |
| `.../results/exposure_second_stage.csv` | 计数与事件率目标的第二阶段 R²/MAE |
| `.../results/diagnostics_scale_table.csv` | 残差 Moran's I、top-k 命中率、SHAP 跨折稳定性 |
| `.../results/figures/*.csv`、`*.png` | 校准曲线与 PR 曲线的数据点与图件 |
| `experiments/E13_split_categories/results/split_targets_r300.csv` | 拆分后两类的完整指标（含空间分块均值） |
| `.../results/drug_alcohol_multiscale.csv`、`..._full_diagnostics.csv`、`..._ablation.csv`、`..._count_models.csv`、`..._exposure.csv` | 毒品与酒精类的多尺度、诊断、消融、计数模型与暴露量结果 |
| `.../results/{drug_alcohol_temporal.csv,drug_alcohol_temporal_bootstrap.csv}` | 时间窗切分与配对 bootstrap |
| `.../results/e13_格网构建bug修正记录.md`、`e13_fix_summary.json`、`e13_fix_verification.csv` | 格网构建 bug 的修正记录与逐格网核对结果 |
| `experiments/E11_scenario_simulation/results/scenario_summary.csv` | 情景模拟主结果（两城 × 情景 × 方法 × 逐算法） |
| `.../results/scenario_results_raw.csv` | 15 个模型实现的逐次结果 |
| `.../results/figures/fig_scenario_effects.png`、`fig_scenario_main.png` | 情景效应图（三面板 / 正文两面板） |

## 3. 逐文件清单（自动生成）

| 文件 | 行数 | 列数 | 前若干列 |
| --- | --- | --- | --- |
| `experiments/E01_multiscale_buffer/data/hk_cells_r100.csv` | 4431 | 37 | school_id, cell_x, cell_y, dist_to_school, school_lon, school_lat, event_count, y_2014... |
| `experiments/E01_multiscale_buffer/data/hk_cells_r200.csv` | 10516 | 37 | school_id, cell_x, cell_y, dist_to_school, school_lon, school_lat, event_count, y_2014... |
| `experiments/E01_multiscale_buffer/data/hk_cells_r300.csv` | 15564 | 30 | school_id, cell_x, cell_y, dist_to_school, school_lon, school_lat, event_count, y_2014... |
| `experiments/E01_multiscale_buffer/data/hk_cells_r400.csv` | 20263 | 37 | school_id, cell_x, cell_y, dist_to_school, school_lon, school_lat, event_count, y_2014... |
| `experiments/E01_multiscale_buffer/data/hk_cells_r500.csv` | 24743 | 37 | school_id, cell_x, cell_y, dist_to_school, school_lon, school_lat, event_count, y_2014... |
| `experiments/E01_multiscale_buffer/data/hk_events_r300.csv` | 3565 | 10 | school_id, school_lon, school_lat, event_count_r300, count_2014_r300, count_2015_r300, count_2016_r300, count_2017_r300... |
| `experiments/E01_multiscale_buffer/data/hk_raster_r300.csv` | 3565 | 11 | school_id, school_lon, school_lat, busStation_density_r300, crossing_density_r300, shop_density_r300, street_lamp_density_r300, traffic_signals_density_r300... |
| `experiments/E01_multiscale_buffer/data/hk_svi_r100.csv` | 3565 | 27 | school_id, school_lon, school_lat, ratio_Enclosure_degree_r100, ratio_Greening_degree_r100, ratio_Openness_r100, ratio_Pedestrian_density_r100, ratio_Protection_r100... |
| `experiments/E01_multiscale_buffer/data/hk_svi_r200.csv` | 3565 | 27 | school_id, school_lon, school_lat, ratio_Enclosure_degree_r200, ratio_Greening_degree_r200, ratio_Openness_r200, ratio_Pedestrian_density_r200, ratio_Protection_r200... |
| `experiments/E01_multiscale_buffer/data/hk_svi_r300.csv` | 3565 | 12 | school_id, school_lon, school_lat, ratio_Enclosure_degree_r300, ratio_Greening_degree_r300, ratio_Openness_r300, ratio_Pedestrian_density_r300, ratio_Protection_r300... |
| `experiments/E01_multiscale_buffer/data/hk_svi_r400.csv` | 3565 | 27 | school_id, school_lon, school_lat, ratio_Enclosure_degree_r400, ratio_Greening_degree_r400, ratio_Openness_r400, ratio_Pedestrian_density_r400, ratio_Protection_r400... |
| `experiments/E01_multiscale_buffer/data/hk_svi_r500.csv` | 3565 | 27 | school_id, school_lon, school_lat, ratio_Enclosure_degree_r500, ratio_Greening_degree_r500, ratio_Openness_r500, ratio_Pedestrian_density_r500, ratio_Protection_r500... |
| `experiments/E01_multiscale_buffer/data/ny_cells_r100.csv` | 4155 | 65 | school_id, cell_x, cell_y, dist_to_school, school_lon, school_lat, event_count, y_2006... |
| `experiments/E01_multiscale_buffer/data/ny_cells_r200.csv` | 14374 | 65 | school_id, cell_x, cell_y, dist_to_school, school_lon, school_lat, event_count, y_2006... |
| `experiments/E01_multiscale_buffer/data/ny_cells_r300.csv` | 26375 | 45 | school_id, cell_x, cell_y, dist_to_school, school_lon, school_lat, event_count, y_2006... |
| `experiments/E01_multiscale_buffer/data/ny_cells_r400.csv` | 37617 | 65 | school_id, cell_x, cell_y, dist_to_school, school_lon, school_lat, event_count, y_2006... |
| `experiments/E01_multiscale_buffer/data/ny_cells_r500.csv` | 47147 | 65 | school_id, cell_x, cell_y, dist_to_school, school_lon, school_lat, event_count, y_2006... |
| `experiments/E01_multiscale_buffer/data/ny_events_r300.csv` | 1950 | 23 | school_id, school_lon, school_lat, event_count_r300, count_2006_r300, count_2007_r300, count_2008_r300, count_2009_r300... |
| `experiments/E01_multiscale_buffer/data/ny_raster_r300.csv` | 1950 | 13 | school_id, school_lon, school_lat, busStation_density_r300, crossing_density_r300, shop_density_r300, street_lamp_density_r300, traffic_signals_density_r300... |
| `experiments/E01_multiscale_buffer/data/ny_svi_r100.csv` | 1950 | 42 | school_id, school_lon, school_lat, ratio_Enclosure_degree_r100, ratio_Greening_degree_r100, ratio_Openness_r100, ratio_Pedestrian_density_r100, ratio_Protection_r100... |
| `experiments/E01_multiscale_buffer/data/ny_svi_r200.csv` | 1950 | 42 | school_id, school_lon, school_lat, ratio_Enclosure_degree_r200, ratio_Greening_degree_r200, ratio_Openness_r200, ratio_Pedestrian_density_r200, ratio_Protection_r200... |
| `experiments/E01_multiscale_buffer/data/ny_svi_r300.csv` | 1950 | 12 | school_id, school_lon, school_lat, ratio_Enclosure_degree_r300, ratio_Greening_degree_r300, ratio_Openness_r300, ratio_Pedestrian_density_r300, ratio_Protection_r300... |
| `experiments/E01_multiscale_buffer/data/ny_svi_r400.csv` | 1950 | 42 | school_id, school_lon, school_lat, ratio_Enclosure_degree_r400, ratio_Greening_degree_r400, ratio_Openness_r400, ratio_Pedestrian_density_r400, ratio_Protection_r400... |
| `experiments/E01_multiscale_buffer/data/ny_svi_r500.csv` | 1950 | 42 | school_id, school_lon, school_lat, ratio_Enclosure_degree_r500, ratio_Greening_degree_r500, ratio_Openness_r500, ratio_Pedestrian_density_r500, ratio_Protection_r500... |
| `experiments/E01_multiscale_buffer/results/ablation_scale_table.csv` | 80 | 11 | AUC, PR_AUC, Recall, n_test, R2_pos, MAE_pos, city, radius... |
| `experiments/E01_multiscale_buffer/results/algo_scale_table.csv` | 60 | 12 | AUC, PR_AUC, Recall, Brier, top1_hit, top5_hit, top10_hit, n_test... |
| `experiments/E01_multiscale_buffer/results/count_model_comparison.csv` | 60 | 8 | model, MAE, RMSE, Poisson_deviance, city, radius, n_train, n_test |
| `experiments/E01_multiscale_buffer/results/curve_files.csv` | 10 | 3 | city, radius, figure |
| `experiments/E01_multiscale_buffer/results/diagnostics_scale_table.csv` | 10 | 12 | city, radius, zero_ratio, morans_I_resid, morans_p, top1_hit, top5_hit, top10_hit... |
| `experiments/E01_multiscale_buffer/results/exposure_second_stage.csv` | 10 | 6 | city, radius, count_R2, count_MAE, rate_R2, rate_MAE |
| `experiments/E01_multiscale_buffer/results/figures/hk_calibration_r100_full.csv` | 10 | 2 | mean_predicted, fraction_positive |
| `experiments/E01_multiscale_buffer/results/figures/hk_calibration_r200_full.csv` | 10 | 2 | mean_predicted, fraction_positive |
| `experiments/E01_multiscale_buffer/results/figures/hk_calibration_r300_full.csv` | 10 | 2 | mean_predicted, fraction_positive |
| `experiments/E01_multiscale_buffer/results/figures/hk_calibration_r400_full.csv` | 10 | 2 | mean_predicted, fraction_positive |
| `experiments/E01_multiscale_buffer/results/figures/hk_calibration_r500_full.csv` | 10 | 2 | mean_predicted, fraction_positive |
| `experiments/E01_multiscale_buffer/results/figures/hk_pr_r100_full.csv` | 862 | 2 | recall, precision |
| `experiments/E01_multiscale_buffer/results/figures/hk_pr_r200_full.csv` | 1926 | 2 | recall, precision |
| `experiments/E01_multiscale_buffer/results/figures/hk_pr_r300_full.csv` | 2694 | 2 | recall, precision |
| `experiments/E01_multiscale_buffer/results/figures/hk_pr_r400_full.csv` | 3318 | 2 | recall, precision |
| `experiments/E01_multiscale_buffer/results/figures/hk_pr_r500_full.csv` | 3839 | 2 | recall, precision |
| `experiments/E01_multiscale_buffer/results/figures/ny_calibration_r100_full.csv` | 10 | 2 | mean_predicted, fraction_positive |
| `experiments/E01_multiscale_buffer/results/figures/ny_calibration_r200_full.csv` | 10 | 2 | mean_predicted, fraction_positive |
| `experiments/E01_multiscale_buffer/results/figures/ny_calibration_r300_drug_alcohol.csv` | 10 | 2 | mean_predicted, fraction_positive |
| `experiments/E01_multiscale_buffer/results/figures/ny_calibration_r300_full.csv` | 10 | 2 | mean_predicted, fraction_positive |
| `experiments/E01_multiscale_buffer/results/figures/ny_calibration_r400_full.csv` | 10 | 2 | mean_predicted, fraction_positive |
| `experiments/E01_multiscale_buffer/results/figures/ny_calibration_r500_full.csv` | 10 | 2 | mean_predicted, fraction_positive |
| `experiments/E01_multiscale_buffer/results/figures/ny_pr_r100_full.csv` | 792 | 2 | recall, precision |
| `experiments/E01_multiscale_buffer/results/figures/ny_pr_r200_full.csv` | 2655 | 2 | recall, precision |
| `experiments/E01_multiscale_buffer/results/figures/ny_pr_r300_drug_alcohol.csv` | 1326 | 2 | recall, precision |
| `experiments/E01_multiscale_buffer/results/figures/ny_pr_r300_full.csv` | 4789 | 2 | recall, precision |
| `experiments/E01_multiscale_buffer/results/figures/ny_pr_r400_full.csv` | 6442 | 2 | recall, precision |
| `experiments/E01_multiscale_buffer/results/figures/ny_pr_r500_full.csv` | 7402 | 2 | recall, precision |
| `experiments/E01_multiscale_buffer/results/hk_cell_model_r100.csv` | 1 | 11 | AUC, Recall, R2, MAE, n_samples, n_positive, zero_ratio, city... |
| `experiments/E01_multiscale_buffer/results/hk_cell_model_r200.csv` | 1 | 11 | AUC, Recall, R2, MAE, n_samples, n_positive, zero_ratio, city... |
| `experiments/E01_multiscale_buffer/results/hk_cell_model_r300.csv` | 1 | 11 | AUC, Recall, R2, MAE, n_samples, n_positive, zero_ratio, city... |
| `experiments/E01_multiscale_buffer/results/hk_cell_model_r400.csv` | 1 | 11 | AUC, Recall, R2, MAE, n_samples, n_positive, zero_ratio, city... |
| `experiments/E01_multiscale_buffer/results/hk_cell_model_r500.csv` | 1 | 11 | AUC, Recall, R2, MAE, n_samples, n_positive, zero_ratio, city... |
| `experiments/E01_multiscale_buffer/results/hk_robustness_r100.csv` | 7 | 15 | n, n_pos, zero_ratio, AUC, Recall, PR_AUC, Brier, top5_hit... |
| `experiments/E01_multiscale_buffer/results/hk_robustness_r200.csv` | 7 | 15 | n, n_pos, zero_ratio, AUC, Recall, PR_AUC, Brier, top5_hit... |
| `experiments/E01_multiscale_buffer/results/hk_robustness_r300.csv` | 9 | 13 | n, n_pos, zero_ratio, AUC, Recall, PR_AUC, Brier, top5_hit... |
| `experiments/E01_multiscale_buffer/results/hk_robustness_r400.csv` | 7 | 15 | n, n_pos, zero_ratio, AUC, Recall, PR_AUC, Brier, top5_hit... |
| `experiments/E01_multiscale_buffer/results/hk_robustness_r500.csv` | 7 | 15 | n, n_pos, zero_ratio, AUC, Recall, PR_AUC, Brier, top5_hit... |
| `experiments/E01_multiscale_buffer/results/hk_vif_r100.csv` | 23 | 2 | variable, VIF |
| `experiments/E01_multiscale_buffer/results/hk_vif_r200.csv` | 23 | 2 | variable, VIF |
| `experiments/E01_multiscale_buffer/results/hk_vif_r300.csv` | 17 | 2 | variable, VIF |
| `experiments/E01_multiscale_buffer/results/hk_vif_r400.csv` | 23 | 2 | variable, VIF |
| `experiments/E01_multiscale_buffer/results/hk_vif_r500.csv` | 23 | 2 | variable, VIF |
| `experiments/E01_multiscale_buffer/results/multiscale_summary.csv` | 10 | 7 | city, radius, cells, zero_ratio, random_AUC, spatial_AUC, temporal_AUC |
| `experiments/E01_multiscale_buffer/results/ny_cell_model_r100.csv` | 1 | 11 | AUC, Recall, R2, MAE, n_samples, n_positive, zero_ratio, city... |
| `experiments/E01_multiscale_buffer/results/ny_cell_model_r200.csv` | 1 | 11 | AUC, Recall, R2, MAE, n_samples, n_positive, zero_ratio, city... |
| `experiments/E01_multiscale_buffer/results/ny_cell_model_r300.csv` | 1 | 11 | AUC, Recall, R2, MAE, n_samples, n_positive, zero_ratio, city... |
| `experiments/E01_multiscale_buffer/results/ny_cell_model_r400.csv` | 1 | 11 | AUC, Recall, R2, MAE, n_samples, n_positive, zero_ratio, city... |
| `experiments/E01_multiscale_buffer/results/ny_cell_model_r500.csv` | 1 | 11 | AUC, Recall, R2, MAE, n_samples, n_positive, zero_ratio, city... |
| `experiments/E01_multiscale_buffer/results/ny_model_r300.csv` | 1 | 11 | AUC, Recall, R2, MAE, n_samples, n_positive, zero_ratio, city... |
| `experiments/E01_multiscale_buffer/results/ny_robustness_r100.csv` | 7 | 15 | n, n_pos, zero_ratio, AUC, Recall, PR_AUC, Brier, top5_hit... |
| `experiments/E01_multiscale_buffer/results/ny_robustness_r200.csv` | 7 | 15 | n, n_pos, zero_ratio, AUC, Recall, PR_AUC, Brier, top5_hit... |
| `experiments/E01_multiscale_buffer/results/ny_robustness_r300.csv` | 9 | 13 | n, n_pos, zero_ratio, AUC, Recall, PR_AUC, Brier, top5_hit... |
| `experiments/E01_multiscale_buffer/results/ny_robustness_r400.csv` | 7 | 15 | n, n_pos, zero_ratio, AUC, Recall, PR_AUC, Brier, top5_hit... |
| `experiments/E01_multiscale_buffer/results/ny_robustness_r500.csv` | 7 | 15 | n, n_pos, zero_ratio, AUC, Recall, PR_AUC, Brier, top5_hit... |
| `experiments/E01_multiscale_buffer/results/ny_vif_r100.csv` | 38 | 2 | variable, VIF |
| `experiments/E01_multiscale_buffer/results/ny_vif_r200.csv` | 38 | 2 | variable, VIF |
| `experiments/E01_multiscale_buffer/results/ny_vif_r300.csv` | 19 | 2 | variable, VIF |
| `experiments/E01_multiscale_buffer/results/ny_vif_r400.csv` | 38 | 2 | variable, VIF |
| `experiments/E01_multiscale_buffer/results/ny_vif_r500.csv` | 38 | 2 | variable, VIF |
| `experiments/E11_scenario_simulation/results/ny_cells_property_r300.csv` | 26375 | 26 | school_id, cell_x, cell_y, dist_to_school, y_property, school_lon, school_lat, ratio_Enclosure_degree_r300... |
| `experiments/E11_scenario_simulation/results/ny_cells_violent_r300.csv` | 26375 | 26 | school_id, cell_x, cell_y, dist_to_school, y_violent, school_lon, school_lat, ratio_Enclosure_degree_r300... |
| `experiments/E11_scenario_simulation/results/scenario_results_raw.csv` | 330 | 16 | city, target, scenario, method, algo, seed, n_test, n_cells_affected... |
| `experiments/E11_scenario_simulation/results/scenario_summary.csv` | 22 | 21 | city, scenario, method, delta_pct, delta_pct_min, delta_pct_max, share_cells_reduced, delta_pct_extensive... |
| `experiments/E13_split_categories/data/ny_cells_drug_alcohol_r100.csv` | 4155 | 56 | school_id, cell_x, cell_y, dist_to_school, school_lon, school_lat, y_drug_alcohol, y_traffic... |
| `experiments/E13_split_categories/data/ny_cells_drug_alcohol_r200.csv` | 14374 | 56 | school_id, cell_x, cell_y, dist_to_school, school_lon, school_lat, y_drug_alcohol, y_traffic... |
| `experiments/E13_split_categories/data/ny_cells_drug_alcohol_r300.csv` | 26375 | 27 | school_id, cell_x, cell_y, dist_to_school, school_lon, school_lat, y_drug_alcohol, y_traffic... |
| `experiments/E13_split_categories/data/ny_cells_drug_alcohol_r400.csv` | 37617 | 56 | school_id, cell_x, cell_y, dist_to_school, school_lon, school_lat, y_drug_alcohol, y_traffic... |
| `experiments/E13_split_categories/data/ny_cells_drug_alcohol_r500.csv` | 47147 | 56 | school_id, cell_x, cell_y, dist_to_school, school_lon, school_lat, y_drug_alcohol, y_traffic... |
| `experiments/E13_split_categories/data/ny_cells_drug_alcohol_year_r300.csv` | 26375 | 46 | school_id, cell_x, cell_y, dist_to_school, school_lon, school_lat, y_drug_alcohol, y_traffic... |
| `experiments/E13_split_categories/data/ny_cells_split_r300.csv` | 26375 | 27 | school_id, cell_x, cell_y, dist_to_school, school_lon, school_lat, y_drug_alcohol, y_traffic... |
| `experiments/E13_split_categories/results/drug_alcohol_ablation.csv` | 5 | 8 | AUC, PR_AUC, Recall, n_test, R2_pos, MAE_pos, group, n_features |
| `experiments/E13_split_categories/results/drug_alcohol_count_models.csv` | 6 | 8 | model, MAE, RMSE, Poisson_deviance, city, radius, n_train, n_test |
| `experiments/E13_split_categories/results/drug_alcohol_diagnostics.csv` | 5 | 8 | radius, AUC_spatial_mean, morans_I_resid, morans_p, shap_spearman_mean, shap_folds, zero_ratio, cells |
| `experiments/E13_split_categories/results/drug_alcohol_exposure.csv` | 2 | 3 | target, R2, MAE |
| `experiments/E13_split_categories/results/drug_alcohol_full_diagnostics.csv` | 5 | 10 | radius, cells, zero_ratio, AUC, PR_AUC, AUC_spatial_mean, morans_I_resid, morans_p... |
| `experiments/E13_split_categories/results/drug_alcohol_multiscale.csv` | 5 | 11 | target, cells, zero_ratio, pos_rate, AUC, PR_AUC, Recall, R2_pos... |
| `experiments/E13_split_categories/results/drug_alcohol_robustness.csv` | 5 | 13 | n, n_pos, zero_ratio, AUC, Recall, PR_AUC, Brier, top5_hit... |
| `experiments/E13_split_categories/results/drug_alcohol_temporal.csv` | 2 | 4 | scheme, AUC, PR_AUC, Recall |
| `experiments/E13_split_categories/results/drug_alcohol_temporal_bootstrap.csv` | 2 | 7 | scheme, scope, AUC_full, AUC_history_only, delta, bootstrap_p, n_eval |
| `experiments/E13_split_categories/results/e13_fix_verification.csv` | 6 | 2 | name, value |
| `experiments/E13_split_categories/results/split_targets_r300.csv` | 2 | 10 | target, cells, zero_ratio, pos_rate, AUC, PR_AUC, Recall, R2_pos... |
| `experiments/E13_split_categories/results/split_targets_r300_full.csv` | 2 | 14 | AUC, PR_AUC, Recall, n_test, R2_pos, MAE_pos, target, label... |
| `experiments/E13_split_categories/results/split_targets_r300_withcoords.csv` | 2 | 10 | target, cells, zero_ratio, pos_rate, AUC, PR_AUC, Recall, R2_pos... |
