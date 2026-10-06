# E13 拆分因变量：毒品与酒精类 / 交通类

论文正文把 NYPD 的 11 个 `OFNS_DESC` 类别合并为"毒品、酒精与交通类违法"。本实验把该合并类别还原成两组，
分别建模，用于识别合并类别内部的异质性（对应增补 S3）。

## 分组定义

定义集中在 `code/config/settings.py` 的 `OFNS_GROUPS`：

| 组 | 中文 | 包含的 `OFNS_DESC` |
| --- | --- | --- |
| `a` | 毒品与酒精类 | DANGEROUS DRUGS、CANNABIS RELATED OFFENSES、ALCOHOLIC BEVERAGE CONTROL LAW、LOITERING FOR DRUG PURPOSES、UNDER THE INFLUENCE, DRUGS |
| `b` | 交通类 | VEHICLE AND TRAFFIC LAWS、MOVING INFRACTIONS、OTHER TRAFFIC INFRACTION、PARKING OFFENSES、INTOXICATED & IMPAIRED DRIVING、INTOXICATED/IMPAIRED DRIVING |

## 运行

```bash
# 一条命令跑完全部步骤（数据集 + 多尺度 + 稳健性 + 诊断 + 消融 + 计数模型 + 暴露量 + 时间窗 + 对比表 + 校准曲线）
python code/analysis/e13_suite.py

# 也可以只跑某几步
python code/analysis/e13_suite.py --steps data,targets
python code/analysis/e13_suite.py --steps temporal

# 只用数据集构建器（可指定半径与特征来源半径）
python code/analysis/ofns_split.py --radii 100,200,300,400,500 --groups a --name drug_alcohol
```

## 口径说明

- **特征随半径重算**：每个半径的街景比例与栅格变量都取自同半径的学校级特征表（`--feature-radius` 可覆盖）。
  早期版本的非基准半径文件混用了 300 m 街景比例与该半径栅格，已在 2026-10 统一；
- 数据集固定携带 `y_drug_alcohol` 与 `y_traffic` 两列，未参与统计的分组填 0；
- 基准尺度 300 m 的结果：毒品与酒精类 801,629 起、交通类 331,153 起；分类 AUC 0.729 / 0.715，
  第二阶段 R² 0.344 / −0.212；
- 多尺度分类 AUC（100→500 m）依次为 0.756、0.740、0.729、0.721、0.735。

## 产出

| 文件 | 内容 |
| --- | --- |
| `data/ny_cells_drug_alcohol_r{100..500}.csv` | 各半径的拆分数据集（毒品与酒精类） |
| `data/ny_cells_split_r300.csv` | 基准尺度两目标数据集 |
| `data/ny_cells_drug_alcohol_year_r300.csv` | 基准尺度按年计数（用于时间窗验证） |
| `results/split_targets_r300.csv`（`_withcoords`、`.json`） | 两类事件的对比表 |
| `results/drug_alcohol_multiscale.csv`、`_robustness.csv` | 多尺度与稳健性 |
| `results/drug_alcohol_diagnostics.csv`、`_full_diagnostics.csv` | 残差 Moran's I、Top-k、SHAP 稳定性 |
| `results/drug_alcohol_ablation.csv`、`_count_models.csv`、`_exposure.csv` | 消融、计数模型比较、暴露量调整 |
| `results/drug_alcohol_temporal.csv`、`_temporal_bootstrap.csv` | 时间窗切分与配对 bootstrap |
| `results/ny_curves_r300_drug_alcohol.png` 等 | 拆分口径的校准与 PR 曲线（写入 E01 的 figures 目录） |
