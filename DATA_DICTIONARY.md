# Data dictionary

All derived datasets and result tables are stored under `experiments/`. Raw inputs (arrest records, street-view image points, rasters) are not distributed with the repository because of licence and size restrictions; see section 4 of `README.md` for the list of required files and how to obtain them.

## 1. Core datasets

| Path | Level | Contents |
| --- | --- | --- |
| `experiments/E01_multiscale_buffer/data/ny_cells_r{100..500}.csv` | 100 m grid | New York grid-level dataset: all crime events within the school buffer as the dependent variable (yearly columns `y_YYYY`), plus 19 environmental features. Grid counts per radius: 4,155 / 14,374 / 26,375 / 37,617 / 47,147. |
| `experiments/E01_multiscale_buffer/data/hk_cells_r{100..500}.csv` | 100 m grid | Hong Kong grid-level dataset: traffic accident counts as the dependent variable, plus 17 environmental features. Grid counts per radius: 4,431 / 10,516 / 15,564 / 20,263 / 24,743. |
| `experiments/E01_multiscale_buffer/data/{ny,hk}_school_features_r{r}.csv` | school | Merged school-level feature table (base table + street-view + events + rasters) written by `run_multiscale_all.py`; canonical name. |
| `experiments/E01_multiscale_buffer/data/{ny,hk}_svi_r{r}.csv` | school | Street-view indicators aggregated per school and radius (image-level ratios to panorama, then buffer mean). For r = 300 this is the pure street-view table; for the other radii the legacy name still holds the merged table (kept for backwards compatibility, prefer `school_features`). |
| `experiments/E01_multiscale_buffer/data/{ny,hk}_events_r{r}.csv` | school | Event counts per school and radius, with yearly and offence-type breakdowns. |
| `experiments/E01_multiscale_buffer/data/{ny,hk}_raster_r{r}.csv` | school | Buffer means of the continuous rasters (kernel densities, road network, population); r = 300 only. |
| `experiments/E13_split_categories/data/ny_cells_drug_alcohol_r{100..500}.csv` | 100 m grid | As the E01 New York grids, but the dependent variable is the count of drugs- and alcohol-related offences; each radius uses the features recomputed at that radius. |
| `experiments/E13_split_categories/data/ny_cells_split_r300.csv` | 100 m grid | New York 300 m split dataset carrying both targets (`y_drug_alcohol`, `y_traffic`). |
| `experiments/E13_split_categories/data/ny_cells_drug_alcohol_year_r300.csv` | 100 m grid | Drugs and alcohol counts plus one column per year, used for the temporal-window validation. |
| `experiments/E11_scenario_simulation/results/ny_cells_property_r300.csv` | 100 m grid | Property-crime grid counts used by the scenario simulation. |
| `experiments/E11_scenario_simulation/results/ny_cells_violent_r300.csv` | 100 m grid | Violent-crime grid counts used by the scenario simulation. |

Exact row and column counts for every file are listed in section 3.

## 2. Result tables

| Path | Contents |
| --- | --- |
| `experiments/E01_multiscale_buffer/results/multiscale_summary.csv` | Grid counts, zero ratios and random / spatially blocked / temporal AUC for both cities across the 100-500 m radii. |
| `experiments/E01_multiscale_buffer/results/algo_scale_table.csv` | Full metrics for three algorithms across five radii (including PR-AUC, Brier score and top-k hit rates). |
| `experiments/E01_multiscale_buffer/results/ablation_scale_table.csv` | Seven ablation groups by city and radius, plus the paired bootstrap comparison of the full model against the history-only baseline. |
| `experiments/E01_multiscale_buffer/results/count_model_comparison.csv` | Two-stage hurdle model compared with Poisson, negative binomial, ZIP, ZINB and single-stage tree models. |
| `experiments/E01_multiscale_buffer/results/exposure_second_stage.csv` | Stage-2 R2 / MAE for count targets and for road-density-adjusted rate targets. |
| `experiments/E01_multiscale_buffer/results/diagnostics_scale_table.csv` | Residual Moran's I, top-k hit rates and cross-fold SHAP rank stability. |
| `experiments/E01_multiscale_buffer/results/figures/*.csv`, `*.png` | Data points and figures for the calibration and precision-recall curves. |
| `experiments/E13_split_categories/results/split_targets_r300.csv` (plus `_withcoords` and `.json`) | Full metrics for the two split targets under the main feature set and under a feature set that also keeps the raw coordinates. |
| `experiments/E13_split_categories/results/drug_alcohol_multiscale.csv`, `..._robustness.csv` | Multi-scale and robustness results for the drugs and alcohol target. |
| `experiments/E13_split_categories/results/drug_alcohol_diagnostics.csv`, `..._full_diagnostics.csv` | Residual Moran's I, hit rates and SHAP stability for the split target. |
| `experiments/E13_split_categories/results/drug_alcohol_ablation.csv`, `..._count_models.csv`, `..._exposure.csv` | Ablation, count-model comparison and exposure adjustment for the split target. |
| `experiments/E13_split_categories/results/drug_alcohol_temporal.csv`, `..._temporal_bootstrap.csv` | Temporal-window split and paired bootstrap for the split target. |
| `experiments/E13_split_categories/results/e13_fix_summary.json`, `e13_fix_verification.csv`, `e13_grid_construction_bug_fix_log.md` | Record of two grid-construction bugs and the cell-by-cell verification after the fix. |
| `experiments/E11_scenario_simulation/results/scenario_summary.csv` | Main scenario results (city x scenario x method, including per-algorithm values and confidence intervals). |
| `experiments/E11_scenario_simulation/results/scenario_results_raw.csv` | The 15 individual model implementations. |
| `experiments/E11_scenario_simulation/results/figures/fig_scenario_main.png`, `fig_scenario_effects.png` | Scenario effect figures (two-panel main figure and three-panel overview). |

Every table above is regenerated by the scripts described in `README.md` section 3.

## 3. File inventory

| File | Rows | Columns | First columns |
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
| `experiments/E13_split_categories/data/ny_cells_drug_alcohol_r100.csv` | 4155 | 27 | school_id, cell_x, cell_y, dist_to_school, school_lon, school_lat, y_drug_alcohol, y_traffic... |
| `experiments/E13_split_categories/data/ny_cells_drug_alcohol_r200.csv` | 14374 | 27 | school_id, cell_x, cell_y, dist_to_school, school_lon, school_lat, y_drug_alcohol, y_traffic... |
| `experiments/E13_split_categories/data/ny_cells_drug_alcohol_r300.csv` | 26375 | 27 | school_id, cell_x, cell_y, dist_to_school, school_lon, school_lat, y_drug_alcohol, y_traffic... |
| `experiments/E13_split_categories/data/ny_cells_drug_alcohol_r400.csv` | 37617 | 27 | school_id, cell_x, cell_y, dist_to_school, school_lon, school_lat, y_drug_alcohol, y_traffic... |
| `experiments/E13_split_categories/data/ny_cells_drug_alcohol_r500.csv` | 47147 | 27 | school_id, cell_x, cell_y, dist_to_school, school_lon, school_lat, y_drug_alcohol, y_traffic... |
| `experiments/E13_split_categories/data/ny_cells_drug_alcohol_year_r300.csv` | 26375 | 46 | school_id, cell_x, cell_y, dist_to_school, school_lon, school_lat, count_2006, count_2007... |
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

### Other artifacts

| File |
| --- |
| `experiments/E01_multiscale_buffer/results/figures/hk_curves_r100_full.png` |
| `experiments/E01_multiscale_buffer/results/figures/hk_curves_r200_full.png` |
| `experiments/E01_multiscale_buffer/results/figures/hk_curves_r300_full.png` |
| `experiments/E01_multiscale_buffer/results/figures/hk_curves_r400_full.png` |
| `experiments/E01_multiscale_buffer/results/figures/hk_curves_r500_full.png` |
| `experiments/E01_multiscale_buffer/results/figures/ny_curves_r100_full.png` |
| `experiments/E01_multiscale_buffer/results/figures/ny_curves_r200_full.png` |
| `experiments/E01_multiscale_buffer/results/figures/ny_curves_r300_drug_alcohol.png` |
| `experiments/E01_multiscale_buffer/results/figures/ny_curves_r300_full.png` |
| `experiments/E01_multiscale_buffer/results/figures/ny_curves_r400_full.png` |
| `experiments/E01_multiscale_buffer/results/figures/ny_curves_r500_full.png` |
| `experiments/E11_scenario_simulation/config.md` |
| `experiments/E11_scenario_simulation/results/figures/fig_scenario_effects.png` |
| `experiments/E11_scenario_simulation/results/figures/fig_scenario_main.png` |
| `experiments/E11_scenario_simulation/results/scenario_manifest.json` |
| `experiments/E11_scenario_simulation/results/scenario_note.md` |
| `experiments/E13_split_categories/results/e13_fix_summary.json` |
| `experiments/E13_split_categories/results/e13_grid_construction_bug_fix_log.md` |
| `experiments/E13_split_categories/results/split_targets_r300.json` |

