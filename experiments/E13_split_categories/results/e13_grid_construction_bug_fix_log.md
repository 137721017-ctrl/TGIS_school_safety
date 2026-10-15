# E13 grid construction bug fix log

Historical note: the `st*/` scripts referenced below are the one-off working scripts used at the
time of the analysis; they are not part of this repository. The consolidated implementation is
`code/analysis/ofns_split.py` together with `code/analysis/e13_suite.py`.

## 1. The two bugs

### Bug 1 - wrong merge key in the grid-level temporal-window script (the main subject of this fix)

In `st23/year_and_temporal.py`:

```python
feats = pd.read_csv(E13 / "data" / "ny_cells_drug_alcohol_r300.csv")
feats = feats[[c for c in feats.columns if c not in cells.columns or c == "school_id"]]
cells = cells.merge(feats, on="school_id", how="left")     # <- key is not unique
```

Both `cells` and `feats` are grid-level tables with 26,375 rows. Merging them on the
**non-unique key `school_id`** produces a k x k Cartesian product within each school, inflating the
result to **570,451 rows**. Features and the dependent variable were then misaligned row by row, so
the temporal-window AUC and the paired-bootstrap p-values were both invalid.

### Bug 2 - hard-coded output filename in the split grid builder

Inside `build_cells` in `st18/split_categories.py`:

```python
cells.to_csv(OUT / "data" / "ny_cells_split_r300.csv", ...)
```

`st19/rerun_drug_alcohol.py` calls this function in a loop over the 100-500 m radii, so each
iteration overwrote the same `ny_cells_split_r300.csv`. What remained on disk was the **500 m grid
(47,147 rows) labelled as r300**, with `y_traffic` equal to zero everywhere (because st19 had
emptied `GROUP_B` before rebuilding). The on-disk versions of the traffic and split-target datasets
were therefore unusable.

## 2. What was fixed

1. Merge the features on the unique cell key `(school_id, cell_x, cell_y)` to guarantee a 1:1 join.
2. Rebuild the r300 grid and the per-cell counts from the raw arrest records with the same grid
   formula, then verify cell by cell against the existing E13 files.
3. Rebuild `ny_cells_split_r300.csv` with the correct r300 grid.
4. Align the temporal split with `robustness_suite.run_temporal` (fit the early-year labels on all
   cells and predict the late-year labels on all cells), and report the 80/20 subset as a secondary
   specification.
5. Recompute the paired bootstrap.

## 3. Results after the fix

| Item | Before | After |
| --- | --- | --- |
| Rows in the year table | 570,451 | 26,375 |
| Grid | could not be verified | 26,375 100 m cells (cell-by-cell identical to the existing E13 grid) |
| Drugs and alcohol events | - | 801,629 |
| Traffic events | `y_traffic` all zero | 331,153 |
| Drugs and alcohol AUC / R2 | 0.729 / 0.340 | **0.7291 / 0.3480** (unchanged) |
| Traffic AUC | 0.717 | **0.7155** (20-feature full model) |
| Temporal-window AUC (all cells) | 0.733 (incorrect) | **0.7391** |
| History-only baseline AUC | 0.706 (incorrect) | **0.7031** |
| Delta AUC / bootstrap p | +0.027 / 0.000 | **+0.0360 / 0.000** |
| Temporal-window AUC (80/20 subset) | - | **0.7111** (history only 0.7054, p = 0.210) |

Key conclusion: the **per-cell counts are identical to the existing E13 results** (`y_drug_alcohol`
is unchanged for all 26,375 cells, 801,629 events in total), which shows that the main results
(AUC 0.729, R2 0.340 and so on) were not affected by either bug. Only the temporal split and the
paired bootstrap were affected; both have been recomputed against the corrected target.
