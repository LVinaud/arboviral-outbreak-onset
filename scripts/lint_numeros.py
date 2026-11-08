"""Lists every numeric literal left in the LaTeX prose, so that each can be
checked: a result must come from a macro in paper/numbers.tex; what may stay as a
literal is a design parameter (thresholds, horizons, years, budgets), a count fixed
by the study (645 municipalities, sixteen sources) or a number quoted from a cited
paper.

    python scripts/lint_numeros.py paper/main.tex paper/appendix.tex
"""
import re
import sys
from pathlib import Path

SKIP = [r"\\(?:label|ref|eqref|citep?|citet|input|url|includegraphics|graphicspath|"
        r"addlinespace|vspace|cmidrule|newcommand|renewcommand|setcounter|begin|end|"
        r"jmlrvolume|jmlryear|todo)\*?(?:\[[^\]]*\])?\{[^}]*\}",
        r"\\[A-Za-z]+",                      # any control word, including the macros
        r"\[(?:t|!ht|width=[^\]]*)\]",       # float placement and widths
        r"\d*\.?\d+\\(?:linewidth|textwidth)",
        r"\[\d+pt\]",
        r"\b[a-z_]+\d{4}[a-z_]+\b",          # citation keys split across lines
        r"\{[\d.]+\}"]                      # numeric arguments in the preamble
NUM = re.compile(r"(?<![A-Za-z\d.])\d(?:[\d.,{}]*\d)?(?![A-Za-z\d])")

total = 0
for path in sys.argv[1:]:
    text = Path(path).read_text()
    start = text.find("\\begin{document}")
    offset = text[:start].count("\n") if start >= 0 else 0
    body = text[start:] if start >= 0 else text
    for i, line in enumerate(body.splitlines(), start=offset + 1):
        clean = re.sub(r"(?<!\\)%.*", "", line)
        for pat in SKIP:
            clean = re.sub(pat, " ", clean)
        hits = [h for h in NUM.findall(clean) if h.strip(".,{}")]
        if hits:
            total += len(hits)
            print(f"{path}:{i}: {', '.join(hits):<28} | {line.strip()[:110]}")
print(f"{total} numeric literals listed")
