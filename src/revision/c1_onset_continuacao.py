"""C1. Onset e continuação por horizonte, com as duas referências de estado.

Dengue, inc100, dobras 2022-2024, h = 1 a 6. Para cada referência r:
  t    o mês que a linha lê (a referência da versão submetida do artigo; na
       data de emissão esse mês ainda não está consolidado)
  t-1  o último mês consolidado na data de emissão (tempo real)
os subconjuntos são
  onset         calmo em r; positivo = surto em t+h
  continuação   em surto em r; positivo = surto em t+h

Métricas, por subconjunto e modelo:
  taxa de base      positivos / linhas do subconjunto (juntando as dobras)
  recall, precisão  limiar 0,5, juntando as dobras (convenção da Tabela 2)
  AUROC, AUPRC      média das dobras (convenção da Tabela 1)
  IC 95%            bootstrap de municípios, 1000 réplicas, seed fixa
  faixa             mínimo e máximo entre as 3 dobras

A persistência em t-1 é constante dentro dos subconjuntos com referência t-1
(0 nos calmos, 1 nos em surto): AUROC 0,5 e AUPRC igual à taxa de base por
construção, recall 0 no onset e 100 na continuação.

Também decompõe os onsets de tempo real (referência t-1): quantos já estavam em
surto em t, ou em t+1 quando t+1 vem antes do alvo (h >= 2), isto é, começaram
antes da emissão sem estarem consolidados nela; e o recall nos onsets "limpos".
"""
import numpy as np
import pandas as pd

from comum import (OUT_DIR, carregar, checar_metricas, fracao_bootstrap,
                   pesos_por_linha, resumo_metrica)

MODELOS = ["rf", "xgb", "lgbm", "logreg", "climatology_corr", "persistence_tm1", "persistence"]
checar_metricas()

linhas, limpos = [], []
for h in range(1, 7):
    df = carregar(h)
    W = pesos_por_linha(df)
    pos = (df["y_true"] == 1).values
    for ref, rotulo in (("s_tm1", "t-1"), ("s_t", "t")):
        for subconj, valor in (("onset", 0), ("continuation", 1)):
            grupo = (df[ref] == valor).values
            base = fracao_bootstrap(df, W, pos, grupo)
            for m in MODELOS:
                alerta = (df[m] >= 0.5).values
                rec = fracao_bootstrap(df, W, alerta, grupo & pos)
                pre = fracao_bootstrap(df, W, pos, grupo & alerta)
                r = resumo_metrica(df, m, grupo)
                linhas.append({
                    "h": h, "ref": rotulo, "subset": subconj, "model": m,
                    "n": int(grupo.sum()), "n_pos": int((grupo & pos).sum()),
                    "base_rate": base["valor"], "base_rate_ci_lo": base["ci_lo"],
                    "base_rate_ci_hi": base["ci_hi"],
                    "recall": rec["valor"], "recall_ci_lo": rec["ci_lo"],
                    "recall_ci_hi": rec["ci_hi"], "recall_fold_min": rec["fold_min"],
                    "recall_fold_max": rec["fold_max"],
                    "n_alerts": int((grupo & alerta).sum()),
                    "precision": pre["valor"], "precision_ci_lo": pre["ci_lo"],
                    "precision_ci_hi": pre["ci_hi"],
                    **{k: r[k] for k in ("auroc", "auroc_ci_lo", "auroc_ci_hi", "auroc_fold_min",
                                         "auroc_fold_max", "auprc", "auprc_ci_lo", "auprc_ci_hi",
                                         "auprc_fold_min", "auprc_fold_max")},
                })
    onset = (df["s_tm1"] == 0).values & pos
    ja = onset & ((df["s_t"] == 1).values | (((df["s_tp1"] == 1).values) if h >= 2 else False))
    limpo = onset & ~ja
    for m in MODELOS:
        alerta = (df[m] >= 0.5).values
        rl = fracao_bootstrap(df, W, alerta, limpo)
        rj = fracao_bootstrap(df, W, alerta, ja)
        limpos.append({"h": h, "model": m, "n_onset": int(onset.sum()),
                       "n_already_started": int(ja.sum()),
                       "pct_already_started": ja.sum() / onset.sum(),
                       "n_clean": int(limpo.sum()),
                       "recall_clean": rl["valor"], "recall_clean_ci_lo": rl["ci_lo"],
                       "recall_clean_ci_hi": rl["ci_hi"],
                       "recall_already_started": rj["valor"]})
    print(f"h={h} ok", flush=True)

tab = pd.DataFrame(linhas)
tab.to_csv(OUT_DIR / "c1_onset_continuacao.csv", index=False)
pd.DataFrame(limpos).to_csv(OUT_DIR / "c1_onsets_limpos.csv", index=False)

# Resumo: onde os dois problemas diferem (RF e XGBoost, referência t-1)
q = tab[(tab["ref"] == "t-1") & tab["model"].isin(["rf", "xgb"])]
larga = q.pivot_table(index=["h", "model"], columns="subset",
                      values=["base_rate", "recall", "precision", "auroc", "auprc"])
print((larga.round(3)).to_string())
