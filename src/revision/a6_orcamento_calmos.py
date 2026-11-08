"""A6. Orçamento de alertas só entre municípios calmos.

Em cada mês de emissão, ficam só os municípios calmos em t-1 (último mês
consolidado). Ranqueia-se esse conjunto pelo escore de cada modelo e apoia-se o
top k. Positivo = onset (surto em t+h). k fixo (10, 25, 50) ou proporcional
(de 1% a 100% dos calmos do mês, arredondado, mínimo 1); os proporcionais formam
a curva de alertas emitidos contra onsets captados. Todos os modelos no
mesmo k. Empates desfeitos ao acaso: modelos aprendidos com uma semente fixa;
persistência e climatologia com a média de 100 sementes (a persistência em t-1
é constante entre calmos, logo equivale a um sorteio aleatório).
Precisão@k = onsets no top k / apoiados; recall@k = onsets no top k / onsets do
mês, somando sobre os meses das 3 dobras. Faixa entre dobras na precisão.
"""
import numpy as np
import pandas as pd

from comum import NOMES, OUT_DIR, SEED, carregar

MODELOS = ["rf", "xgb", "lgbm", "logreg", "persistence_tm1", "climatology_corr"]
ORCAMENTOS = ([("k", 10), ("k", 25), ("k", 50)]
              + [("pct", f) for f in (0.01, 0.02, 0.05, 0.10, 0.15, 0.20, 0.30, 0.40,
                                      0.50, 0.75, 1.00)])
SEMENTES_BASELINE = 100


def avaliar(meses, coluna, sementes):
    """Devolve, por orçamento, (apoiados, acertos) por dobra, média sobre sementes."""
    acum = {o: {} for o in ORCAMENTOS}
    for s in sementes:
        rng = np.random.default_rng(s)
        for ty, escore, y in meses:
            desempate = rng.random(len(escore))
            ordem = np.lexsort((desempate, -escore))
            y_ord = y[ordem]
            for tipo, valor in ORCAMENTOS:
                k = valor if tipo == "k" else max(1, int(round(valor * len(escore))))
                k = min(k, len(escore))
                a = acum[(tipo, valor)].setdefault(ty, [0.0, 0.0])
                a[0] += k / len(sementes)
                a[1] += y_ord[:k].sum() / len(sementes)
    return acum


linhas = []
for h in range(1, 7):
    df = carregar(h)
    calmos = df[df["s_tm1"] == 0]
    total_onsets = calmos.groupby("test_year")["y_true"].sum()
    for m in MODELOS:
        meses = [(ty, g[m].values, g["y_true"].values)
                 for (ty, _), g in calmos.groupby(["test_year", "mi"])]
        sementes = range(SEED, SEED + SEMENTES_BASELINE) if m in ("persistence_tm1", "climatology_corr") else [SEED]
        acum = avaliar(meses, m, sementes)
        for (tipo, valor), por_dobra in acum.items():
            apoiados = sum(v[0] for v in por_dobra.values())
            acertos = sum(v[1] for v in por_dobra.values())
            prec_dobra = [v[1] / v[0] for v in por_dobra.values()]
            linhas.append({
                "h": h, "model": m, "budget": f"k={valor}" if tipo == "k" else f"{round(valor*100)}% dos calmos",
                "budget_type": tipo, "budget_value": valor,
                "supported_per_month": apoiados / calmos.groupby(["test_year", "mi"]).ngroups,
                "precision_at_k": acertos / apoiados,
                "precision_fold_min": min(prec_dobra), "precision_fold_max": max(prec_dobra),
                "recall_at_k": acertos / total_onsets.sum(),
                "onset_base_rate_calm": total_onsets.sum() / len(calmos)})

tab = pd.DataFrame(linhas)
tab.to_csv(OUT_DIR / "a6_orcamento_calmos.csv", index=False)
mostra = tab.copy()
mostra["model"] = mostra["model"].map(NOMES)
for c in ("precision_at_k", "precision_fold_min", "precision_fold_max", "recall_at_k", "onset_base_rate_calm"):
    mostra[c] = (100 * mostra[c]).round(1)
mostra["supported_per_month"] = mostra["supported_per_month"].round(1)
for h, g in mostra.groupby("h"):
    print(f"\n=== h = {h} (emissão no início de t+2), taxa de onset entre calmos "
          f"{g['onset_base_rate_calm'].iloc[0]}% ===")
    print(g.pivot_table(index="model", columns="budget", values="precision_at_k", sort=False).to_string())
    print("recall@k:")
    print(g.pivot_table(index="model", columns="budget", values="recall_at_k", sort=False).to_string())
