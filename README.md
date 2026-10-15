# Code and data for the TGIS manuscript

Micro-scale environmental correlates of school-area crime and traffic incidents:
street-view evidence from New York and Hong Kong

## 1. Repository contents

| Path | Contents |
| --- | --- |
| `code/` | All analysis code: preprocessing, feature construction, two-stage hurdle modelling and robustness analysis |
| `experiments/` | Derived datasets and result tables used in the paper (E01 multi-scale, E11 scenario simulation, E13 split dependent variables) |
| `DATA_DICTIONARY.md` | Data dictionary: core datasets, result tables and a per-file inventory |
| `data/` | Raw inputs, not distributed because of licence and size restrictions |
| `requirements.txt` | Pinned dependency versions |

The repository is about 180 MB across 165 files and the largest single file is about 21 MB, so a
plain `git push` is sufficient and Git LFS is not required. The raw inputs (about 130 GB) are not
distributed with the repository.

## 2. Environment

Python 3.11 with the dependency versions pinned in `requirements.txt`. The original analysis ran in
the conda environment `geoKD_final`.

## 3. Code structure

```
code/
  config/settings.py       paths and parameters; the project root defaults to the repository root
                           and can be overridden with the SCHOOLSAFETY_ROOT environment variable
  01_preprocess/           event classification, school spatial processing, POI and population
                           rasterisation (original notebooks, outputs stripped)
  02_features/             street-view aggregation, event counts, raster statistics, grid datasets,
                           robustness suite, diagnostics and supplementary analyses;
                           assemble_summary.py builds the 100-500 m multiscale_summary.csv
  03_modeling/             two-stage hurdle models for each buffer radius
  analysis/                OFNS split datasets and split-category suite, class-based split,
                           temporal-window split, intervention scenario simulation
```

## 4. Raw data and access

The repository contains the code, the derived datasets and the result tables only. The raw inputs
are not distributed because of licence and size restrictions:

| Data | Source and access |
| --- | --- |
| New York arrest records (2006-2024) | NYPD Arrest Data (Historic), published on NYC Open Data |
| Hong Kong traffic accidents (2014-2019) | Transport Department of the Hong Kong SAR; redistribution is restricted, so the repository provides counts aggregated to 100 m grid cells only |
| Street-view imagery | Google Street View API (New York) and Tencent Map Street View API (Hong Kong), subject to their terms of service |
| POI and road network | OpenStreetMap (July 2019 snapshot, ODbL) |
| Population rasters | LandScan USA 2021 day/night rasters (New York); a matching 10 m population raster for Hong Kong |

`code/config/settings.py` resolves every input relative to the project root. Place the files as
listed below, or point `SCHOOLSAFETY_ROOT` at a project root that already contains them:

| Variable | File | Key in `settings.py` |
| --- | --- | --- |
| School locations | `school_NY.csv`, `school_HK.csv` | `schools` |
| New York events | `{year}_school_crime_class.csv` (2006-2024) | `events_dir`, `events_pattern` |
| Hong Kong events | `hongkong_accidents.csv` (2014-2019) | `events_combined` |
| Street-view points and ratios | `view_all_*.shp`, `sv_elements_ratio.csv` | `svi_views`, `svi_ratios` |
| Continuous rasters | kernel densities of bus stops, crossings, shops, street lamps, traffic signals and speed cameras, plus the road raster (10 m) | `rasters` |
| Population | LandScan USA 2021 day/night rasters | `rasters` |

The notebooks under `code/01_preprocess/` are the original working copies and still contain the
absolute paths used at the time (`E:/chuli/...`, `F:/schoolsafety/...`). To rerun them, replace those
prefixes with local paths:

```powershell
Get-ChildItem code -Recurse -Include *.ipynb | ForEach-Object {
  (Get-Content $_ -Raw) -replace 'F:/schoolsafety/data', 'D:/myrepo/data' | Set-Content $_ -Encoding UTF8
}
```
