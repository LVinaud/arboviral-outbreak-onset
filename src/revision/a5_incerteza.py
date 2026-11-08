"""A5. Incerteza nas Tabelas 1 e 2 (dengue, inc100, h = 1).

Tabela 1: AUROC e AUPRC, média das 3 dobras, faixa entre dobras e IC 95% por
bootstrap de municípios (1000 reamostragens). Tabela 2: recall de onset e de
continuação, precisão geral e entre calmos, falso alarme entre calmos, limiar
0.5, juntando as dobras como o paper, com o mesmo bootstrap. Referência de
estado = rótulo em t, como no paper. Inclui as baselines do paper e as
corrigidas (A1, A2).
"""
import numpy as np
import pandas as pd

from comum import NOMES, OUT_DIR, carregar, pesos_bootstrap, resumo_metrica

df = carregar(1)
MODELOS = ["persistence", "persistence_tm1", "climatology_corr",
           "logreg", "rf", "xgb", "lgbm"]
municipios = np.sort(df["cod_ibge"].unique())
W = pesos_bootstrap(municipios)[:, df["cod_ibge"].map({c: i for i, c in enumerate(municipios)}).values]

# ---- Tabela 1
t1 = []
for m in MODELOS:
    r = resumo_metrica(df, m, np.ones(len(df), bool))
    t1.append({"model": m, **r})
t1 = pd.DataFrame(t1)
t1.to_csv(OUT_DIR / "a5_tabela1_ic.csv", index=False)


def fracao(num, den):
    """Fração num/den (booleanos por linha), ponto, IC bootstrap e faixa entre dobras."""
    num = num.astype(float).values
    den = den.astype(float).values
    if den.sum() == 0:  # ex.: persistência nunca alerta em município calmo
        return (np.nan,) * 5
    ponto = (num * den).sum() / den.sum() if den.sum() else np.nan
    with np.errstate(invalid="ignore", divide="ignore"):
        boot = (W * num * den).sum(1) / (W * den).sum(1)
    dobras = [(num[g] * den[g]).sum() / den[g].sum()
              for g in (df["test_year"] == ty for ty in sorted(df["test_year"].unique()))
              if den[g].sum()]
    return ponto, np.nanpercentile(boot, 2.5), np.nanpercentile(boot, 97.5), min(dobras), max(dobras)


# ---- Tabela 2
calmo = df["s_t"] == 0
onset = calmo & (df["y_true"] == 1)
cont = (df["s_t"] == 1) & (df["y_true"] == 1)
t2 = []
for m in MODELOS:
    alerta = df[m] >= 0.5
    pos = df["y_true"] == 1
    for nome, num, den in [
        ("recall_onset", alerta, onset), ("recall_continuation", alerta, cont),
        ("precision_all", pos, alerta), ("precision_calm", pos, alerta & calmo),
        ("false_alarm_calm", alerta, calmo & ~pos)]:
        p, lo, hi, fmin, fmax = fracao(num, den)
        t2.append({"model": m, "metric": nome, "value": p, "ci_lo": lo, "ci_hi": hi,
                   "fold_min": fmin, "fold_max": fmax, "n_den": int(den.sum())})
t2 = pd.DataFrame(t2)
t2.to_csv(OUT_DIR / "a5_tabela2_ic.csv", index=False)

print("Tabela 1 com incerteza")
for _, r in t1.iterrows():
    print(f"  {NOMES[r.model]:<38} AUROC {r.auroc:.3f} [{r.auroc_ci_lo:.3f}, {r.auroc_ci_hi:.3f}] "
          f"dobras {r.auroc_fold_min:.3f}-{r.auroc_fold_max:.3f} | AUPRC {r.auprc:.3f} "
          f"[{r.auprc_ci_lo:.3f}, {r.auprc_ci_hi:.3f}] dobras {r.auprc_fold_min:.3f}-{r.auprc_fold_max:.3f}")
print("\nTabela 2 com incerteza (%)")
for _, r in t2.iterrows():
    print(f"  {NOMES[r.model]:<38} {r.metric:<20} {100*r.value:5.1f} [{100*r.ci_lo:5.1f}, {100*r.ci_hi:5.1f}] "
          f"dobras {100*r.fold_min:5.1f}-{100*r.fold_max:5.1f}")
