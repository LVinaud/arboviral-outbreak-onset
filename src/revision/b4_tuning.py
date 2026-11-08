"""B4. Ajuste leve de hiperparâmetros para RF e XGBoost.

Busca aleatória com 20 configurações por modelo (sorteadas uma vez, seed fixa,
as mesmas em todas as dobras). Em cada dobra de teste ty: treino interno com
alvos < ty-1, validação com alvos em ty-1, escolha pela AUPRC de validação;
depois reajuste com todos os alvos < ty e teste em ty. Nada do ano de teste
entra na escolha. Compara com a configuração fixa do paper (predições do B1,
idênticas às do paper). Dengue, inc100, h = 1 e 2, dobras 2022-2024.
"""
import time

import numpy as np
import pandas as pd
import xgboost as xgb
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import average_precision_score

from b_comum import enriquecer, metricas_por_dobra
from comum import OUT_DIR, SEED, carregar_rotulos
from treino import FEAT_COLS, ajustar_prever, montar, treinar_dobra

N_CONFIGS = 20
rng = np.random.default_rng(SEED)
ESPACO = {
    "rf": {"n_estimators": [200, 300], "max_depth": [None, 12, 20],
           "min_samples_leaf": [1, 5, 10, 20, 50], "max_features": ["sqrt", 0.2, 0.4],
           "class_weight": ["balanced", "balanced_subsample", None]},
    "xgb": {"n_estimators": [200, 300, 500], "max_depth": [3, 4, 6, 8],
            "learning_rate": [0.03, 0.05, 0.1], "subsample": [0.6, 0.8, 1.0],
            "colsample_bytree": [0.5, 0.8, 1.0], "min_child_weight": [1, 5, 10]},
}


def sortear(espaco):
    return {k: v[rng.integers(len(v))] for k, v in espaco.items()}


CONFIGS = {m: [sortear(e) for _ in range(N_CONFIGS)] for m, e in ESPACO.items()}


def fabrica(m, cfg):
    if m == "rf":
        return lambda: RandomForestClassifier(**cfg, n_jobs=-1, random_state=42)
    return lambda: xgb.XGBClassifier(**cfg, tree_method="hist", n_jobs=-1,
                                     eval_metric="aucpr", random_state=42)


lab = carregar_rotulos("dengue", "inc100")
escolhas, metricas = [], []
for h in (1, 2):
    work = montar("dengue", "inc100", h)
    partes = []
    for ty in (2022, 2023, 2024):
        tr = work["target_year"] < ty - 1
        va = work["target_year"] == ty - 1
        Xtr, ytr = work.loc[tr, FEAT_COLS].fillna(0), work.loc[tr, "target"]
        Xva, yva = work.loc[va, FEAT_COLS].fillna(0), work.loc[va, "target"]
        melhores = {}
        for m in ("rf", "xgb"):
            t0 = time.time()
            notas = [average_precision_score(yva, ajustar_prever(m, Xtr, ytr, Xva, fabrica(m, c)))
                     for c in CONFIGS[m]]
            # referência: a configuração do paper na mesma validação
            nota_paper = average_precision_score(yva, ajustar_prever(m, Xtr, ytr, Xva))
            i = int(np.argmax(notas))
            melhores[m] = fabrica(m, CONFIGS[m][i])
            escolhas.append({"h": h, "test_year": ty, "model": m, "config": CONFIGS[m][i],
                             "val_auprc_best": notas[i], "val_auprc_paper_config": nota_paper,
                             "val_auprc_median_search": float(np.median(notas))})
            print(f"h={h} {ty} {m}: val AUPRC melhor {notas[i]:.4f} vs paper {nota_paper:.4f} "
                  f"[{time.time()-t0:.0f}s]", flush=True)
        pred = treinar_dobra(work, ty, ["rf", "xgb"],
                             fabricas_={"rf": melhores["rf"], "xgb": melhores["xgb"]})
        partes.append(pred.rename(columns={"rf": "rf_tuned", "xgb": "xgb_tuned"}))
    tun = pd.concat(partes, ignore_index=True)
    fixo = pd.read_parquet(OUT_DIR / f"b1_pred_dengue_inc100_h{h}.parquet")
    fixo = fixo[fixo["test_year"] <= 2024][["cod_ibge", "mi", "rf", "xgb"]]
    p = enriquecer(tun.merge(fixo, on=["cod_ibge", "mi"], validate="1:1"), lab, h)
    m = metricas_por_dobra(p, ["rf", "rf_tuned", "xgb", "xgb_tuned"])
    m["h"] = h
    metricas.append(m)

pd.DataFrame(escolhas).to_csv(OUT_DIR / "b4_configs_escolhidas.csv", index=False)
tab = pd.concat(metricas, ignore_index=True)
tab.to_csv(OUT_DIR / "b4_tuning.csv", index=False)
cols = ["auroc", "auprc", "onset_auroc_ref_t", "onset_auprc_ref_t", "recall_onset_ref_t",
        "recall_cont_ref_t", "false_alarm_calm_ref_t", "onset_auroc_ref_tm1", "onset_auprc_ref_tm1"]
print(tab.groupby(["h", "model"], sort=False)[cols].mean().round(3).to_string())
print(tab.groupby(["h", "model"], sort=False)[["auroc", "onset_auroc_ref_t"]].agg(["min", "max"]).round(3).to_string())
