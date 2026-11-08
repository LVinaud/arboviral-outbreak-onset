"""A9. SHAP por família só nas linhas de onset (dengue, inc100, h = 1, RF).

Usa os random forests salvos pelo 03 (data/train/models, um por
dobra) e reconstrói as features executando as células do 03_train, como o
04_results faz (o notebook não é alterado). O agrupamento em famílias é o da
célula 51 do 04_results, executada como está. Antes do SHAP, confere que o
modelo carregado reproduz as probabilidades salvas.

Subconjuntos por dobra (referência = rótulo em t, como no paper):
  agregado      amostra de 1500 linhas de teste (random_state=0, como o paper)
  onset         todas as linhas calmas em t com surto em t+1
  continuação   todas as linhas em surto em t e em t+1
  onset (t-1)   calmas em t-1 com surto em t+1 (referência de tempo real)
Participação de uma família = soma de |SHAP| médio das suas features / total.
"""
import json
import os
import time
import warnings

import joblib
import numpy as np
import pandas as pd
import shap

from comum import OUT_DIR, ROOT, carregar

warnings.simplefilter("ignore")
NB03 = json.loads((ROOT / "notebooks" / "03_train.ipynb").read_text())
NB04 = json.loads((ROOT / "notebooks" / "04_results.ipynb").read_text())
os.chdir(ROOT / "notebooks")  # o 03 resolve caminhos a partir de Path.cwd().parent
ns = {}
for i in [2, 4, 5, 7, 9]:
    exec("".join(NB03["cells"][i]["source"]), ns)
feats, build_target, y_labels = ns["feats"], ns["build_target"], ns["y_labels"]
FEATURE_COLS_ALL = [c for c in feats.columns if c not in ("cod_ibge", "ano", "mes")]
ns.update({"FEATURE_COLS_ALL": FEATURE_COLS_ALL, "DISEASE": "dengue"})
exec("".join(NB04["cells"][51]["source"]), ns)
GROUP_MAP = ns["GROUP_MAP"]

work = feats.copy()
work["target"] = build_target(y_labels, "dengue", "inc100", 1).values
work = ns["add_target_year"](work, 1).dropna(subset=["target"])
fcols = [c for c in work.columns if c not in ("cod_ibge", "ano", "mes", "target", "target_year")]
assert len(fcols) == 125

estados = carregar(1)[["cod_ibge", "ano", "mes", "s_t", "s_tm1", "y_true", "rf"]]
linhas = []
for ty in (2022, 2023, 2024):
    modelo = joblib.load(ROOT / "data" / "train" / "models" / f"dengue_inc100_h1_rf_{ty}.joblib")
    te = work[work["target_year"] == ty].reset_index(drop=True)
    te = te.merge(estados, on=["cod_ibge", "ano", "mes"], how="left", validate="1:1")
    X = te[fcols].fillna(0)
    proba = modelo.predict_proba(X)[:, 1]
    diff = np.abs(proba - te["rf"].values).max()
    assert diff < 1e-9, f"modelo de {ty} não reproduz as predições salvas ({diff})"
    assert (te["target"].astype(int).values == te["y_true"].values).all()
    subconjuntos = {
        "aggregate (sample 1500)": X.sample(min(1500, len(X)), random_state=0).index,
        "onset (ref t)": te.index[(te["s_t"] == 0) & (te["y_true"] == 1)],
        "continuation (ref t)": te.index[(te["s_t"] == 1) & (te["y_true"] == 1)],
        "onset (ref t-1)": te.index[(te["s_tm1"] == 0) & (te["y_true"] == 1)],
    }
    explicador = shap.TreeExplainer(modelo)
    for nome, idx in subconjuntos.items():
        t0 = time.time()
        v = explicador.shap_values(X.loc[idx], check_additivity=False)
        arr = v[..., 1] if isinstance(v, np.ndarray) and v.ndim == 3 else v[1]
        imp = pd.Series(np.abs(arr).mean(0), index=fcols)
        share = imp.groupby(pd.Series(GROUP_MAP)[fcols].values).sum() / imp.sum()
        for familia, valor in share.items():
            linhas.append({"test_year": ty, "subset": nome, "n_rows": len(idx),
                           "group": familia, "shap_share": float(valor)})
        print(f"{ty} {nome:<24} {len(idx):>5} linhas [{time.time()-t0:.0f}s]", flush=True)

tab = pd.DataFrame(linhas)
tab.to_csv(OUT_DIR / "a9_shap_onset_por_dobra.csv", index=False)
resumo = (tab.groupby(["subset", "group"])["shap_share"].agg(["mean", "min", "max"])
          .reset_index())
resumo.to_csv(OUT_DIR / "a9_shap_onset.csv", index=False)
larga = resumo.pivot(index="group", columns="subset", values="mean")
larga = larga[["aggregate (sample 1500)", "onset (ref t)", "onset (ref t-1)", "continuation (ref t)"]]
print((100 * larga.sort_values("aggregate (sample 1500)", ascending=False)).round(1).to_string())
