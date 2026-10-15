# E13 格网构建 bug 修正记录

## 一、两个 bug

### bug 1　格网级时间窗脚本的特征合并键错误（本次修正的主对象）

`st23/year_and_temporal.py` 中：

```python
feats = pd.read_csv(E13 / "data" / "ny_cells_drug_alcohol_r300.csv")
feats = feats[[c for c in feats.columns if c not in cells.columns or c == "school_id"]]
cells = cells.merge(feats, on="school_id", how="left")     # ← 键不唯一
```

`cells` 是格网表（26375 行），`feats` 也是格网表（26375 行），两者用
**非唯一键 `school_id`** 合并，每所学校内部形成 k×k 的笛卡尔积，
结果膨胀到 **570451 行**，特征与因变量逐行错位，
时间窗 AUC 与配对 bootstrap p 值全部失真。

### bug 2　拆分格网数据集的输出文件名被硬编码

`st18/split_categories.py` 的 `build_cells` 里写死：

```python
cells.to_csv(OUT / "data" / "ny_cells_split_r300.csv", ...)
```

`st19/rerun_drug_alcohol.py` 循环调用它生成 100—500 m 各半径文件时，
每次都会覆盖同一个 `ny_cells_split_r300.csv`，最终留在磁盘上的是
**半径 500 m 的网格（47,147 行）却标为 r300**，且 `y_traffic` 全为 0
（因为 st19 把 `GROUP_B` 置空后重建）。交通类与拆分因变量数据集的磁盘版本因此不可用。

## 二、修正做法

1. 用格网唯一键 `(school_id, cell_x, cell_y)` 合并特征，保证 1:1；
2. 用同一套网格公式从原始逮捕记录重建 r300 网格与逐格网计数，
   并逐格网核对既有 E13 文件；
3. 重建 `ny_cells_split_r300.csv`（正确的 r300 网格）；
4. 时间窗切分改为与 `robustness_suite.run_temporal` 同口径（全样本拟合早期标签、
   全样本预测后期标签），另附 80/20 子集口径作为对照；
5. 重新计算配对 bootstrap。

## 三、修正结果

| 项目 | 修正前 | 修正后 |
| --- | --- | --- |
| 年限表行数 | 570451 | 26375 |
| 网格 | 无法核对 | 26375 个 100 m 格网（与既有 E13 网格逐格网一致） |
| 毒品与酒精类事件 | — | 801629 起 |
| 交通类事件 | y_traffic 全为 0 | 331153 起 |
| 毒品与酒精类 AUC / R² | 0.729 / 0.340 | **0.7291 / 0.3480**（未变） |
| 交通类 AUC | 0.717 | **0.7155**（20 特征全模型口径） |
| 时间窗 AUC（全样本口径） | 0.733（错误） | **0.7391** |
| 仅历史基线 AUC | 0.706（错误） | **0.7031** |
| ΔAUC / bootstrap p | +0.027 / 0.000 | **+0.0360 / 0.000** |
| 时间窗 AUC（80/20 子集口径） | — | **0.7111**（仅历史 0.7054，p=0.210） |

关键结论：**逐格网计数与既有 E13 结果完全一致**（26375 个格网的
`y_drug_alcohol` 无一不同，合计 801629 起），说明主结果
（AUC 0.729、R² 0.340 等）不受 bug 影响；受影响的只有时间窗切分与配对 bootstrap，
现已按新目标重算。
