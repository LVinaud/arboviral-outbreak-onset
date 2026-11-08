"""Everything the paper reports, generated from the results on disk.

Reads the tables of 04_results (data/train/tables), the analyses of
05_revision_analyses (data/train/revision) and data/master, and writes:

  paper/numbers.tex          one \\newcommand per number quoted in the text
  paper/tables/*.tex         every table of the paper
  figuras/{timeline,alert_tradeoff,calibration_isotonic}.pdf
  paper/abstract_openreview.txt   both versions of the abstract as plain text

Every qualitative claim the text makes about these numbers ("outperforms at every
horizon", "both are below the pooled score", ...) is asserted here, so a rerun that
changes a number enough to break a sentence stops instead of producing a PDF that
says something false.
"""
import os
import re
from pathlib import Path

os.environ["SOURCE_DATE_EPOCH"] = "0"   # byte-identical PDFs across runs

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
TAB = ROOT / "data" / "train" / "tables"
REV = ROOT / "data" / "train" / "revision"
MASTER = ROOT / "data" / "master"
PAPER = ROOT / "paper"
TABOUT = PAPER / "tables"
FIG = ROOT / "figuras"
TABOUT.mkdir(parents=True, exist_ok=True)

MACROS = {}
CLAIMS = []
WRITTEN = []


# --------------------------------------------------------------------------- helpers
def m(name, value):
    """Register one macro. Names are letters only (LaTeX control words)."""
    assert re.fullmatch(r"n[A-Z][A-Za-z]*", name), name
    assert name not in MACROS, f"duplicate macro {name}"
    MACROS[name] = value


def claim(cond, text):
    """A sentence of the paper that depends on the numbers."""
    CLAIMS.append(text)
    assert bool(cond), f"claim no longer holds: {text}"


def f3(x):
    return f"{x:.3f}"


def f2(x):
    return f"{x:.2f}"


def pct(x, d=1):
    """A fraction as a percentage with d decimals (no % sign)."""
    return f"{100 * x:.{d}f}"


def num(n):
    """Integer with a LaTeX thousands separator."""
    return f"{int(round(n)):,}".replace(",", "{,}")


def signed(x, d=3):
    s = f"{x:+.{d}f}"
    return s.replace("-", "$-$").replace("+", "")


def write_table(name, body):
    (TABOUT / f"{name}.tex").write_text(body.strip() + "\n")
    WRITTEN.append(f"paper/tables/{name}.tex")


def ci(row, col, d=3):
    return f"{row[col]:.{d}f} [{row[col + '_ci_lo']:.{d}f}, {row[col + '_ci_hi']:.{d}f}]"


def cipct(row, col, d=1):
    return (f"{100 * row[col]:.{d}f} [{100 * row[col + '_ci_lo']:.{d}f}, "
            f"{100 * row[col + '_ci_hi']:.{d}f}]")


# --------------------------------------------------------------------------- inputs
t3 = pd.read_csv(TAB / "table3_global_dengue_inc100.csv", index_col=0)
onset04 = pd.read_csv(TAB / "table_onset_vs_continuation.csv", index_col=0)
prev = pd.read_csv(TAB / "table2_label_prevalence.csv")
kappa = pd.read_csv(TAB / "table_kappa_definitions.csv", index_col=0)
grid = pd.read_csv(TAB / "table_full_grid.csv")
hor = pd.read_csv(TAB / "table6_horizon_degradation.csv")
season = pd.read_csv(TAB / "table_by_season.csv", index_col=0)
size = pd.read_csv(TAB / "table_by_municipality_size.csv")
abl = pd.read_csv(TAB / "table_ablation_groups.csv")
inc = pd.read_csv(TAB / "table_incremental_groups.csv")
shap = pd.read_csv(TAB / "table_shap_groups.csv")
budget_all = pd.read_csv(TAB / "table_alert_budget.csv")
evaluab = pd.read_csv(TAB / "table_evaluability.csv")

c1 = pd.read_csv(REV / "c1_onset_continuacao.csv")
limpos = pd.read_csv(REV / "c1_onsets_limpos.csv")
a6 = pd.read_csv(REV / "a6_orcamento_calmos.csv")
a9 = pd.read_csv(REV / "a9_shap_onset.csv")
b1ic = pd.read_csv(REV / "b1_dobra_2025_ic.csv")
b1orc = pd.read_csv(REV / "b1_orcamento_2025.csv")
b2 = pd.read_csv(REV / "b2_modelo_onset.csv")
b3 = pd.read_csv(REV / "b3_limiares_passado.csv")
b3lab = pd.read_csv(REV / "b3_mudanca_rotulos.csv")
b4 = pd.read_csv(REV / "b4_tuning.csv")
b4cfg = pd.read_csv(REV / "b4_configs_escolhidas.csv")
c2 = pd.read_csv(REV / "c2_calibracao_resumo.csv")
c2rel = pd.read_csv(REV / "c2_confiabilidade.csv")
c2act = pd.read_csv(REV / "c2_limiares_acao.csv")
delay = pd.read_csv(MASTER / "notification_delay.csv").set_index("year")
master = pd.read_parquet(MASTER / "municipio_mes.parquet")
labels = pd.read_parquet(MASTER / "labels.parquet")

LBL = {"persistence": "Persistence (month t)", "persistence_tm1": "Persistence (real time)",
       "climatology": "Climatology", "logreg": "Logistic regression",
       "rf": "Random Forest", "xgb": "XGBoost", "lgbm": "LightGBM"}
NICE = {"Persistence (month t)": "Persistence (month $t$)",
        "Persistence (real time)": "Persistence (real time)",
        "Climatology": "Climatology", "Logistic regression": "Logistic regression",
        "Random Forest": "Random forest", "XGBoost": "XGBoost", "LightGBM": "LightGBM"}


def rt(h, subset, model, ref="t-1"):
    """One row of C1: onset/continuation metrics."""
    r = c1[(c1.h == h) & (c1.ref == ref) & (c1.subset == subset) & (c1.model == model)]
    assert len(r) == 1, (h, subset, model, ref)
    return r.iloc[0]


# --------------------------------------------------------------------------- data
m("nRows", num(len(master)))
m("nCols", str(master.shape[1]))
n_months = master[["ano", "mes"]].drop_duplicates().shape[0]
m("nMonths", str(n_months))
assert master["cod_ibge"].nunique() == 645
n_feat = abl[abl.definition == "inc100"]["n_features"].sum()
m("nFeatures", str(n_feat))
for y, w in ((2022, "TwentyTwo"), (2023, "TwentyThree")):
    m(f"nDelayN{w}", num(delay.loc[y, "n_notifications"]))
    m(f"nDelaySixty{w}", pct(delay.loc[y, "pct_closed_60d"]))
    m(f"nDelayNinety{w}", pct(delay.loc[y, "pct_closed_90d"]))

# Agreement between definitions
k = kappa
m("nKappaRel", f2(k.loc["canal", "zscore"]))
m("nKappaAbs", f2(k.loc["inc100", "inc300"]))
cross = [k.loc[a, b] for a in ("inc100", "inc300") for b in ("canal", "zscore")]
m("nKappaCrossLo", f2(min(cross)))
m("nKappaCrossHi", f2(max(cross)))
lt = labels[labels["ano"].between(2022, 2024)]
m("nRawAgreeRel", pct((lt["dengue_canal"] == lt["dengue_zscore"]).mean()))

# Evaluable pairs
n_eval = (evaluab["verdict"] == "evaluable").sum()
claim(n_eval == 8, "eight of sixteen pairs can be scored")
claim(set(evaluab.loc[evaluab.verdict != "evaluable", "disease"]) == {"zika", "fa"},
      "the pairs that cannot be scored are exactly Zika and yellow fever")

# --------------------------------------------------------------------------- Table 1
ROWS1 = ["Persistence (month t)", "Persistence (real time)", "Climatology",
         "Logistic regression", "Random Forest", "XGBoost", "LightGBM"]
rate = prev[(prev.disease == "dengue") & (prev.definition == "inc100")]["prev_test_%"].item() / 100
m("nRateInc", f"{100 * rate:.1f}")
trees = t3.loc[["Random Forest", "XGBoost", "LightGBM"]]
m("nTreeAurocLo", f3(trees.auroc.min()))
m("nTreeAurocHi", f3(trees.auroc.max()))
m("nTreeAuprcLo", f3(trees.auprc.min()))
m("nTreeAuprcHi", f3(trees.auprc.max()))
m("nXgbAuroc", f3(t3.loc["XGBoost", "auroc"]))
claim(t3.auroc.idxmax() == "XGBoost", "XGBoost has the best pooled AUROC")
best_auprc = t3.loc[["Logistic regression", "Random Forest", "XGBoost", "LightGBM"], "auprc"].max()
for key, lbl in (("Pers", "Persistence (month t)"), ("PersRt", "Persistence (real time)")):
    m(f"n{key}Auroc", f3(t3.loc[lbl, "auroc"]))
    m(f"n{key}Auprc", f3(t3.loc[lbl, "auprc"]))
    m(f"n{key}Share", f"{100 * (t3.loc[lbl, 'auprc'] - rate) / (best_auprc - rate):.0f}")
lines = []
for lbl in ROWS1:
    r = t3.loc[lbl]
    au = f3(r.auroc)
    ap = f3(r.auprc)
    if lbl == t3.auroc.idxmax():
        au = r"\textbf{" + au + "}"
    if lbl == t3.auprc.idxmax():
        ap = r"\textbf{" + ap + "}"
    lines.append(f"{NICE[lbl]} & {au} & {ap} & {r.lift:.1f} \\\\")
write_table("tab_global", r"""
\begin{table}[t]
\centering\small
\caption{One month ahead, dengue, inc100, mean over the test years 2022 to 2024.
The outbreak rate is \nRateInc\%; lift is AUPRC divided by it. Persistence
(month $t$) uses a month not yet consolidated on the issue date.}
\label{tab:global}
\begin{tabular}{lccc}
\toprule
Model & AUROC & AUPRC & Lift \\
\midrule
""" + "\n".join(lines) + r"""
\bottomrule
\end{tabular}
\end{table}
""")

# --------------------------------------------------------------------------- Table 2 (reference t)
rf = onset04.loc["Random Forest"]
m("nOnsetsHOne", num(rf.n_onset))
m("nContsHOne", num(rf.n_continuation))
pos_test = prev[(prev.disease == "dengue") & (prev.definition == "inc100")]["pos_test"].item()
claim(rf.n_onset + rf.n_continuation == pos_test, "onsets plus continuations are all outbreak months")
m("nOutbreakMonthsHOne", num(pos_test))
m("nRfOnsetRecallT", pct(rf.recall_onset))
m("nRfContRecallT", pct(rf.recall_continuation))
gap_t1 = round(100 * rf.recall_continuation, 1) - round(100 * rf.recall_onset, 1)
m("nRfGapT", f"{gap_t1:.1f}")
m("nRfPrecAll", pct(rf.precision_global))
m("nRfPrecCalmT", pct(rf.precision_in_calm))
m("nRfFalseAlarmT", pct(rf.false_alarm_calm))
pers = onset04.loc["Persistence (month t)"]
claim(pers.recall_onset == 0 and pers.recall_continuation == 1,
      "persistence (month t) catches every continuation and no onset")
m("nOnsetRateT", pct(rt(1, "onset", "rf", "t").base_rate))
m("nContRateT", pct(rt(1, "continuation", "rf", "t").base_rate))
for key, mod in (("Rf", "rf"), ("Xgb", "xgb")):
    m(f"n{key}OnsetAurocT", f3(rt(1, "onset", mod, "t").auroc))
    m(f"n{key}ContAurocT", f3(rt(1, "continuation", mod, "t").auroc))
m("nRfPooledAuroc", f3(t3.loc["Random Forest", "auroc"]))
for mod in ("rf", "xgb"):
    pooled = t3.loc[LBL[mod], "auroc"]
    claim(rt(1, "onset", mod, "t").auroc < pooled and rt(1, "continuation", mod, "t").auroc < pooled,
          f"{mod}: AUROC within each group is below the pooled AUROC")
    claim(abs(rt(1, "onset", mod, "t").auroc - rt(1, "continuation", mod, "t").auroc) < 0.03,
          f"{mod}: onsets and continuations ranked about equally well at h=1 (reference t)")
lines = []
for lbl in ("Random Forest", "XGBoost", "LightGBM", "Logistic regression", "Climatology",
            "Persistence (month t)", "Persistence (real time)"):
    r = onset04.loc[lbl]
    a, b = round(100 * r.recall_onset, 1), round(100 * r.recall_continuation, 1)
    lines.append(f"{NICE[lbl]} & {a:.1f} & {b:.1f} & {b - a:.1f} \\\\")
write_table("tab_onset", r"""
\begin{table}[t]
\centering\small
\caption{The models of Table~\ref{tab:global}, split by the state in month $t$
(original reference). Recall in per cent at a 0.5 threshold; \nOnsetsHOne{} onsets
and \nContsHOne{} continuations.}
\label{tab:onset}
\begin{tabular}{lccc}
\toprule
 & Onset & Contin. & Gap \\
Model & recall & recall & (pts) \\
\midrule
""" + "\n".join(lines) + r"""
\bottomrule
\end{tabular}
\end{table}
""")

# --------------------------------------------------------------------------- real time (C1)
WORDS = {1: "One", 2: "Two", 3: "Three", 4: "Four", 5: "Five", 6: "Six"}
for h in (1, 3, 6):
    w = WORDS[h]
    m(f"nRtOnsetRateH{w}", pct(rt(h, "onset", "rf").base_rate))
    m(f"nRtContRateH{w}", pct(rt(h, "continuation", "rf").base_rate))
for h in (1, 3):
    w = WORDS[h]
    m(f"nRtRfOnsetRecH{w}", pct(rt(h, "onset", "rf").recall))
    m(f"nRtRfContRecH{w}", pct(rt(h, "continuation", "rf").recall))
    m(f"nRtXgbOnsetAurocH{w}", f3(rt(h, "onset", "xgb").auroc))
    m(f"nRtXgbContAurocH{w}", f3(rt(h, "continuation", "xgb").auroc))
m("nRtXgbOnsetAurocHThreeLo", f3(rt(3, "onset", "xgb").auroc_ci_lo))
m("nRtXgbOnsetAurocHThreeHi", f3(rt(3, "onset", "xgb").auroc_ci_hi))
m("nRtClimOnsetAurocHThree", f3(rt(3, "onset", "climatology_corr").auroc))
m("nRtRfOnsetPrecHThree", pct(rt(3, "onset", "rf").precision))
m("nRtRfContPrecHThree", pct(rt(3, "continuation", "rf").precision))
o1, c1x = rt(1, "onset", "xgb"), rt(1, "continuation", "xgb")
claim(o1.auroc_ci_hi >= c1x.auroc_ci_lo, "h=1 real time: XGBoost onset and continuation AUROC intervals overlap")
claim(rt(1, "onset", "rf").base_rate < rt(1, "continuation", "rf").base_rate,
      "h=1 real time: onsets are rarer than continuations")
claim(abs(rt(3, "onset", "rf").base_rate - rt(3, "continuation", "rf").base_rate) < 0.03,
      "h=3 real time: the two base rates are close")
claim(abs(rt(3, "onset", "rf").recall - rt(3, "continuation", "rf").recall) < 0.05,
      "h=3 real time: recall is similar for onsets and continuations")
claim(rt(3, "onset", "rf").precision < rt(3, "continuation", "rf").precision,
      "h=3 real time: precision on onsets is lower")
diffs = [rt(h, "continuation", "xgb").auroc - rt(h, "onset", "xgb").auroc for h in range(2, 7)]
claim(min(diffs) > 0, "from h=2 on, XGBoost ranks continuations better than onsets")
m("nRtAurocDiffLo", f3(min(diffs)))
m("nRtAurocDiffHi", f3(max(diffs)))
claim(rt(1, "onset", "rf").base_rate < rt(6, "onset", "rf").base_rate
      and rt(1, "continuation", "rf").base_rate > rt(6, "continuation", "rf").base_rate,
      "the onset rate rises and the continuation rate falls between h=1 and h=6")
for h in range(1, 7):
    x, c = rt(h, "onset", "xgb"), rt(h, "onset", "climatology_corr")
    claim(x.auroc_ci_lo > c.auroc_ci_hi and x.auprc_ci_lo > c.auprc_ci_hi,
          f"h={h}: XGBoost beats climatology on onsets in AUROC and AUPRC, intervals apart")
gap_t3 = round(100 * rt(3, "continuation", "rf", "t").recall, 1) - round(100 * rt(3, "onset", "rf", "t").recall, 1)
m("nRfGapTHThree", f"{gap_t3:.1f}")
claim(all(rt(h, "continuation", "rf", "t").recall < rt(h, "onset", "rf", "t").recall for h in (4, 5, 6)),
      "with reference t, the recall gap reverses from h=4")
claim(rt(3, "onset", "rf").recall >= rt(3, "continuation", "rf").recall - 0.05,
      "with the real-time reference, the h=3 gap disappears")
l1 = limpos[(limpos.h == 1) & (limpos.model == "rf")].iloc[0]
m("nAlreadyStartedHOne", pct(l1.pct_already_started))
m("nRfCleanRecHOne", pct(l1.recall_clean))

LEAD = {1: r"$-1$ (past)", 2: "0 (current)", 3: "1", 4: "2", 5: "3", 6: "4"}
lines = []
for h in range(1, 7):
    o, c = rt(h, "onset", "rf"), rt(h, "continuation", "rf")
    xo, xc = rt(h, "onset", "xgb"), rt(h, "continuation", "xgb")
    cl = rt(h, "onset", "climatology_corr")
    lines.append(f"{h} & {LEAD[h]} & {pct(o.base_rate)} & {pct(c.base_rate)} & "
                 f"{pct(o.recall)} & {pct(c.recall)} & {ci(xo, 'auroc')} & {ci(xc, 'auroc')} & "
                 f"{f3(cl.auroc)} \\\\")
write_table("tab_realtime", r"""
\begin{table*}[t]
\centering\small
\caption{Onset and continuation by horizon with the real-time reference (calm or
in outbreak in month $t-1$, the last consolidated month), dengue, inc100, test
years 2022 to 2024. Lead time is the number of whole months between the issue date
and the target month. Rates and recall in per cent; recall at 0.5, random forest;
AUROC with 95\% bootstrap intervals over municipalities.}
\label{tab:realtime}
\begin{tabular}{ccccccccc}
\toprule
 & Lead time & \multicolumn{2}{c}{Base rate} & \multicolumn{2}{c}{Recall, RF}
 & \multicolumn{2}{c}{AUROC, XGBoost} & Climatology \\
\cmidrule(lr){3-4}\cmidrule(lr){5-6}\cmidrule(lr){7-8}
$h$ & (months) & Onset & Contin. & Onset & Contin. & Onset & Contin. & onset AUROC \\
\midrule
""" + "\n".join(lines) + r"""
\bottomrule
\end{tabular}
\end{table*}
""")

# --------------------------------------------------------------------------- budget (A6)
def bud(h, model, budget="5% dos calmos"):
    r = a6[(a6.h == h) & (a6.model == model) & (a6.budget == budget)]
    assert len(r) == 1, (h, model, budget)
    return r.iloc[0]


for h in (1, 3):
    w = WORDS[h]
    m(f"nBudgetXgbH{w}", pct(bud(h, "xgb").precision_at_k))
    m(f"nBudgetRandH{w}", pct(bud(h, "persistence_tm1").precision_at_k))
    m(f"nBudgetClimH{w}", pct(bud(h, "climatology_corr").precision_at_k))
    claim(bud(h, "xgb").precision_at_k > bud(h, "climatology_corr").precision_at_k
          > bud(h, "persistence_tm1").precision_at_k,
          f"h={h}: XGBoost > climatology > random at a 5% budget")
m("nBudgetRecallXgbHThree", pct(bud(3, "xgb").recall_at_k))

# --------------------------------------------------------------------------- 2025 (B1)
def y25(defn, h, subset, model, period):
    r = b1ic[(b1ic.definition == defn) & (b1ic.h == h) & (b1ic.subset == subset)
             & (b1ic.model == model) & (b1ic.period == period)]
    assert len(r) == 1, (defn, h, subset, model, period)
    return r.iloc[0]


def bud25(defn, h, model, period):
    q = b1orc[(b1orc.definition == defn) & (b1orc.h == h) & (b1orc.model == model)]
    q = q[q.test_year == 2025] if period == "2025" else q[q.test_year <= 2024]
    return q.hits.sum() / q.supported.sum()


P0, P1 = "2022-2024", "2025"
claim(abs(y25("inc100", 1, "pooled", "xgb", P0).auroc - t3.loc["XGBoost", "auroc"]) < 6e-4,
      "B1 reproduces the 2022-2024 pooled AUROC of 04")
claim(abs(bud25("inc100", 3, "xgb", P0) - bud(3, "xgb").precision_at_k) < 1e-9,
      "B1 reproduces the 5% budget precision of A6")
m("nTwentyFiveXgbAuroc", f3(y25("inc100", 1, "pooled", "xgb", P1).auroc))
m("nTwentyFiveXgbOnsetHThree", f3(y25("inc100", 3, "onset_ref_tm1", "xgb", P1).auroc))
m("nTwentyFiveClimOnsetHThree", f3(y25("inc100", 3, "onset_ref_tm1", "climatology_corr", P1).auroc))
m("nTwentyFiveCanalRfAuroc", f3(y25("canal", 1, "pooled", "rf", P1).auroc))
m("nCanalRfAuroc", f3(y25("canal", 1, "pooled", "rf", P0).auroc))
for h in (1, 3):
    claim(y25("inc100", h, "pooled", "xgb", P1).auroc >= y25("inc100", h, "pooled", "xgb", P0).auroc - 0.005
          and y25("inc100", h, "onset_ref_tm1", "xgb", P1).auroc >= y25("inc100", h, "onset_ref_tm1", "xgb", P0).auroc - 0.005,
          f"2025, inc100, h={h}: as good or better than 2022-2024")
claim(y25("canal", 1, "pooled", "rf", P1).auroc < y25("canal", 1, "pooled", "rf", P0).auroc,
      "2025 is weaker under the historical range")
for h in range(1, 7):
    claim(y25("canal", h, "onset_ref_tm1", "xgb", P1).auroc > y25("canal", h, "onset_ref_tm1", "climatology_corr", P1).auroc,
          f"2025, historical range, h={h}: XGBoost still beats climatology on onsets")
    claim(y25("inc100", h, "onset_ref_tm1", "xgb", P1).auroc > y25("inc100", h, "onset_ref_tm1", "climatology_corr", P1).auroc,
          f"2025, inc100, h={h}: XGBoost beats climatology on onsets")
rows25 = [("All months, XGBoost", "inc100", 1, "pooled", "xgb"),
          ("Onsets, XGBoost", "inc100", 1, "onset_ref_tm1", "xgb"),
          ("Onsets, XGBoost", "inc100", 3, "onset_ref_tm1", "xgb"),
          ("Onsets, climatology", "inc100", 3, "onset_ref_tm1", "climatology_corr"),
          ("All months, random forest", "canal", 1, "pooled", "rf"),
          ("Onsets, XGBoost", "canal", 3, "onset_ref_tm1", "xgb"),
          ("Onsets, climatology", "canal", 3, "onset_ref_tm1", "climatology_corr")]
lines = [r"\multicolumn{4}{l}{\emph{inc100}} \\"]
for i, (lab, d, h, s, mod) in enumerate(rows25):
    if i == 4:
        lines.append(r"\multicolumn{4}{l}{\emph{Historical range}} \\")
    lines.append(f"{lab} & {h} & {f3(y25(d, h, s, mod, P0).auroc)} & {f3(y25(d, h, s, mod, P1).auroc)} \\\\")
lines.insert(5, f"5\\% budget precision, XGBoost & 3 & {pct(bud25('inc100', 3, 'xgb', P0))}\\% & "
                f"{pct(bud25('inc100', 3, 'xgb', P1))}\\% \\\\")
write_table("tab_2025", r"""
\begin{table}[t]
\centering\small
\caption{2025 as a fourth test year, against the mean of 2022 to 2024. AUROC
unless stated; onsets with the real-time reference.}
\label{tab:y2025}
\begin{tabular}{lccc}
\toprule
 & $h$ & 2022--24 & 2025 \\
\midrule
""" + "\n".join(lines) + r"""
\bottomrule
\end{tabular}
\end{table}
""")

# --------------------------------------------------------------------------- onset-only model (B2)
g2 = b2.groupby(["h", "ref", "model"])[["onset_auroc", "onset_auprc", "precision_at_5pct",
                                        "recall_onset_05", "false_alarm_05"]].mean()
deltas, not_better, cases = [], 0, 0
for (h, ref) in sorted({(a, b) for a, b, _ in g2.index}):
    for mod in ("rf", "xgb"):
        u, o = g2.loc[(h, ref, f"{mod}_unico")], g2.loc[(h, ref, f"{mod}_onset")]
        deltas.append(abs(o.onset_auroc - u.onset_auroc))
        not_better += int(o.precision_at_5pct <= u.precision_at_5pct)
        cases += 1
m("nOnsetModelMaxDelta", f3(max(deltas)))
m("nOnsetModelNotBetter", str(not_better))
m("nOnsetModelCases", str(cases))
lines = []
for (h, ref) in sorted({(a, b) for a, b, _ in g2.index}, key=lambda x: (x[0], x[1] != "t-1")):
    for mod, nm in (("rf", "Random forest"), ("xgb", "XGBoost")):
        u, o = g2.loc[(h, ref, f"{mod}_unico")], g2.loc[(h, ref, f"{mod}_onset")]
        refl = "$t-1$" if ref == "t-1" else "$t$"
        lines.append(f"{h} & {refl} & {nm} & {f3(u.onset_auroc)} & {f3(o.onset_auroc)} & "
                     f"{f3(u.onset_auprc)} & {f3(o.onset_auprc)} & {pct(u.precision_at_5pct)} & "
                     f"{pct(o.precision_at_5pct)} & {pct(u.recall_onset_05)} & {pct(o.recall_onset_05)} \\\\")
write_table("tab_onsetmodel", r"""
\begin{table*}[t]
\centering\small
\caption{The single model (S) against a model trained only on calm months (O), on
the same calm test months, dengue, inc100, mean of the test years. Precision at
5\% and recall at 0.5 in per cent.}
\label{tab:onsetmodel}
\begin{tabular}{cclcccccccc}
\toprule
 & & & \multicolumn{2}{c}{Onset AUROC} & \multicolumn{2}{c}{Onset AUPRC}
 & \multicolumn{2}{c}{Precision at 5\%} & \multicolumn{2}{c}{Recall at 0.5} \\
\cmidrule(lr){4-5}\cmidrule(lr){6-7}\cmidrule(lr){8-9}\cmidrule(lr){10-11}
$h$ & Ref. & Model & S & O & S & O & S & O & S & O \\
\midrule
""" + "\n".join(lines) + r"""
\bottomrule
\end{tabular}
\end{table*}
""")

# --------------------------------------------------------------------------- past-only thresholds (B3)
g3 = b3.groupby(["definition", "h", "model", "labels"])[
    ["auroc", "auprc", "onset_auroc_ref_t", "onset_auroc_ref_tm1", "recall_onset_ref_t",
     "recall_cont_ref_t"]].mean()
m("nPastChangedLo", f"{100 * b3lab.pct_changed.min():.0f}")
m("nPastChangedHi", f"{100 * b3lab.pct_changed.max():.0f}")
dd = {}
for d in ("canal", "zscore"):
    v = [g3.loc[(d, h, mod, "past-only"), c] - g3.loc[(d, h, mod, "paper"), c]
         for h in (1, 2) for mod in ("rf", "xgb") for c in ("onset_auroc_ref_t", "onset_auroc_ref_tm1")]
    dd[d] = (min(v), max(v))
claim(dd["canal"][0] > 0, "historical range: onset AUROC rises with past-only thresholds")
m("nPastCanalLo", f3(dd["canal"][0]))
m("nPastCanalHi", f3(dd["canal"][1]))
m("nPastZLo", signed(dd["zscore"][0]))
m("nPastZHi", signed(dd["zscore"][1]))
claim(all(g3.loc[("zscore", h, "rf", "past-only"), "recall_onset_ref_t"]
          < g3.loc[("zscore", h, "rf", "paper"), "recall_onset_ref_t"] for h in (1, 2)),
      "standard score: recall at 0.5 drops with past-only thresholds")
lines = []
for d, dn in (("canal", "Hist. range"), ("zscore", "Std. score")):
    for h in (1, 2):
        for mod, nm in (("rf", "RF"), ("xgb", "XGBoost")):
            p, q = g3.loc[(d, h, mod, "paper")], g3.loc[(d, h, mod, "past-only")]
            lines.append(f"{dn} & {h} & {nm} & {f3(p.auroc)} & {f3(q.auroc)} & "
                         f"{f3(p.onset_auroc_ref_tm1)} & {f3(q.onset_auroc_ref_tm1)} & "
                         f"{pct(p.recall_onset_ref_t)} & {pct(q.recall_onset_ref_t)} & "
                         f"{pct(p.recall_cont_ref_t)} & {pct(q.recall_cont_ref_t)} \\\\")
lab_lines = []
for _, r in b3lab.iterrows():
    dn = "Hist. range" if r.definition == "canal" else "Std. score"
    lab_lines.append(f"{r.test_year} & {dn} & {pct(r.prev_paper)} & {pct(r.prev_past_only)} & "
                     f"{pct(r.pct_changed)} & {f2(r.kappa)} \\\\")
write_table("tab_past", r"""
\begin{table*}[t]
\centering\small
\caption{Thresholds fitted on the whole series (W) against thresholds from earlier
years only (P), dengue, mean of the test years. Onset AUROC with the real-time
reference; recall at 0.5 in per cent with the original reference. Below: how the
test labels change.}
\label{tab:past}
\begin{tabular}{lclcccccccc}
\toprule
 & & & \multicolumn{2}{c}{AUROC} & \multicolumn{2}{c}{Onset AUROC}
 & \multicolumn{2}{c}{Onset recall} & \multicolumn{2}{c}{Contin. recall} \\
\cmidrule(lr){4-5}\cmidrule(lr){6-7}\cmidrule(lr){8-9}\cmidrule(lr){10-11}
Definition & $h$ & Model & W & P & W & P & W & P & W & P \\
\midrule
""" + "\n".join(lines) + r"""
\bottomrule
\end{tabular}

\vspace{6pt}
\begin{tabular}{llcccc}
\toprule
Test year & Definition & Rate, W (\%) & Rate, P (\%) & Labels changed (\%) & $\kappa$ \\
\midrule
""" + "\n".join(lab_lines) + r"""
\bottomrule
\end{tabular}
\end{table*}
""")

# --------------------------------------------------------------------------- tuning (B4)
g4 = b4.groupby(["h", "model"])[["auroc", "auprc", "onset_auroc_ref_t", "onset_auroc_ref_tm1",
                                 "recall_onset_ref_t", "recall_cont_ref_t"]].mean()
tdelta = max(abs(g4.loc[(h, f"{mod}_tuned"), "auroc"] - g4.loc[(h, mod), "auroc"])
             for h in (1, 2) for mod in ("rf", "xgb"))
m("nTuneMaxDelta", f3(tdelta))
m("nTuneAboveMedian", str(int((b4cfg.val_auprc_paper_config > b4cfg.val_auprc_median_search).sum())))
claim(len(b4cfg) == 12, "twelve tuning cases")
xt = g4.loc[(1, "xgb_tuned")]
m("nTuneXgbOnsetRec", pct(xt.recall_onset_ref_t))
m("nTuneXgbContRec", pct(xt.recall_cont_ref_t))
claim(xt.recall_cont_ref_t - xt.recall_onset_ref_t > 0.2, "the gap remains after tuning")
lines = []
for h in (1, 2):
    for mod, nm in (("rf", "Random forest"), ("xgb", "XGBoost")):
        a, b = g4.loc[(h, mod)], g4.loc[(h, f"{mod}_tuned")]
        lines.append(f"{h} & {nm} & {f3(a.auroc)} & {f3(b.auroc)} & {f3(a.auprc)} & {f3(b.auprc)} & "
                     f"{f3(a.onset_auroc_ref_tm1)} & {f3(b.onset_auroc_ref_tm1)} & "
                     f"{pct(a.recall_onset_ref_t)} & {pct(b.recall_onset_ref_t)} & "
                     f"{pct(a.recall_cont_ref_t)} & {pct(b.recall_cont_ref_t)} \\\\")
write_table("tab_tuning", r"""
\begin{table*}[t]
\centering\small
\caption{Fixed configuration (F) against the configuration chosen by random search
on the year before each test year (T), dengue, inc100, mean of the test years.
Onset AUROC with the real-time reference; recall at 0.5 in per cent with the
original reference.}
\label{tab:tuning}
\begin{tabular}{clcccccccccc}
\toprule
 & & \multicolumn{2}{c}{AUROC} & \multicolumn{2}{c}{AUPRC} & \multicolumn{2}{c}{Onset AUROC}
 & \multicolumn{2}{c}{Onset recall} & \multicolumn{2}{c}{Contin. recall} \\
\cmidrule(lr){3-4}\cmidrule(lr){5-6}\cmidrule(lr){7-8}\cmidrule(lr){9-10}\cmidrule(lr){11-12}
$h$ & Model & F & T & F & T & F & T & F & T & F & T \\
\midrule
""" + "\n".join(lines) + r"""
\bottomrule
\end{tabular}
\end{table*}
""")

# --------------------------------------------------------------------------- season, size, folds
MONTHS = {"Jan": "January", "Feb": "February", "Mar": "March", "Apr": "April", "May": "May",
          "Jun": "June", "Jul": "July", "Aug": "August", "Sep": "September", "Oct": "October",
          "Nov": "November", "Dec": "December"}
m("nSeasonMinAuroc", f3(season.auroc.min()))
m("nSeasonMinMonth", MONTHS[season.auroc.idxmin()])
m("nSeasonMaxAuroc", f3(season.auroc.max()))
m("nSeasonMaxMonth", MONTHS[season.auroc.idxmax()])
m("nSeasonMinRate", pct(season.base_rate.min()))
m("nSeasonMaxRate", pct(season.base_rate.max()))
rfs = size[size.model == "Random Forest"].set_index("stratum")
claim(rfs.municipalities.sum() == 645, "size bands partition the 645 municipalities")
m("nSizeSmallAuroc", f3(rfs.loc["< 10k", "auroc"]))
m("nSizeSmallN", str(int(rfs.loc["< 10k", "municipalities"])))
m("nSizeLargeAuroc", f3(rfs.loc["> 200k", "auroc"]))
m("nSizeLargeN", str(int(rfs.loc["> 200k", "municipalities"])))
for y, w in ((2022, "TwentyTwo"), (2023, "TwentyThree"), (2024, "TwentyFour")):
    m(f"nFoldRate{w}", pct(labels.loc[labels.ano == y, "dengue_inc100"].mean()))
lines = [f"{mo} & {f3(r.auroc)} & {f3(r.auroc_min)}--{f3(r.auroc_max)} & {pct(r.base_rate)}\\% \\\\"
         for mo, r in season.iterrows()]
write_table("tab_season", r"""
\begin{table}[t]
\centering\small
\caption{Random forest by the calendar month being predicted, dengue, inc100, one
month ahead. Range spans the three test years.}
\label{tab:season}
\begin{tabular}{lccc}
\toprule
Month & AUROC & Range & Outbreak rate \\
\midrule
""" + "\n".join(lines) + r"""
\bottomrule
\end{tabular}
\end{table}
""")
SIZEN = {"< 10k": "$<$ 10k", "10k–50k": "10k--50k", "50k–200k": "50k--200k", "> 200k": "$>$ 200k"}
lines = [f"{SIZEN[s]} & {int(r.municipalities)} & {r['base_rate_%']:.1f}\\% & {f3(r.auroc)} & {f3(r.auprc)} \\\\"
         for s, r in rfs.iterrows()]
write_table("tab_size", r"""
\begin{table}[t]
\centering\small
\caption{Random forest by municipality size (2022 census), dengue, inc100, one
month ahead. The four bands partition the 645 municipalities.}
\label{tab:size}
\begin{tabular}{lcccc}
\toprule
Population & Munic. & Rate & AUROC & AUPRC \\
\midrule
""" + "\n".join(lines) + r"""
\bottomrule
\end{tabular}
\end{table}
""")

# --------------------------------------------------------------------------- feature families
mean_abl = abl.groupby("group")["delta_auprc"].mean()
m("nAblTarget", f3(mean_abl["target history"]))
others = mean_abl.drop("target history")
m("nAblOtherMax", f3(others.max()))
claim(mean_abl["sanitation"] < 0, "sanitation has a negative ablation value")
m("nAblWeather", f3(mean_abl["climate"]))
shap_mean = shap.groupby(["definition", "group"])["shap_share"].mean().groupby("group").mean()
m("nShapWeather", pct(shap_mean["climate"]))
base = inc[(inc.definition == "inc100") & (inc.group == "(baseline alone)")].iloc[0]
m("nBaseFeat", str(int(base.n_features)))
m("nBaseAuprc", f3(base.auprc))
m("nFullAuprc", f3(t3.loc["Random Forest", "auprc"]))
claim(abs(base.auprc - t3.loc["Random Forest", "auprc"]) < 0.005, "the base of 38 features matches the full model")
CORE = {"target history", "climate", "seasonality"}
w9 = a9.pivot(index="group", columns="subset", values="mean")
m("nShapOtherOnset", pct(w9.loc[~w9.index.isin(CORE), "onset (ref t-1)"].sum()))
m("nShapOtherPooled", pct(w9.loc[~w9.index.isin(CORE), "aggregate (sample 1500)"].sum()))

# --------------------------------------------------------------------------- rarity example, horizon
ck = grid[(grid.disease == "chikungunya") & (grid.definition == "inc300") & (grid.h == 1)].iloc[0]
m("nChikRate", f"{ck['prevalence_%']:.2f}")
m("nChikAuroc", f3(ck.rf_auroc))
m("nChikAuprc", f3(ck.rf_auprc))
claim(ck.rf_auprc < 0.5 < ck.rf_auroc, "chikungunya inc300: high AUROC, low AUPRC")
hh = hor.set_index("h")
m("nHorAurocOne", f3(hh.loc[1, "auroc"]))
m("nHorAurocSix", f3(hh.loc[6, "auroc"]))
m("nHorAuprcOne", f3(hh.loc[1, "auprc"]))
m("nHorAuprcSix", f3(hh.loc[6, "auprc"]))
m("nHorLiftSix", f"{hh.loc[6, 'lift']:.1f}")


def gaur(d, defn, h):
    return grid[(grid.disease == d) & (grid.definition == defn) & (grid.h == h)].iloc[0].rf_auroc


m("nHbdDengue", f3(gaur("dengue", "canal", 1) - gaur("dengue", "canal", 6)))
m("nHbdChik", f3(gaur("chikungunya", "canal", 1) - gaur("chikungunya", "canal", 6)))
GNAME = {"dengue": "Dengue", "chikungunya": "Chikung."}
DNAME = {"inc100": "inc100", "inc300": "inc300", "canal": "hist.\\ range", "zscore": "std.\\ score"}
lines = []
for d in ("dengue", "chikungunya"):
    for defn in ("inc100", "inc300", "canal", "zscore"):
        g = grid[(grid.disease == d) & (grid.definition == defn)].set_index("h")
        if g.empty:
            continue
        lines.append(f"{GNAME[d]} & {DNAME[defn]} & {g.loc[1, 'prevalence_%']:.2f}\\% & "
                     f"{f3(g.loc[1, 'rf_auroc'])} & {f3(g.loc[3, 'rf_auroc'])} & {f3(g.loc[6, 'rf_auroc'])} & "
                     f"{f3(g.loc[1, 'rf_auprc'])} & {f3(g.loc[6, 'rf_auprc'])} \\\\")
claim(len(lines) == 8, "the grid has the eight evaluable pairs")
write_table("tab_grid", r"""
\begin{table*}[t]
\centering\small
\caption{The eight evaluable disease and definition pairs, random forest. Rate is
the outbreak rate in the test years; lift is AUPRC divided by it.}
\label{tab:grid}
\begin{tabular}{llcccccc}
\toprule
 & & & \multicolumn{3}{c}{AUROC} & \multicolumn{2}{c}{AUPRC} \\
\cmidrule(lr){4-6}\cmidrule(lr){7-8}
Disease & Defn. & Rate & $h$1 & $h$3 & $h$6 & $h$1 & $h$6 \\
\midrule
""" + "\n".join(lines) + r"""
\bottomrule
\end{tabular}
\end{table*}
""")

# --------------------------------------------------------------------------- calibration (C2)
def cal(h, mod, ver):
    r = c2[(c2.h == h) & (c2.model == mod) & (c2.version == ver)]
    assert len(r) == 1
    return r.iloc[0]


m("nCalRfMidGapRaw", signed(cal(1, "rf", "raw")["mean_gap_0.2_to_0.8"], 2))
m("nCalRfMidGapCal", signed(cal(1, "rf", "calibrated")["mean_gap_0.2_to_0.8"], 2))
m("nCalRfBrierRaw", f3(cal(1, "rf", "raw").brier))
m("nCalRfBrierCal", f3(cal(1, "rf", "calibrated").brier))
claim(cal(1, "rf", "raw")["mean_gap_0.2_to_0.8"] < -0.05, "the raw random forest overestimates mid-range risk")
claim(abs(cal(1, "rf", "calibrated")["mean_gap_0.2_to_0.8"]) < abs(cal(1, "rf", "raw")["mean_gap_0.2_to_0.8"]),
      "calibration reduces the mid-range gap")
claim(cal(1, "rf", "calibrated").brier < cal(1, "rf", "raw").brier, "calibration lowers the Brier score")
act = c2act[(c2act.h == 3) & (c2act.model == "xgb") & (c2act.threshold_C_over_L == 0.2)].iloc[0]
m("nActXgbAlerts", f"{act.alerts_per_month:.0f}")
m("nActXgbPrec", pct(act.precision))
lines = []
for h in (1, 3):
    for mod, nm in (("rf", "Random forest"), ("xgb", "XGBoost"), ("lgbm", "LightGBM")):
        a, b = cal(h, mod, "raw"), cal(h, mod, "calibrated")
        lines.append(f"{h} & {nm} & {f3(a.brier)} & {f3(b.brier)} & {f3(a.ece)} & {f3(b.ece)} & "
                     f"{signed(a['mean_gap_0.2_to_0.8'], 3)} & {signed(b['mean_gap_0.2_to_0.8'], 3)} & "
                     f"{f3(a.auroc)} & {f3(b.auroc)} \\\\")
write_table("tab_calib", r"""
\begin{table*}[t]
\centering\small
\caption{Raw (R) and isotonically calibrated (C) scores, dengue, inc100, test
years 2022 to 2024. ECE is the mean absolute gap between predicted and observed
frequency over ten equal-width bins, weighted by bin size; the mid-range gap is
observed minus predicted, averaged over bins between 0.2 and 0.8 (negative means
risk is overestimated).}
\label{tab:calib}
\begin{tabular}{clcccccccc}
\toprule
 & & \multicolumn{2}{c}{Brier} & \multicolumn{2}{c}{ECE} & \multicolumn{2}{c}{Mid-range gap}
 & \multicolumn{2}{c}{AUROC} \\
\cmidrule(lr){3-4}\cmidrule(lr){5-6}\cmidrule(lr){7-8}\cmidrule(lr){9-10}
$h$ & Model & R & C & R & C & R & C & R & C \\
\midrule
""" + "\n".join(lines) + r"""
\bottomrule
\end{tabular}
\end{table*}
""")
lines = []
for h in (1, 3):
    for _, r in c2act[(c2act.h == h) & (c2act.model == "xgb")].iterrows():
        lines.append(f"{h} & {r.threshold_C_over_L:.1f} & {r.alerts_per_month:.0f} & "
                     f"{pct(r.share_of_calm_flagged)} & {pct(r.precision)} & {pct(r.recall_onsets)} \\\\")
write_table("tab_action", r"""
\begin{table}[t]
\centering\small
\caption{Acting on calm municipalities whose calibrated XGBoost probability exceeds
$C/L$, dengue, inc100, real-time reference. Per cent of calm municipalities
flagged, of flagged municipalities that enter an outbreak (precision), and of
onsets caught (recall).}
\label{tab:action}
\begin{tabular}{cccccc}
\toprule
$h$ & $C/L$ & Alerts/month & Flagged & Precision & Recall \\
\midrule
""" + "\n".join(lines) + r"""
\bottomrule
\end{tabular}
\end{table}
""")

# --------------------------------------------------------------------------- appendix tables from C1
lines = []
for h in range(1, 7):
    lr, lx = limpos[(limpos.h == h) & (limpos.model == "rf")].iloc[0], limpos[(limpos.h == h) & (limpos.model == "xgb")].iloc[0]
    lines.append(f"{h} & {num(lr.n_onset)} & {num(lr.n_already_started)} & {pct(lr.pct_already_started)} & "
                 f"{num(lr.n_clean)} & {cipct(lr, 'recall_clean')} & {cipct(lx, 'recall_clean')} & "
                 f"{pct(lr.recall_already_started)} \\\\")
write_table("tab_started", r"""
\begin{table*}[t]
\centering\small
\caption{Real-time onsets (calm in $t-1$, outbreak in $t+h$) that had already begun
before the issue date, and recall at 0.5 on the rest (``clean''), dengue, inc100,
with 95\% bootstrap intervals over municipalities.}
\label{tab:started}
\begin{tabular}{cccccccc}
\toprule
 & & \multicolumn{2}{c}{Already begun} & & \multicolumn{2}{c}{Recall on clean onsets (\%)} & RF recall on \\
\cmidrule(lr){3-4}\cmidrule(lr){6-7}
$h$ & Onsets & $n$ & \% & Clean & Random forest & XGBoost & begun (\%) \\
\midrule
""" + "\n".join(lines) + r"""
\bottomrule
\end{tabular}
\end{table*}
""")
lines = []
for h in range(1, 7):
    for s, sn in (("onset", "Onset"), ("continuation", "Contin.")):
        r, x, c = rt(h, s, "rf"), rt(h, s, "xgb"), rt(h, s, "climatology_corr")
        hcell = str(h) if s == "onset" else ""
        lines.append(f"{hcell} & {sn} & {pct(r.base_rate)} & {cipct(r, 'precision')} & "
                     f"{cipct(x, 'precision')} & {ci(r, 'auprc')} & {ci(x, 'auprc')} & {ci(c, 'auprc')} & "
                     f"{f3(x.auroc_fold_min)}--{f3(x.auroc_fold_max)} \\\\")
write_table("tab_realtime_full", r"""
\begin{table*}[t]
\centering\small
\caption{Precision at 0.5 and AUPRC by horizon with the real-time reference,
dengue, inc100, with 95\% bootstrap intervals over municipalities. The last column
is the range of XGBoost's AUROC across the three test years.}
\label{tab:realtimefull}
\begin{tabular}{clccccccc}
\toprule
 & & Rate & \multicolumn{2}{c}{Precision (\%)} & \multicolumn{3}{c}{AUPRC} & XGBoost AUROC \\
\cmidrule(lr){4-5}\cmidrule(lr){6-8}
$h$ & & (\%) & Random forest & XGBoost & Random forest & XGBoost & Climatology & across years \\
\midrule
""" + "\n".join(lines) + r"""
\bottomrule
\end{tabular}
\end{table*}
""")
lines = []
for h in range(1, 7):
    o, c = rt(h, "onset", "rf", "t"), rt(h, "continuation", "rf", "t")
    xo, xc, cl = rt(h, "onset", "xgb", "t"), rt(h, "continuation", "xgb", "t"), rt(h, "onset", "climatology_corr", "t")
    a, b = round(100 * o.recall, 1), round(100 * c.recall, 1)
    lines.append(f"{h} & {pct(o.base_rate)} & {pct(c.base_rate)} & {a:.1f} & {b:.1f} & {b - a:.1f} & "
                 f"{f3(xo.auroc)} & {f3(xc.auroc)} & {f3(cl.auroc)} \\\\")
write_table("tab_reft", r"""
\begin{table*}[t]
\centering\small
\caption{Onset and continuation by horizon with the original reference (calm or in
outbreak in month $t$), dengue, inc100. Rates and recall in per cent; recall at 0.5,
random forest; gap is continuation minus onset recall.}
\label{tab:reft}
\begin{tabular}{ccccccccc}
\toprule
 & \multicolumn{2}{c}{Base rate} & \multicolumn{3}{c}{Recall, RF} & \multicolumn{2}{c}{AUROC, XGBoost} & Climatology \\
\cmidrule(lr){2-3}\cmidrule(lr){4-6}\cmidrule(lr){7-8}
$h$ & Onset & Contin. & Onset & Contin. & Gap & Onset & Contin. & onset AUROC \\
\midrule
""" + "\n".join(lines) + r"""
\bottomrule
\end{tabular}
\end{table*}
""")

# --------------------------------------------------------------------------- budget tables
BUD = [("k=10", "10"), ("k=25", "25"), ("k=50", "50"), ("5% dos calmos", "5\\%"), ("10% dos calmos", "10\\%")]
BMOD = [("xgb", "XGBoost"), ("rf", "Random forest"), ("lgbm", "LightGBM"), ("logreg", "Logistic regression"),
        ("climatology_corr", "Climatology"), ("persistence_tm1", "Random")]
lines = []
for h in (1, 3):
    for mod, nm in BMOD:
        cells = [pct(bud(h, mod, b).precision_at_k) for b, _ in BUD]
        lines.append(f"{h if mod == 'xgb' else ''} & {nm} & " + " & ".join(cells)
                     + f" & {pct(bud(h, mod).recall_at_k)} \\\\")
    if h == 1:
        lines.append(r"\addlinespace")
write_table("tab_budget_calm", r"""
\begin{table*}[t]
\centering\small
\caption{Precision (\%) when supporting, each month, the highest-scored
municipalities among those calm in the last consolidated month: a fixed number
$k$, or a share of the calm municipalities. The last column is recall at the 5\%
budget. ``Random'' is real-time persistence, which is constant among calm
municipalities. Dengue, inc100, test years 2022 to 2024.}
\label{tab:budgetcalm}
\begin{tabular}{clcccccc}
\toprule
$h$ & Model & $k=10$ & $k=25$ & $k=50$ & 5\% & 10\% & Recall at 5\% \\
\midrule
""" + "\n".join(lines) + r"""
\bottomrule
\end{tabular}
\end{table*}
""")
lines = []
for lbl in ("Random Forest", "XGBoost", "Persistence (month t)", "Persistence (real time)", "Climatology"):
    q = budget_all[budget_all.model == lbl]
    for i, (_, r) in enumerate(q.iterrows()):
        lines.append(f"{NICE[lbl] if i == 0 else ''} & {int(r.k)} & {r['recall_%']:.1f}\\% & {r['precision_%']:.1f}\\% \\\\")
    lines.append(r"\addlinespace")
write_table("tab_budget_all", r"""
\begin{table}[t]
\centering\small
\caption{Supporting the $k$ highest-ranked of all 645 municipalities each month,
dengue, inc100, one month ahead: share of the month's outbreaks covered, and share
of supported municipalities in an outbreak.}
\label{tab:budgetall}
\begin{tabular}{lccc}
\toprule
Model & $k$ & Covered & In outbreak \\
\midrule
""" + "\n".join(lines[:-1]) + r"""
\bottomrule
\end{tabular}
\end{table}
""")

# --------------------------------------------------------------------------- 2025 full
lines = []
for d, dn in (("inc100", "inc100"), ("canal", "Hist. range")):
    for h in range(1, 7):
        cells = []
        for s, mod in (("pooled", "xgb"), ("onset_ref_tm1", "xgb"), ("onset_ref_tm1", "climatology_corr"),
                       ("continuation_ref_tm1", "xgb")):
            cells += [f3(y25(d, h, s, mod, P0).auroc), f3(y25(d, h, s, mod, P1).auroc)]
        cells += [pct(bud25(d, h, "xgb", P0)), pct(bud25(d, h, "xgb", P1))]
        lines.append(f"{dn if h == 1 else ''} & {h} & " + " & ".join(cells) + " \\\\")
    if d == "inc100":
        lines.append(r"\addlinespace")
write_table("tab_2025_full", r"""
\begin{table*}[t]
\centering\small
\caption{2025 (25) against the mean of 2022 to 2024 (22--24), dengue. AUROC of
XGBoost over all months, on onsets and on continuations with the real-time
reference, and of climatology on onsets; precision (\%) of XGBoost when supporting
5\% of calm municipalities each month.}
\label{tab:y2025full}
\begin{tabular}{lccccccccccc}
\toprule
 & & \multicolumn{2}{c}{All months} & \multicolumn{2}{c}{Onsets} & \multicolumn{2}{c}{Onsets, clim.}
 & \multicolumn{2}{c}{Continuations} & \multicolumn{2}{c}{5\% budget} \\
\cmidrule(lr){3-4}\cmidrule(lr){5-6}\cmidrule(lr){7-8}\cmidrule(lr){9-10}\cmidrule(lr){11-12}
Definition & $h$ & 22--24 & 25 & 22--24 & 25 & 22--24 & 25 & 22--24 & 25 & 22--24 & 25 \\
\midrule
""" + "\n".join(lines) + r"""
\bottomrule
\end{tabular}
\end{table*}
""")

# --------------------------------------------------------------------------- Zika and yellow fever
z = master[["ano", "zika_casos"]].groupby("ano")["zika_casos"].sum()
m("nZikaCases", num(z.sum()))
m("nZikaShareSixteen", pct(z.loc[2016] / z.sum()))
zl = labels.groupby("ano")[["zika_inc100", "zika_inc300", "zika_canal", "zika_zscore"]].sum()
claim(zl.loc[zl.index >= 2020].sum().sum() == 0, "no Zika outbreak month from 2020 on under any definition")
lines = [f"{y} & {num(z.loc[y])} & " + " & ".join(str(int(zl.loc[y, c])) for c in zl.columns) + " \\\\"
         for y in z.index]
lines.append(r"\midrule")
lines.append(f"Total & {num(z.sum())} & " + " & ".join(str(int(zl[c].sum())) for c in zl.columns) + " \\\\")
write_table("tab_rare", r"""
\begin{table}[t]
\centering\small
\caption{Confirmed Zika cases in the 645 municipalities and outbreak months under
each definition, by year (2026 up to June).}
\label{tab:rare}
\begin{tabular}{lccccc}
\toprule
 & & \multicolumn{4}{c}{Outbreak months} \\
\cmidrule(lr){3-6}
Year & Cases & inc100 & inc300 & Hist. & Std. \\
\midrule
""" + "\n".join(lines) + r"""
\bottomrule
\end{tabular}
\end{table}
""")

# --------------------------------------------------------------------------- figures
COL = {"rf": "#0072B2", "xgb": "#D55E00", "lgbm": "#009E73", "logreg": "#5D3A9B",
       "climatology_corr": "#8c8c8c", "persistence_tm1": "#3a3a3a"}
NAMEF = {"rf": "Random forest", "xgb": "XGBoost", "lgbm": "LightGBM", "logreg": "Logistic regression",
         "climatology_corr": "Climatology", "persistence_tm1": "Random"}
INK, MUTED, GRID = "#1a1a1a", "#5c5c5c", "#d9d9d9"
plt.rcParams.update({"font.size": 8, "axes.edgecolor": GRID, "axes.labelcolor": MUTED,
                     "xtick.color": MUTED, "ytick.color": MUTED, "pdf.fonttype": 42})


def style(ax):
    ax.grid(True, color=GRID, linewidth=0.6)
    ax.set_axisbelow(True)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)


def save(fig, name):
    fig.savefig(FIG / f"{name}.pdf", bbox_inches="tight")
    fig.savefig(FIG / f"{name}.png", bbox_inches="tight", dpi=200)
    plt.close(fig)
    WRITTEN.append(f"figuras/{name}.pdf")


# Timeline of one forecast
fig, ax = plt.subplots(figsize=(3.4, 1.75))
months = ["Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
xs = np.arange(len(months))
ax.set_xlim(-0.6, len(months) - 0.4)
ax.set_ylim(-1.55, 1.45)
ax.axis("off")
for x, mo in zip(xs, months):
    ax.add_patch(plt.Rectangle((x - 0.46, -0.22), 0.92, 0.44, color="#f0f0f0", lw=0))
    ax.text(x, 0, mo, ha="center", va="center", color=INK, fontsize=7.5)
ax.add_patch(plt.Rectangle((-0.46 + 0.0, -0.22), 1.92, 0.44, fill=False, ec=COL["rf"], lw=1.2))
ax.text(0.5, 0.36, "cases consolidated", ha="center", va="bottom", fontsize=6.5, color=COL["rf"])
ax.add_patch(plt.Rectangle((2 - 0.46, -0.22), 0.92, 0.44, fill=False, ec=COL["lgbm"], lw=1.2, ls=(0, (2, 1))))
ax.text(2, 0.36, "weather only\n(row $t$)", ha="center", va="bottom", fontsize=6.5, color=COL["lgbm"])
ax.annotate("", xy=(3.5, 0.95), xytext=(3.5, 0.25), arrowprops=dict(arrowstyle="-|>", color=COL["xgb"], lw=1.0))
ax.text(3.5, 1.0, "issued 1 Aug", ha="center", va="bottom", fontsize=6.5, color=COL["xgb"])
for h in range(1, 7):
    x = 2 + h
    ax.text(x, -0.42, f"$h$={h}", ha="center", va="top", fontsize=6.5, color=INK)
    lead = {1: "past", 2: "current"}.get(h, f"+{h - 2} mo")
    ax.text(x, -0.78, lead, ha="center", va="top", fontsize=6, color=MUTED)
ax.text(1.0, -1.25, "reference: May (real time) or June (original)", ha="center", va="top",
        fontsize=6.5, color=MUTED)
ax.annotate("", xy=(1, -0.3), xytext=(1, -1.18), arrowprops=dict(arrowstyle="-", color=GRID, lw=0.8))
ax.annotate("", xy=(2, -0.3), xytext=(2, -1.18), arrowprops=dict(arrowstyle="-", color=GRID, lw=0.8))
save(fig, "timeline")

# Alerts raised against onsets caught
pcts = a6[a6.budget_type == "pct"].copy()
fig, axes = plt.subplots(1, 2, figsize=(3.4, 1.9), sharey=True)
for ax, h in zip(axes, (1, 3)):
    q = pcts[pcts.h == h]
    for mod in ("xgb", "rf", "climatology_corr", "persistence_tm1"):
        s = q[q.model == mod].sort_values("budget_value")
        x = np.r_[0, 100 * s.budget_value.values]
        y = np.r_[0, 100 * s.recall_at_k.values]
        kw = {"color": COL[mod], "lw": 1.4}
        if mod == "persistence_tm1":
            kw.update(ls=(0, (4, 2)), lw=1.0)
        if mod == "climatology_corr":
            kw.update(ls=(0, (1, 1.2)))
        ax.plot(x, y, label=NAMEF[mod], **kw)
    ax.axvline(5, color=GRID, lw=0.8, zorder=0)
    ax.set_xlim(0, 50)
    ax.set_ylim(0, 100)
    ax.set_title(f"$h$={h}" + (" (nowcast)" if h == 1 else " (1 month ahead)"), fontsize=7.5, color=INK)
    ax.set_xlabel("Calm municipalities flagged (%)", fontsize=7)
    style(ax)
axes[0].set_ylabel("Onsets caught (%)", fontsize=7)
axes[1].legend(frameon=False, fontsize=6.2, loc="lower right", labelcolor=INK, handlelength=2.2)
fig.tight_layout(w_pad=0.6)
save(fig, "alert_tradeoff")

# Reliability before and after isotonic calibration
fig, axes = plt.subplots(1, 2, figsize=(6.4, 2.7), sharey=True)
for ax, h in zip(axes, (1, 3)):
    ax.plot([0, 1], [0, 1], color=GRID, lw=1.0, zorder=1)
    for mod in ("rf", "xgb"):
        for ver, ls, mk in (("raw", (0, (2, 1.5)), "o"), ("calibrated", "-", "s")):
            q = c2rel[(c2rel.h == h) & (c2rel.model == mod) & (c2rel.version == ver)]
            ax.plot(q.predicted, q.observed, color=COL[mod], ls=ls, marker=mk, ms=3.5, lw=1.3,
                    label=f"{NAMEF[mod]}, {ver}")
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.set_title(f"$h$={h}", fontsize=8, color=INK)
    ax.set_xlabel("Predicted probability", fontsize=7.5)
    style(ax)
axes[0].set_ylabel("Observed frequency", fontsize=7.5)
axes[1].legend(frameon=False, fontsize=6.5, loc="upper left", labelcolor=INK)
fig.tight_layout()
save(fig, "calibration_isotonic")

# --------------------------------------------------------------------------- write numbers.tex
lines = ["% Generated by notebooks/06_paper_outputs.ipynb (src/paper/paper_outputs.py).",
         "% Do not edit by hand: rerun the notebook.", ""]
lines += [f"\\newcommand{{\\{k}}}{{{v}}}" for k, v in sorted(MACROS.items())]
(PAPER / "numbers.tex").write_text("\n".join(lines) + "\n")
WRITTEN.append("paper/numbers.tex")


# --------------------------------------------------------------------------- abstract as plain text
def plain(tex):
    for k, v in MACROS.items():
        tex = re.sub(r"\\" + k + r"(?![A-Za-z])(\{\})?", lambda _m, v=v: v, tex)
    tex = (tex.replace("\\%", "%").replace("{,}", ",").replace("\\~a", "ã").replace("S\\~ao", "São")
           .replace("$-$", "-"))
    tex = re.sub(r"\\[a-zA-Z]+\{([^}]*)\}", r"\1", tex)
    return re.sub(r"\s+", " ", tex).strip()


src = (PAPER / "main.tex").read_text()
ab = src.split("\\begin{abstract}")[1].split("\\end{abstract}")[0]
real, ref = ab.split("\\ifabstractrealtime")[1].split("\\else")
ref = ref.split("\\fi")[0]
txt = ("Version A (real time throughout)\n\n" + plain(real) + "\n\n"
       "Version B (each number with its reference)\n\n" + plain(ref) + "\n")
assert "\\" not in txt, "a LaTeX command survived in the plain-text abstract"
(PAPER / "abstract_openreview.txt").write_text(txt)
WRITTEN.append("paper/abstract_openreview.txt")

# Every macro the paper uses must be defined, and every defined macro used.
used = set()
for f in ("main.tex", "appendix.tex", *[f"tables/{p.name}" for p in TABOUT.glob("*.tex")]):
    used |= set(re.findall(r"\\(n[A-Z][A-Za-z]*)", (PAPER / f).read_text()))
missing = sorted(used - set(MACROS))
unused = sorted(set(MACROS) - used)
assert not missing, f"macros used but not defined: {missing}"

print(f"{len(MACROS)} macros, {len(CLAIMS)} claims checked")
if unused:
    print("defined but not used:", ", ".join(unused))
print("written:")
for w in WRITTEN:
    print("  ", w)
