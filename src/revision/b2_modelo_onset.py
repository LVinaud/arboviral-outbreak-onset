"""B2. Modelo específico de onset.

Para cada referência r (t, como no paper; t-1, tempo real), RF e XGBoost são
treinados só nas linhas de treino calmas em r (mesmas features, hiperparâmetros
e dobras do paper) e avaliados nas linhas de teste calmas em r. Comparação com o
modelo único do paper (treinado em todas as linhas) nas mesmas linhas de teste,
usando as predições do B1 (dobras 2022-2024, idênticas às do paper).
Dengue, inc100, h = 1 e 2.

Métricas: AUROC e AUPRC de onset; recall, falso alarme e precisão a 0.5; e
precisão@5% dos calmos por mês, que independe da calibração. O modelo de onset
vê outra prevalência no treino, então o limiar 0.5 não é comparável entre os dois.
"""
import numpy as np
import pandas as pd
from sklearn.metrics import average_precision_score, roc_auc_score

from comum import OUT_DIR, SEED, carregar_rotulos
from treino import montar, treinar_dobra

lab = carregar_rotulos("dengue", "inc100")
estado = lab[["cod_ibge", "mi", "y"]]
linhas = []
for h in (1, 2):
    work = montar("dengue", "inc100", h)
    for desloc, ref in ((0, "s_t"), (-1, "s_tm1")):
        e = estado.assign(mi=estado["mi"] - desloc).rename(columns={"y": "ref"})
        w = work.merge(e, on=["cod_ibge", "mi"], how="left", validate="m:1")
        w.index = work.index
        calmo = w["ref"] == 0
        unico = pd.read_parquet(OUT_DIR / f"b1_pred_dengue_inc100_h{h}.parquet")
        for ty in (2022, 2023, 2024):
            espec = treinar_dobra(w, ty, ["rf", "xgb"], mascara_treino=calmo)
            espec = espec.merge(e, on=["cod_ibge", "mi"], how="left")
            espec = espec[espec["ref"] == 0]
            base = unico[unico["test_year"] == ty][["cod_ibge", "mi", "rf", "xgb"]]
            m = espec.merge(base, on=["cod_ibge", "mi"], suffixes=("_onset", "_unico"), validate="1:1")
            for modelo in ("rf_onset", "rf_unico", "xgb_onset", "xgb_unico"):
                y, s = m["y_true"], m[modelo]
                alerta = s >= 0.5
                # precisão@5% dos calmos, mês a mês, desempate aleatório com seed
                rng = np.random.default_rng(SEED)
                acertos = apoiados = 0
                for _, g in m.groupby("mi"):
                    k = max(1, int(round(0.05 * len(g))))
                    ordem = np.lexsort((rng.random(len(g)), -g[modelo].values))
                    acertos += g["y_true"].values[ordem[:k]].sum()
                    apoiados += k
                linhas.append({"h": h, "ref": "t" if ref == "s_t" else "t-1", "test_year": ty,
                               "model": modelo, "n_calm": len(m), "onset_rate": y.mean(),
                               "n_train_rows": int((calmo & (w["target_year"] < ty)).sum()) if "onset" in modelo
                               else int((w["target_year"] < ty).sum()),
                               "onset_auroc": roc_auc_score(y, s), "onset_auprc": average_precision_score(y, s),
                               "recall_onset_05": alerta[y == 1].mean(),
                               "false_alarm_05": alerta[y == 0].mean(),
                               "precision_05": y[alerta].mean() if alerta.any() else np.nan,
                               "precision_at_5pct": acertos / apoiados})
            print(f"h={h} ref={ref} {ty} ok", flush=True)

tab = pd.DataFrame(linhas)
tab.to_csv(OUT_DIR / "b2_modelo_onset.csv", index=False)
cols = ["onset_auroc", "onset_auprc", "recall_onset_05", "false_alarm_05", "precision_05", "precision_at_5pct"]
resumo = tab.groupby(["h", "ref", "model"], sort=False)[cols + ["onset_rate"]].mean()
faixa = tab.groupby(["h", "ref", "model"], sort=False)["onset_auprc"].agg(["min", "max"])
print(resumo.join(faixa).round(3).to_string())
