"""B1. 2025 como quarto ano de teste: treino com alvos até 2024, teste com alvos em 2025.

Mesma configuração do 03 (janela expansiva pelo ano do alvo, mesmos modelos e
hiperparâmetros). As dobras 2022-2024 vêm das predições do 03 (o retreino as
reproduz exatamente, ver treino.conferir_reproducao); só a dobra de 2025 é
treinada aqui. O 2025 não entrou em nenhuma decisão de desenho: features,
definições, hiperparâmetros e o limiar de 0,5 foram fixados olhando só
2022-2024. O SINAN 2025 estava em FINAIS (consolidado) na coleta de 2026-09-09.

Escopo: dengue; inc100 e canal; h = 1 a 6; RF, XGBoost, LightGBM e regressão
logística, mais persistência (t e t-1) e climatologia (mês do alvo).

Saídas:
  b1_pred_dengue_<def>_h<h>.parquet  predições largas das 4 dobras
  b1_dobra_2025.csv                  métricas por dobra (agregado, onset, continuação)
  b1_dobra_2025_ic.csv               2025 contra 2022-2024 com IC 95% por bootstrap de
                                     município: AUROC/AUPRC agregado, de onset e de
                                     continuação (referência t-1, data de emissão)
  b1_orcamento_2025.csv              precisão ao apoiar 5% dos calmos em t-1, por dobra
"""
import time

import numpy as np
import pandas as pd

from b_comum import enriquecer, metricas_por_dobra
from comum import OUT_DIR, SEED, carregar, carregar_rotulos, resumo_metrica
from treino import montar, treinar_dobra

MODELOS = ["rf", "xgb", "lgbm", "logreg"]
TODOS = MODELOS + ["persistence", "persistence_tm1", "climatology_corr"]
COLS = ["cod_ibge", "ano", "mes", "mi", "y_true", "test_year"] + MODELOS


def precisao_5pct(p, modelo, sementes):
    """Precisão ao apoiar os 5% de calmos (em t-1) de maior escore em cada mês."""
    calmos = p[p["s_tm1"] == 0]
    out = {}
    for ty, g_ty in calmos.groupby("test_year"):
        acertos = apoiados = 0.0
        for s in sementes:
            rng = np.random.default_rng(s)
            for _, g in g_ty.groupby("mi"):
                k = max(1, int(round(0.05 * len(g))))
                ordem = np.lexsort((rng.random(len(g)), -g[modelo].values))
                acertos += g["y_true"].values[ordem[:k]].sum() / len(sementes)
                apoiados += k / len(sementes)
        out[ty] = (acertos, apoiados, g_ty["y_true"].mean())
    return out


res, ic, orc = [], [], []
for definition in ("inc100", "canal"):
    lab = carregar_rotulos("dengue", definition)
    for h in range(1, 7):
        t0 = time.time()
        work = montar("dengue", definition, h)
        nova = treinar_dobra(work, 2025, MODELOS)
        antigas = carregar(h, "dengue", definition)[COLS]
        p = enriquecer(pd.concat([antigas, nova[COLS]], ignore_index=True), lab, h)
        p.to_parquet(OUT_DIR / f"b1_pred_dengue_{definition}_h{h}.parquet")
        m = metricas_por_dobra(p, TODOS)
        m["definition"], m["h"] = definition, h
        res.append(m)
        for periodo, anos in (("2022-2024", [2022, 2023, 2024]), ("2025", [2025])):
            q = p[p["test_year"].isin(anos)]
            for recorte, mask in (("pooled", np.ones(len(q), bool)),
                                  ("onset_ref_tm1", (q["s_tm1"] == 0).values),
                                  ("continuation_ref_tm1", (q["s_tm1"] == 1).values),
                                  ("onset_ref_t", (q["s_t"] == 0).values)):
                for mod in MODELOS + ["climatology_corr"]:
                    r = resumo_metrica(q, mod, mask)
                    if r is not None:
                        ic.append({"definition": definition, "h": h, "period": periodo,
                                   "subset": recorte, "model": mod, **r})
        for mod in ("rf", "xgb", "lgbm", "climatology_corr"):
            sementes = range(SEED, SEED + 100) if mod == "climatology_corr" else [SEED]
            for ty, (ac, ap_, taxa) in precisao_5pct(p, mod, sementes).items():
                orc.append({"definition": definition, "h": h, "model": mod, "test_year": ty,
                            "hits": ac, "supported": ap_, "precision_at_5pct": ac / ap_,
                            "onset_rate_calm": taxa})
        print(f"{definition} h={h}: 2025 treinado e avaliado [{time.time()-t0:.0f}s]", flush=True)

tab = pd.concat(res, ignore_index=True)
tab.to_csv(OUT_DIR / "b1_dobra_2025.csv", index=False)
pd.DataFrame(ic).to_csv(OUT_DIR / "b1_dobra_2025_ic.csv", index=False)
pd.DataFrame(orc).to_csv(OUT_DIR / "b1_orcamento_2025.csv", index=False)

mostra = pd.DataFrame(ic)
mostra = mostra[mostra["model"].isin(["rf", "xgb", "climatology_corr"])]
mostra["auroc [IC]"] = mostra.apply(
    lambda r: f"{r.auroc:.3f} [{r.auroc_ci_lo:.3f}, {r.auroc_ci_hi:.3f}]", axis=1)
print(mostra.pivot_table(index=["definition", "h", "subset", "model"], columns="period",
                         values="auroc [IC]", aggfunc="first").to_string())
