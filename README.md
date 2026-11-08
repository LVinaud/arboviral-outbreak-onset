# Outbreak Onset and Outbreak Continuation Are Not the Same Prediction Problem

Code and data for the paper *Outbreak Onset and Outbreak Continuation Are Not the
Same Prediction Problem: A Public-Data Benchmark for Four Mosquito-Borne Diseases
in 645 Municipalities*, Machine Learning for Health (ML4H) 2026, Proceedings of
Machine Learning Research 346.

Lázaro Pereira Vinaud Neto, Marcia Regina Martins Martinez Corso, Luisa Paseto,
Marina Carvalho Arruda Barreto and André C. P. L. F. de Carvalho, Instituto de
Ciências Matemáticas e de Computação (ICMC), Universidade de São Paulo.

Monthly prediction of arbovirus outbreaks for the 645 municipalities of São
Paulo state, built from sixteen public data sources, and evaluated separately on
the two halves of the task that the usual pooled metric merges: outbreaks that
**start** in a calm municipality (onset) and outbreaks that **continue**. Each
forecast is also scored with the data available on the date it would be issued.

The version of the code that produced the camera-ready paper is the tag
`v1.0-camera-ready`.

## The six notebooks, in order

Each runs top to bottom and rebuilds everything downstream of it.

| Notebook | What it does | Reads | Writes | Time |
|---|---|---|---|---|
| `01_data_collection` | downloads the sixteen public sources | network | `data/raw/<date>/` | ~1 h, ~5 GB |
| `02_master` | builds the municipality-month table and the sixteen outbreak labels | `data/raw/`, `data/lookup/` | `data/master/` | ~1 h |
| `03_train` | builds 125 features, splits in time, trains four models and three baselines for 4 diseases x 4 definitions x 6 horizons | `data/master/` | `data/train/` | ~1 to 2 h |
| `04_results` | the tables and figures of the original evaluation | `data/train/`, `data/master/` | `data/train/tables/`, `figuras/` | ~25 min |
| `05_revision_analyses` | the analyses added in the review: evaluation by issue date, onset and continuation at every horizon, alert budgets, 2025 as a fourth test year, a model for onsets only, thresholds from past years, hyperparameter search, calibration | `data/train/`, `data/master/` | `data/train/revision/` | ~1.5 h |
| `06_paper_outputs` | every number, table and new figure of the paper | `data/train/tables/`, `data/train/revision/`, `data/master/` | `paper/numbers.tex`, `paper/tables/`, `figuras/` | <1 min |

Times are for a four-core laptop. `05` calls the scripts in `src/revision/`,
which can also be run on their own; `06` calls `src/paper/paper_outputs.py`.

## Data

**`data/master/` is in the repository**, so the pipeline can start at `03`
without downloading anything. It holds the municipality-month table
(`municipio_mes.parquet`: 89,010 rows, 645 municipalities x 138 months from
January 2015 to June 2026), the sixteen labels (`labels.parquet`), the per-source
tables `02` assembles them from, and `notification_delay.csv` (Section 2 of the
paper).

**The raw downloads used for the paper (collected on 9 September 2026) are at
Zenodo**, DOI: *to be added on publication of the record*. The government portals
revise past files, so a collection run today gives a slightly different table;
the archive is what lets `02` rebuild `data/master/` exactly. Extract it into
`data/raw/` (instructions in the record).

`data/lookup/` holds three small tables that cannot be downloaded
programmatically: the weather-station mapping used by `01`, and the human
development and inequality indices, which are published as a report.

## Setup

```bash
python3.12 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

`requirements.txt` pins the versions the paper was produced with.
`01_data_collection` also needs a Chrome or Chromium binary for the portals that
only serve their data through a browser.

## Reproducing the paper

```bash
cd notebooks
for nb in 03_train 04_results 05_revision_analyses 06_paper_outputs; do
  jupyter nbconvert --to notebook --execute --inplace --ExecutePreprocessor.timeout=-1 $nb.ipynb
done
cd ../paper && pdflatex main && bibtex main && pdflatex main && pdflatex main
```

The LaTeX source in `paper/` reads every number from `paper/numbers.tex`, every
table from `paper/tables/` and every data figure from `figuras/`, all written by
the notebooks. Nothing in the PDF is typed by hand.

**The check script** does all of this in a clean folder and compares the result
with what is committed:

```bash
scripts/verificar_camera_ready.sh v1.0-camera-ready /path/to/empty/folder
# also rebuild data/master from the Zenodo archive:
ARBOVIRAL_RAW=/path/to/data/raw/2026-09-09 scripts/verificar_camera_ready.sh v1.0-camera-ready
```

It copies the tagged commit, creates a new virtualenv, runs the notebooks, and
compares `paper/numbers.tex`, `paper/tables/`, `paper/abstract_openreview.txt` and
every file in `figuras/` byte for byte. It then compiles the PDF, lists the LaTeX
warnings, and lists every numeric literal left in the LaTeX source
(`scripts/lint_numeros.py`), which should only be design parameters, years and
numbers quoted from other papers.

**Seeds.** Every model is fitted with `random_state=42`. The bootstrap over
municipalities, the random hyperparameter search and the tie-breaking in the alert
budgets use `20261012`; the SHAP sample uses `0`. The folds are deterministic, and
the figures are written with a fixed `SOURCE_DATE_EPOCH`, so a rerun gives the
same bytes.

## Where each table and figure comes from

| In the paper | File | Written by (from) |
|---|---|---|
| Table 1, pooled performance | `paper/tables/tab_global.tex` | `06` (from `04`) |
| Table 2, onset and continuation, original reference | `paper/tables/tab_onset.tex` | `06` (from `04`) |
| Table 3, onset and continuation by issue date, h = 1 to 6 | `paper/tables/tab_realtime.tex` | `06` (from `05`, C1) |
| Table 4, the 2025 test year | `paper/tables/tab_2025.tex` | `06` (from `05`, B1) |
| Figure 1, timeline of a forecast | `figuras/timeline.pdf` | `06` |
| Figure 2, alerts raised against onsets caught | `figuras/alert_tradeoff.pdf` | `06` (from `05`, A6) |
| Appendix tables | `paper/tables/tab_*.tex` | `06` (from `04` and `05`) |
| Appendix figures: feature families, kappa, original split, alert budget over all municipalities, season and size, stability, horizon decay, horizon by disease, ROC and PR, threshold curves | `figuras/*.pdf` | `04` |
| Appendix figure: calibration before and after | `figuras/calibration_isotonic.pdf` | `06` (from `05`, C2) |
| Appendix figures: interface screens | `paper/figures/*.png` | screenshots of the application |

## How the notebooks check themselves

`03` runs eight leakage checks on every fit and stops on failure, including a
guard on the number of features. `04` re-executes the feature cells of `03` and
refuses to produce a figure unless the refitted model reproduces what `03` wrote.
`05` checks that its weighted metrics match scikit-learn, that retraining
reproduces the predictions of `03`, and that its recomputation of Tables 1 and 2
matches the tables of `04`. `06` asserts every qualitative statement the paper
makes about the numbers, and that every number the LaTeX source uses is defined.

## What is not here

The raw downloads (at Zenodo), the training output (`data/train/`, regenerated by
`03`), and the web application described in the paper, which is a separate
codebase and is not needed to reproduce any number.

## Licence

MIT, see [LICENSE](LICENSE). The underlying data are public and remain governed
by the terms of their publishers.
