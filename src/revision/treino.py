"""Treino do Bloco B do rebuttal, com a mesma configuração do paper.

As features vêm da execução literal das células 2, 4, 5, 7 e 9 do
03_train.ipynb (como faz o 04_results), sem alterar o notebook. Os modelos são
cópias exatas de `model_factories` (03_train, célula 14, linhas 40-55),
inclusive o scale_pos_weight do XGBoost calculado em cada treino (linhas 96-98).
`conferir_reproducao()` prova que isto reproduz as predições salvas pelo 03.
"""
import json
import os
import warnings

import lightgbm as lgb
import numpy as np
import pandas as pd
import xgboost as xgb
from sklearn.ensemble import RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from comum import PRED_DIR, ROOT, mes_idx

warnings.simplefilter("ignore")
NAO_FEATURES = ["cod_ibge", "ano", "mes", "target", "target_year"]


def _carregar_03():
    nb = json.loads((ROOT / "notebooks" / "03_train.ipynb").read_text())
    ns = {}
    antes = os.getcwd()
    os.chdir(ROOT / "notebooks")
    try:
        for i in [2, 4, 5, 7, 9]:
            exec("".join(nb["cells"][i]["source"]), ns)
    finally:
        os.chdir(antes)
    return ns


NS = _carregar_03()
FEATS = NS["feats"]
Y_LABELS = NS["y_labels"]          # rótulos originais (labels.parquet)
add_target_year = NS["add_target_year"]
FEAT_COLS = [c for c in FEATS.columns if c not in ("cod_ibge", "ano", "mes")]
assert len(FEAT_COLS) == 125


def fabricas():
    """Configuração do paper (03_train, célula 14)."""
    return {
        "rf": lambda: RandomForestClassifier(n_estimators=200, min_samples_leaf=20,
                                             class_weight="balanced", n_jobs=-1, random_state=42),
        "lgbm": lambda: lgb.LGBMClassifier(n_estimators=300, num_leaves=63, learning_rate=0.05,
                                           class_weight="balanced", n_jobs=-1, verbose=-1,
                                           random_state=42),
        "xgb": lambda: xgb.XGBClassifier(n_estimators=300, max_depth=6, learning_rate=0.05,
                                         subsample=0.8, colsample_bytree=0.8, tree_method="hist",
                                         n_jobs=-1, eval_metric="aucpr", random_state=42),
        "logreg": lambda: Pipeline([("imp", SimpleImputer(strategy="median")),
                                    ("sc", StandardScaler()),
                                    ("clf", LogisticRegression(class_weight="balanced",
                                                               max_iter=2000, random_state=42))]),
    }


def montar(disease, definition, h, rotulos=None):
    """Matriz de trabalho: features de t, alvo em t+h, ano do alvo.

    `rotulos` permite trocar a tabela de rótulos (B3); por padrão, a do paper.
    """
    rotulos = Y_LABELS if rotulos is None else rotulos
    work = FEATS.copy()
    work["target"] = NS["build_target"](rotulos, disease, definition, h).values
    work = add_target_year(work, h).dropna(subset=["target"])
    work["target"] = work["target"].astype(int)
    work["mi"] = mes_idx(work["ano"], work["mes"])
    return work


def ajustar_prever(nome, Xtr, ytr, Xte, fabrica=None):
    mdl = (fabrica or fabricas()[nome])()
    if nome == "xgb" or isinstance(mdl, xgb.XGBClassifier):
        npos = int(ytr.sum())
        mdl.set_params(scale_pos_weight=(len(ytr) - npos) / max(npos, 1))
    mdl.fit(Xtr, ytr)
    return mdl.predict_proba(Xte)[:, 1]


def treinar_dobra(work, ty, modelos, mascara_treino=None, fabricas_=None):
    """Treina com target_year < ty (opcionalmente só nas linhas de `mascara_treino`)
    e prevê as linhas com target_year == ty. Devolve um DataFrame largo."""
    tr = work["target_year"] < ty
    if mascara_treino is not None:
        tr &= mascara_treino
    te = work["target_year"] == ty
    Xtr, ytr = work.loc[tr, FEAT_COLS].fillna(0), work.loc[tr, "target"]
    Xte = work.loc[te, FEAT_COLS].fillna(0)
    out = work.loc[te, ["cod_ibge", "ano", "mes", "mi", "target"]].rename(columns={"target": "y_true"})
    out["test_year"] = ty
    for m in modelos:
        fab = (fabricas_ or {}).get(m)
        out[m] = ajustar_prever(m, Xtr, ytr, Xte, fab)
    return out.reset_index(drop=True)


def conferir_reproducao():
    """RF e XGBoost, dengue/inc100/h=1, dobra 2024: devem bater com o 03."""
    work = montar("dengue", "inc100", 1)
    nova = treinar_dobra(work, 2024, ["rf", "xgb"])
    salva = pd.read_parquet(PRED_DIR / "dengue_inc100_h1.parquet")
    salva = salva[salva["test_year"] == 2024].pivot_table(
        index=["cod_ibge", "ano", "mes"], columns="model", values="proba").reset_index()
    m = nova.merge(salva, on=["cod_ibge", "ano", "mes"], suffixes=("", "_paper"))
    assert len(m) == len(nova)
    difs = {k: float(np.abs(m[k] - m[f"{k}_paper"]).max()) for k in ("rf", "xgb")}
    print("diferença máxima contra as predições do 03:", difs)
    assert max(difs.values()) < 1e-9, "o retreino não reproduz o 03"
    return difs


if __name__ == "__main__":
    conferir_reproducao()
