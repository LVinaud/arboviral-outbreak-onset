"""Avaliação comum aos itens do Bloco B (predições recém-treinadas)."""
import numpy as np
import pandas as pd
from sklearn.metrics import average_precision_score, roc_auc_score

from comum import _estado, climatologia_corrigida


def enriquecer(pred, lab, h):
    """Acrescenta estados de referência (rótulo em t-1, t) e as baselines
    (persistência em t e em t-1, climatologia corrigida) a predições largas.
    `lab` precisa ter cod_ibge, ano, mes, mi, y (os rótulos usados no treino)."""
    p = pred.copy()
    for desloc, nome in ((-1, "s_tm1"), (0, "s_t")):
        p = _estado(lab, p, desloc, nome)
    p["persistence"] = p["s_t"].astype(float)
    p["persistence_tm1"] = p["s_tm1"].astype(float)
    p = climatologia_corrigida(lab, p, h).rename(columns={"clim": "climatology_corr"})
    return p


def _auc(y, s):
    return roc_auc_score(y, s) if len(np.unique(y)) > 1 else np.nan


def _ap(y, s):
    return average_precision_score(y, s) if len(np.unique(y)) > 1 else np.nan


def metricas_por_dobra(p, modelos):
    """Uma linha por (dobra, modelo): agregado, onset e continuação."""
    linhas = []
    for ty, g in p.groupby("test_year"):
        for m in modelos:
            alerta = g[m] >= 0.5
            r = {"test_year": ty, "model": m, "n": len(g), "prevalence": g["y_true"].mean(),
                 "auroc": _auc(g["y_true"], g[m]), "auprc": _ap(g["y_true"], g[m])}
            for ref in ("s_t", "s_tm1"):
                suf = "ref_t" if ref == "s_t" else "ref_tm1"
                calmo = g[ref] == 0
                cont = g[ref] == 1
                r[f"onset_prev_{suf}"] = g.loc[calmo, "y_true"].mean()
                r[f"onset_auroc_{suf}"] = _auc(g.loc[calmo, "y_true"], g.loc[calmo, m])
                r[f"onset_auprc_{suf}"] = _ap(g.loc[calmo, "y_true"], g.loc[calmo, m])
                r[f"recall_onset_{suf}"] = alerta[calmo & (g["y_true"] == 1)].mean()
                r[f"recall_cont_{suf}"] = alerta[cont & (g["y_true"] == 1)].mean()
                r[f"false_alarm_calm_{suf}"] = alerta[calmo & (g["y_true"] == 0)].mean()
                r[f"n_onset_{suf}"] = int((calmo & (g["y_true"] == 1)).sum())
            linhas.append(r)
    return pd.DataFrame(linhas)
