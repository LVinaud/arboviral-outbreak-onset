"""C2. Calibração isotônica temporal dos escores (dengue, inc100, h = 1 e 3).

Para cada ano de teste ty, a regressão isotônica é ajustada nas predições fora
da amostra do ano anterior (ty-1), feitas por um modelo treinado com alvos
anteriores a ty-1, e aplicada às predições do ano de teste. Nada do ano de
teste entra no ajuste. Para ty = 2023 e 2024 essas predições já existem (são as
do 03 para 2022 e 2023); para ty = 2022 o modelo de 2021 é treinado aqui.

Saídas:
  c2_calibracao_resumo.csv   Brier, ganho sobre a taxa de base, ECE, maior desvio,
                             desvio médio entre 0,2 e 0,8, AUROC/AUPRC; bruto e calibrado
  c2_confiabilidade.csv      curva de confiabilidade (10 faixas de largura igual)
  c2_limiares_acao.csv       entre os municípios calmos no último mês consolidado
                             (t-1): com a regra de agir quando p > C/L, quantos
                             alertas por mês e que fração deles vira surto, para
                             alguns valores de C/L, com os escores calibrados
"""
import numpy as np
import pandas as pd
from sklearn.isotonic import IsotonicRegression
from sklearn.metrics import average_precision_score, roc_auc_score

from comum import OUT_DIR, carregar
from treino import montar, treinar_dobra

MODELOS = ["rf", "xgb", "lgbm"]
LIMIARES = [0.1, 0.2, 0.3, 0.5]
BINS = 10


def confiabilidade(p, y):
    edges = np.linspace(0, 1, BINS + 1)
    idx = np.clip(np.digitize(p, edges) - 1, 0, BINS - 1)
    out = []
    for b in range(BINS):
        sel = idx == b
        if sel.any():
            out.append({"bin": b, "predicted": p[sel].mean(), "observed": y[sel].mean(),
                        "n": int(sel.sum())})
    return pd.DataFrame(out)


resumo, curvas, acao = [], [], []
for h in (1, 3):
    df = carregar(h)
    # Predições fora da amostra de 2021, para calibrar a dobra de 2022.
    work = montar("dengue", "inc100", h)
    p2021 = treinar_dobra(work, 2021, MODELOS)
    cal = pd.concat([p2021[["test_year", "y_true"] + MODELOS],
                     df[df["test_year"] < 2024][["test_year", "y_true"] + MODELOS]],
                    ignore_index=True)
    for m in MODELOS:
        partes = []
        for ty in (2022, 2023, 2024):
            ajuste = cal[cal["test_year"] == ty - 1]
            iso = IsotonicRegression(y_min=0, y_max=1, out_of_bounds="clip")
            iso.fit(ajuste[m].values, ajuste["y_true"].values)
            g = df[df["test_year"] == ty][["test_year", "mi", "y_true", "s_tm1", m]].copy()
            g["cal"] = iso.predict(g[m].values)
            partes.append(g)
        g = pd.concat(partes, ignore_index=True)
        y = g["y_true"].values
        referencia = float(((y.mean() - y) ** 2).mean())
        for versao, col in (("raw", m), ("calibrated", "cal")):
            p = g[col].values
            curva = confiabilidade(p, y)
            curva["gap"] = curva["observed"] - curva["predicted"]
            meio = curva[(curva["predicted"] >= 0.2) & (curva["predicted"] <= 0.8)]
            brier = float(((p - y) ** 2).mean())
            resumo.append({
                "h": h, "model": m, "version": versao, "brier": brier,
                "brier_skill_vs_base_rate": 1 - brier / referencia,
                "ece": float((curva["gap"].abs() * curva["n"]).sum() / curva["n"].sum()),
                "max_abs_gap": float(curva["gap"].abs().max()),
                "mean_gap_0.2_to_0.8": float(meio["gap"].mean()),
                "auroc": np.mean([roc_auc_score(q["y_true"], q[col]) for _, q in g.groupby("test_year")]),
                "auprc": np.mean([average_precision_score(q["y_true"], q[col])
                                  for _, q in g.groupby("test_year")]),
                "mean_pred_calm_tm1": float(p[g["s_tm1"].values == 0].mean()),
                "onset_rate_calm_tm1": float(y[g["s_tm1"].values == 0].mean()),
            })
            curva.insert(0, "version", versao)
            curva.insert(0, "model", m)
            curva.insert(0, "h", h)
            curvas.append(curva)
        calmos = g[g["s_tm1"] == 0]
        meses = calmos.groupby(["test_year", "mi"]).ngroups
        for lim in LIMIARES:
            alerta = calmos["cal"].values > lim
            yc = calmos["y_true"].values
            acao.append({"h": h, "model": m, "threshold_C_over_L": lim,
                         "alerts_per_month": alerta.sum() / meses,
                         "share_of_calm_flagged": alerta.mean(),
                         "precision": yc[alerta].mean() if alerta.any() else np.nan,
                         "recall_onsets": alerta[yc == 1].mean(),
                         "calm_per_month": len(calmos) / meses,
                         "onset_rate_calm": yc.mean()})
    print(f"h={h} ok", flush=True)

res = pd.DataFrame(resumo)
res.to_csv(OUT_DIR / "c2_calibracao_resumo.csv", index=False)
pd.concat(curvas, ignore_index=True).to_csv(OUT_DIR / "c2_confiabilidade.csv", index=False)
pd.DataFrame(acao).to_csv(OUT_DIR / "c2_limiares_acao.csv", index=False)
print(res.round(4).to_string(index=False))
print(pd.DataFrame(acao).round(3).to_string(index=False))
