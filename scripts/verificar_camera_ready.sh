#!/usr/bin/env bash
# Rebuilds every number, table and figure of the camera-ready paper from a clean
# copy of the repository and checks them.
#
#   scripts/verificar_camera_ready.sh [REF] [WORKDIR]
#
#   REF       commit or tag to check (default: HEAD)
#   WORKDIR   empty folder to work in (default: a new temporary folder)
#   ARBOVIRAL_RAW  optional: path to a raw collection folder (data/raw/<date>, as
#                  archived at Zenodo). When set, 02_master and the notification
#                  delay script are rerun too and data/master is compared.
#   PAPER_DIR      optional: path to the LaTeX source of the paper, which is not in
#                  the repository. When set, the numbers.tex, tables and plain-text
#                  abstract written by 06 are compared with the ones there, the PDF
#                  is compiled and its warnings listed, and every numeric literal
#                  left in the LaTeX source is listed for review.
#
# Steps: git archive of REF into WORKDIR/repo; a new virtualenv with
# requirements.txt; notebooks 03, 04, 05 and 06 executed top to bottom (02 too
# with ARBOVIRAL_RAW); then a byte-for-byte comparison of figuras/ against REF,
# and the PAPER_DIR steps above. Takes about four hours on a 4-core laptop.
set -euo pipefail

REF="${1:-HEAD}"
WORK="${2:-$(mktemp -d -t arboviral-check-XXXXXX)}"
SRC="$(git -C "$(dirname "$0")" rev-parse --show-toplevel)"
COMMIT="$(git -C "$SRC" rev-parse "$REF")"
LOG="$WORK/check.log"
mkdir -p "$WORK/repo" "$WORK/committed"
exec > >(tee -a "$LOG") 2>&1

echo "== Checking $REF ($COMMIT) in $WORK"
date

# Clean copy of the commit, plus a pristine copy of the outputs to compare against.
git -C "$SRC" archive "$COMMIT" | tar -x -C "$WORK/repo"
git -C "$SRC" archive "$COMMIT" figuras data/master | tar -x -C "$WORK/committed"
cd "$WORK/repo"
test ! -e data/train || { echo "data/train should not be in the archive"; exit 1; }
test ! -e paper || { echo "paper/ should not be in the archive"; exit 1; }

# The LaTeX source, if given: a pristine copy to compare against, and a copy in the
# repository without the files 06 writes and without any LaTeX build output.
if [[ -n "${PAPER_DIR:-}" ]]; then
  PAPER_DIR="$(cd "$PAPER_DIR" && pwd)"
  test -f "$PAPER_DIR/main.tex" || { echo "PAPER_DIR has no main.tex"; exit 1; }
  cp -r "$PAPER_DIR" "$WORK/committed/paper"
  cp -r "$PAPER_DIR" paper
  rm -rf paper/tables paper/numbers.tex paper/abstract_openreview.txt
  rm -f paper/*.aux paper/*.bbl paper/*.blg paper/*.log paper/*.out paper/*.pdf paper/*.synctex.gz
fi

python3 -m venv "$WORK/venv"
"$WORK/venv/bin/pip" install --quiet --upgrade pip
"$WORK/venv/bin/pip" install --quiet -r requirements.txt
JUP="$WORK/venv/bin/jupyter"
PY="$WORK/venv/bin/python"

run_nb() {
  local t0=$SECONDS
  echo "-- running $1"
  (cd notebooks && "$JUP" nbconvert --to notebook --execute --inplace \
      --ExecutePreprocessor.timeout=-1 "$1")
  echo "   $1 done in $(( (SECONDS - t0) / 60 )) min"
}

if [[ -n "${ARBOVIRAL_RAW:-}" ]]; then
  mkdir -p data/raw
  ln -s "$(cd "$ARBOVIRAL_RAW" && pwd)" "data/raw/$(basename "$ARBOVIRAL_RAW")"
  run_nb 02_master.ipynb
  "$PY" src/revision/d1_atraso_notificacao.py
  "$PY" - "$WORK/committed/data/master" data/master <<'EOF'
import sys
from pathlib import Path
import pandas as pd
a, b = Path(sys.argv[1]), Path(sys.argv[2])
bad = []
for f in sorted(a.glob("*.parquet")):
    x, y = pd.read_parquet(f), pd.read_parquet(b / f.name)
    if not x.equals(y):
        bad.append(f.name)
for f in sorted(a.glob("*.csv")):
    if f.read_bytes() != (b / f.name).read_bytes():
        bad.append(f.name)
print("data/master: identical to the commit" if not bad else f"data/master DIFFERS: {bad}")
sys.exit(1 if bad else 0)
EOF
else
  echo "-- ARBOVIRAL_RAW not set: starting from the committed data/master (02 not rerun)"
fi

run_nb 03_train.ipynb
run_nb 04_results.ipynb
run_nb 05_revision_analyses.ipynb
run_nb 06_paper_outputs.ipynb

echo "== Comparing generated outputs with the commit"
status=0
compare() {
  if cmp -s "$WORK/committed/$1" "$1"; then echo "   same      $1"
  else echo "   DIFFERENT $1"; status=1; fi
}
for f in "$WORK"/committed/figuras/*; do compare "figuras/$(basename "$f")"; done
extra=$(comm -13 <(cd "$WORK/committed" && find figuras -type f | sort) <(find figuras -type f | sort))
[[ -z "$extra" ]] || { echo "   generated but not committed: $extra"; status=1; }

if [[ -z "${PAPER_DIR:-}" ]]; then
  echo "== PAPER_DIR not set: paper/numbers.tex and paper/tables/ written, not compared"
else
  echo "== Comparing with the LaTeX source in PAPER_DIR"
  compare paper/numbers.tex
  compare paper/abstract_openreview.txt
  for f in "$WORK"/committed/paper/tables/*.tex; do compare "paper/tables/$(basename "$f")"; done
  extra=$(comm -13 <(cd "$WORK/committed" && find paper/tables -type f | sort) \
                   <(find paper/tables -type f | sort))
  [[ -z "$extra" ]] || { echo "   generated but not in PAPER_DIR: $extra"; status=1; }

  echo "== Compiling the PDF"
  (cd paper && pdflatex -interaction=nonstopmode main >/dev/null; bibtex main >/dev/null;
   pdflatex -interaction=nonstopmode main >/dev/null; pdflatex -interaction=nonstopmode main >/dev/null) || true
  test -s paper/main.pdf || { echo "   PDF not produced"; status=1; }
  grep -E "^! " paper/main.log && status=1 || echo "   no LaTeX errors"
  echo "   overfull boxes: $(grep -c 'Overfull' paper/main.log || true)"
  grep -E "Warning" paper/main.log | grep -v "Font shape" | sort | uniq -c || true

  echo "== Numeric literals left in the LaTeX source"
  "$PY" scripts/lint_numeros.py paper/main.tex paper/appendix.tex
fi

date
if [[ $status -eq 0 ]]; then echo "== RESULT: everything matches $REF"
else echo "== RESULT: differences found (see above)"; fi
exit $status
