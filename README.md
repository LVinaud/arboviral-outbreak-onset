# Outbreak onset and outbreak continuation are not the same prediction problem

Monthly prediction of arbovirus outbreaks for the 645 municipalities of São
Paulo state, built from sixteen public Brazilian data sources, and evaluated
separately on the two halves of the task that the usual pooled metric merges:
outbreaks that **start** and outbreaks that **continue**.

Lázaro Pereira Vinaud Neto, Instituto de Ciências Matemáticas e de Computação,
Universidade de São Paulo. Undergraduate research supervised by André Carlos
Ponce de Leon Ferreira de Carvalho.

## Why the split matters

Most municipality-months labelled as an outbreak are continuations of an
outbreak that was already visible, and for those the current case count already
carries much of the signal. The months that change what a health department can
do are the ones where a calm municipality is about to have an outbreak, because
only there does a warning still leave time to act. Those are a minority of the
positive labels, so they weigh little in a pooled score.

Reported separately, the gap is large: the random forest catches **89.2%** of
continuations and **46.6%** of onsets one month ahead, a 42.6-point difference
the pooled figure hides.

## The four notebooks

Each runs top to bottom and rebuilds everything downstream of it.

| notebook | what it does | needs | writes |
|---|---|---|---|
| `01_data_collection.ipynb` | downloads the sixteen public sources | network | `data/raw/<date>/` |
| `02_master.ipynb` | builds the municipality-month table and the sixteen outbreak labels | `data/raw/`, `data/lookup/` | `data/master/` |
| `03_train.ipynb` | builds 125 features, splits in time, trains six predictors | `data/master/` | `data/train/` |
| `04_results.ipynb` | aggregates into the tables and figures | `data/train/`, `data/master/` | `data/train/tables/`, `figuras/` |

## Starting without re-downloading

`data/master/` is versioned here, so you can skip `01` and `02` and start at
`03`. The two files the training needs are:

- `municipio_mes.parquet` — 89,010 rows (645 municipalities x 138 months,
  2015-01 to 2026-06), 83 columns
- `labels.parquet` — the same grid with 16 outbreak labels, one per disease and
  definition

Collection takes about an hour and roughly 5 GB; those two files are its result.

`data/lookup/` holds three small tables that cannot be downloaded
programmatically: the weather-station mapping used by `01`, and the human
development and inequality indices, which are published as a report rather than
as a machine-readable file.

## Setup

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

Python 3.12. `01_data_collection.ipynb` additionally needs a Chrome or Chromium
binary for the portals that only serve their data through a browser, and
installs its own remaining prerequisites in its second cell.

## Reproducibility

**From `03` onward, exactly.** Every model is fitted with a fixed seed, the
folds are deterministic, and the two parquet files in `data/master/` are the
exact inputs the published results were computed from. Running `03` then `04`
regenerates every table and figure.

**From `01`, no, and that is a property of the data rather than of the code.**
The sixteen sources are live government systems. They publish new months, revise
earlier ones, and move preliminary notifications into consolidated files as
cases are closed. `02` also ends the series at the last month that has had 60
days to consolidate, computed from the date you run it, so the grid itself grows
as time passes. A collection run today produces a table that is larger and
slightly different from the one used here, and the numbers move accordingly.

That is the intended behaviour for a pipeline meant to keep running, and it is
why the assembled table ships with the code: `01` and `02` are there so the
assembly can be inspected and repeated, and the parquet files are there so the
published results can be checked exactly.

## How the notebooks check themselves

`04` re-executes the feature-building cells of `03` rather than restating that
code, and refuses to produce a figure unless the refitted model reproduces the
metrics `03` wrote to disk to four decimal places. If the two ever drift apart,
`04` stops instead of reporting numbers that do not match.

`03` runs eight leakage checks on every fit and stops on failure, including a
guard that the feature matrix has exactly 125 columns. That guard exists because
an earlier version of the pipeline computed rolling windows on a flat series,
which let the opening months of each municipality inherit the tail of the
previous one; for the three-month mean of dengue cases alone, that affected
1,768 rows across 644 of the 645 municipalities.

Training the full grid (4 diseases x 4 definitions x 6 horizons) takes roughly
an hour on a four-core machine. The group-importance section of `04` refits the
forest about forty more times and caches its results as CSV, so it is slow the
first time and immediate afterwards.

## The application

`app/` is a Streamlit application, in Portuguese and English, that reads what
`03` writes: this month's alert queue, a state map, one page per municipality
with the SHAP explanation and a comparison with similar municipalities, the
measured performance of the default models, and an About page. It needs
`data/train/` (run `03` with `RODAR_PRODUCAO = True`) and nothing from `04`.

```bash
pip install -r requirements.txt
streamlit run app/app.py
python -m unittest discover tests      # smoke tests: translations and every page
```

The language follows the browser (Portuguese for Portuguese browsers, English
otherwise) and can be changed in the sidebar or with `?lang=pt` / `?lang=en`.

### Publishing

The public site runs on Streamlit Community Cloud, deployed from this repository
with `app/app.py` as the entry point; it installs `app/requirements.txt` and
`packages.txt` by itself. The training output is not in Git, so the app
downloads each file it needs, the first time it needs it, from a public dataset
repository on Hugging Face (`LVinaud/arboviral-alerta-dados`, see
`app/lib/dados.py`). After a run of the pipeline, update that repository with:

```bash
hf auth login                  # once, with a write token
python deploy/publicar.py      # sends data/ (tables and the offered models)
```

and reboot the app from the Community Cloud dashboard so it reads the new files.
`ARBOVIRAL_HF_REPO` points the app at another repository (empty disables the
download) and `ARBOVIRAL_DADOS` at another local data folder.
`deploy/Dockerfile` builds the same app for any host that runs containers.

## What is not here

The raw downloads (several gigabytes, reproducible by `01`) and the training
output (`data/train/`, regenerated by `03`, and published for the application
as described above).

## Data sources

All sixteen are published by Brazilian federal agencies and none contains
individual-level identifiers: notifiable diseases (SINAN), yellow fever open
data, hospital admissions (SIH-SUS), health network (CNES/SIM), live births
(SINASC), weather (NASA POWER), population and GDP (IBGE), territorial area
(IBGE), commuting (IBGE census), housing (IBGE), land cover (MapBiomas),
sanitation (SINISA), primary care (e-Gestor), municipal capacity (MUNIC), fiscal
and development indices, and yellow fever vaccination coverage.

## Licence

MIT, see [LICENSE](LICENSE). The underlying data are public and remain governed
by the terms of their respective agencies.
