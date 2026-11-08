"""B3. Rótulos canal e zscore com limiares calculados só com o passado.

Para cada dobra de teste ty, os rótulos de TODAS as linhas (treino e teste) são
recalculados com uma base que só usa anos anteriores a ty:
  1. Anos epidêmicos, regra objetiva no lugar da lista fixada à mão:
     um ano Y < ty é epidêmico se o total estadual de casos em Y passar de 1,5
     vez a mediana dos totais anuais de todos os anos anteriores a ty.
  2. Mediana, média e desvio-padrão por (município, mês do calendário) nos anos
     anteriores a ty que não são epidêmicos.
  3. As mesmas fórmulas do 02_master (célula 62): canal = casos > mediana +
     1.96 sigma; zscore = (casos - média)/sigma > 2, ou casos > média quando
     sigma = 0; ambos com o piso de 5 casos.
Depois retreina RF, XGBoost e logística em cada dobra com esses rótulos e compara
com os rótulos do paper (predições salvas da rodada do paper).
Dengue, h = 1 e 2, dobras 2022-2024.
"""
import numpy as np
import pandas as pd
from sklearn.metrics import cohen_kappa_score

from b_comum import enriquecer, metricas_por_dobra
from comum import OUT_DIR, ROOT, carregar, mes_idx
from treino import Y_LABELS, montar, treinar_dobra

MIN_CASES = 5
FATOR = 1.5
MODELOS = ["rf", "xgb", "logreg"]
TODOS = MODELOS + ["persistence", "persistence_tm1", "climatology_corr"]

master = pd.read_parquet(ROOT / "data" / "master" / "municipio_mes.parquet",
                         columns=["cod_ibge", "ano", "mes", "dengue_casos"])
master = master.sort_values(["cod_ibge", "ano", "mes"]).reset_index(drop=True)
base_lab = Y_LABELS.sort_values(["cod_ibge", "ano", "mes"]).reset_index(drop=True)
assert (master[["cod_ibge", "ano", "mes"]].values == base_lab[["cod_ibge", "ano", "mes"]].values).all()
casos = master["dengue_casos"].fillna(0)
totais = casos.groupby(master["ano"]).sum()


def rotulos_passado(ty):
    anos = totais[totais.index < ty]
    epid = sorted(anos[anos > FATOR * anos.median()].index.tolist())
    usar = (master["ano"] < ty) & ~master["ano"].isin(epid)
    stats = (pd.DataFrame({"cod_ibge": master["cod_ibge"], "mes": master["mes"], "c": casos})[usar]
             .groupby(["cod_ibge", "mes"])["c"].agg(med="median", media="mean", sd="std").reset_index())
    stats["sd"] = stats["sd"].fillna(0)
    b = master[["cod_ibge", "mes"]].merge(stats, on=["cod_ibge", "mes"], how="left", validate="m:1")
    obs, med, media, sd = casos.values, b["med"].values, b["media"].values, b["sd"].values
    enough = obs >= MIN_CASES
    canal = (obs > med + 1.96 * sd) & enough
    with np.errstate(divide="ignore", invalid="ignore"):
        z = np.where(sd > 0, (obs - media) / np.where(sd > 0, sd, np.nan) > 2, obs > media)
    zscore = z & enough
    lab = base_lab.copy()
    lab["dengue_canal"] = canal.astype(int)
    lab["dengue_zscore"] = zscore.astype(int)
    return lab, epid


print("totais estaduais de casos de dengue por ano:")
print(totais.astype(int).to_string())

metricas, mudancas, epidemicos = [], [], []
for ty in (2022, 2023, 2024):
    lab_ty, epid = rotulos_passado(ty)
    epidemicos.append({"test_year": ty, "epidemic_years_rule": epid,
                       "epidemic_years_paper": [2015, 2019, 2024, 2025],
                       "median_prior_total": float(totais[totais.index < ty].median())})
    teste = lab_ty["ano"] == ty
    for d in ("canal", "zscore"):
        novo, velho = lab_ty.loc[teste, f"dengue_{d}"], base_lab.loc[teste, f"dengue_{d}"]
        mudancas.append({"test_year": ty, "definition": d, "prev_paper": velho.mean(),
                         "prev_past_only": novo.mean(), "labels_changed": int((novo != velho).sum()),
                         "pct_changed": (novo != velho).mean(),
                         "kappa": cohen_kappa_score(novo, velho)})
        for h in (1, 2):
            work = montar("dengue", d, h, rotulos=lab_ty)
            pred = treinar_dobra(work, ty, MODELOS)
            lab_simples = lab_ty[["cod_ibge", "ano", "mes", f"dengue_{d}"]].rename(columns={f"dengue_{d}": "y"})
            lab_simples["mi"] = mes_idx(lab_simples["ano"], lab_simples["mes"])
            p = enriquecer(pred, lab_simples, h)
            m = metricas_por_dobra(p, TODOS)
            m["definition"], m["h"], m["labels"] = d, h, "past-only"
            metricas.append(m)
            print(f"{ty} {d} h={h} ok", flush=True)

# Rótulos do paper: predições salvas da rodada do paper, mesmas baselines corrigidas.
for d in ("canal", "zscore"):
    for h in (1, 2):
        m = metricas_por_dobra(carregar(h, "dengue", d), TODOS)
        m["definition"], m["h"], m["labels"] = d, h, "paper"
        metricas.append(m)

tab = pd.concat(metricas, ignore_index=True)
tab.to_csv(OUT_DIR / "b3_limiares_passado.csv", index=False)
pd.DataFrame(mudancas).to_csv(OUT_DIR / "b3_mudanca_rotulos.csv", index=False)
pd.DataFrame(epidemicos).to_csv(OUT_DIR / "b3_anos_epidemicos.csv", index=False)
print(pd.DataFrame(epidemicos).to_string(index=False))
print(pd.DataFrame(mudancas).round(3).to_string(index=False))
cols = ["prevalence", "auroc", "auprc", "onset_auroc_ref_t", "onset_auprc_ref_t", "onset_prev_ref_t",
        "recall_onset_ref_t", "recall_cont_ref_t", "false_alarm_calm_ref_t", "onset_auroc_ref_tm1"]
print(tab.groupby(["definition", "h", "model", "labels"], sort=False)[cols].mean().round(3).to_string())
