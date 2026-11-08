"""Funções comuns às análises da revisão (ML4H 2026, camera-ready).

Origem: as análises pedidas na revisão do artigo (avaliação por data de emissão,
métricas de onset sem limiar, orçamento de alertas, modelo só de onset, limiares
só com o passado, ano de teste 2025, busca de hiperparâmetros, calibração).

Tudo aqui lê artefatos que o 03_train já gravou e não treina nada:
  data/train/predictions/   predições de cada combinação (doença, definição, h)
  data/master/labels.parquet  os 16 rótulos de surto
As saídas vão para data/train/revision/.

Convenções de tempo: cada linha de predição é indexada pelo mês t lido pelo
modelo; o alvo é o rótulo em t+h. Os modelos veem casos até t-1 e clima até t.
A previsão da linha t é emitida no início do mês t+2, quando os casos de t-1
completam cerca de 60 dias. Assim, h = 1 é um nowcast de um mês já encerrado,
h = 2 prevê o mês que começa na emissão e h = 3 é o primeiro horizonte com um
mês inteiro de antecedência (antecedência efetiva = h - 2 meses).
"""
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import average_precision_score, roc_auc_score

ROOT = Path(__file__).resolve().parents[2]
PRED_DIR = ROOT / "data" / "train" / "predictions"
LABELS_PATH = ROOT / "data" / "master" / "labels.parquet"
OUT_DIR = ROOT / "data" / "train" / "revision"
OUT_DIR.mkdir(parents=True, exist_ok=True)

TEST_YEARS = [2022, 2023, 2024]
LEARNED = ["rf", "xgb", "lgbm", "logreg"]
NOMES = {
    "rf": "Random forest", "xgb": "XGBoost", "lgbm": "LightGBM",
    "logreg": "Logistic regression",
    "persistence": "Persistence (month t)",
    "persistence_tm1": "Persistence (real time, month t-1)",
    "climatology_corr": "Climatology (month t+h)",
}
SEED = 20261012


def mes_idx(ano, mes):
    """Índice mensal contínuo a partir de jan/2015."""
    return (np.asarray(ano) - 2015) * 12 + (np.asarray(mes) - 1)


def carregar_rotulos(disease="dengue", definition="inc100"):
    lab = pd.read_parquet(LABELS_PATH)[["cod_ibge", "ano", "mes", f"{disease}_{definition}"]]
    lab = lab.rename(columns={f"{disease}_{definition}": "y"})
    lab["mi"] = mes_idx(lab["ano"], lab["mes"])
    return lab


def _estado(lab, preds, desloc, nome):
    """Rótulo no mês t + desloc, para cada linha de predição."""
    ref = lab[["cod_ibge", "mi", "y"]].copy()
    ref["mi"] = ref["mi"] - desloc
    out = preds.merge(ref.rename(columns={"y": nome}), on=["cod_ibge", "mi"],
                      how="left", validate="m:1")
    return out


def climatologia_corrigida(lab, preds, h):
    """Frequência histórica de surto no mês do calendário do ALVO (t+h).

    Para a dobra do ano de teste ty, usa só rótulos de meses com ano < ty, que
    são exatamente os alvos das linhas de treino daquela dobra (a partir do
    mês h da série, o primeiro alvo possível). É a mesma conta que o 03_train
    faz em `baseline_climatology`; `carregar` confere que as duas batem.
    """
    preds = preds.copy()
    alvo_mi = preds["mi"] + h
    preds["mes_alvo"] = alvo_mi % 12 + 1
    partes = []
    for ty, grupo in preds.groupby("test_year"):
        hist = lab[(lab["ano"] < ty) & (lab["mi"] >= h)]
        freq = (hist.groupby(["cod_ibge", "mes"])["y"].mean()
                .rename("clim").reset_index().rename(columns={"mes": "mes_alvo"}))
        g = grupo.merge(freq, on=["cod_ibge", "mes_alvo"], how="left", validate="m:1")
        g["clim"] = g["clim"].fillna(0.0)
        partes.append(g)
    out = pd.concat(partes, ignore_index=True)
    return out.drop(columns=["mes_alvo"])


def carregar(h, disease="dengue", definition="inc100"):
    """Predições em formato largo: uma linha por município-mês de teste, uma
    coluna por modelo, mais os estados de referência e as baselines.

    Colunas de estado: s_tm1, s_t, s_tp1 = rótulo em t-1, t, t+1.
    Baselines: persistence (rótulo de t), persistence_tm1 (rótulo de t-1, o
    último mês consolidado na emissão) e climatology_corr (mês do alvo). As duas
    últimas são recalculadas aqui a partir dos rótulos e conferidas contra as
    que o 03_train gravou.
    """
    p = pd.read_parquet(PRED_DIR / f"{disease}_{definition}_h{h}.parquet")
    n_modelos = p["model"].nunique()
    larga = (p.pivot_table(index=["cod_ibge", "ano", "mes", "test_year", "y_true"],
                           columns="model", values="proba")
             .reset_index())
    larga.columns.name = None
    assert len(larga) * n_modelos == len(p), "pivot perdeu linhas"
    larga["mi"] = mes_idx(larga["ano"], larga["mes"])
    lab = carregar_rotulos(disease, definition)
    for desloc, nome in ((-1, "s_tm1"), (0, "s_t"), (1, "s_tp1")):
        larga = _estado(lab, larga, desloc, nome)
    # Conferência: o y_true salvo tem de ser o rótulo em t+h.
    chk = _estado(lab, larga[["cod_ibge", "mi"]], h, "y_chk")
    assert (chk["y_chk"].values == larga["y_true"].values).all(), "y_true != rótulo em t+h"
    # As persistências do 03 são exatamente os rótulos de t e de t-1.
    assert (larga["persistence"].values == larga["s_t"].values).all()
    assert (larga["persistence_tm1"].values == larga["s_tm1"].fillna(0).values).all()
    larga = climatologia_corrigida(lab, larga, h)
    assert np.allclose(larga["clim"].values, larga["climatology"].values), \
        "a climatologia do 03 não é a do mês do alvo"
    larga = larga.drop(columns=["climatology"]).rename(columns={"clim": "climatology_corr"})
    larga["h"] = h
    return larga.sort_values(["test_year", "cod_ibge", "mi"]).reset_index(drop=True)


# ---------------------------------------------------------------------------
# Métricas ponderadas e vetorizadas (para o bootstrap por município)
# ---------------------------------------------------------------------------

def _prep(score, y):
    """Ordena por score decrescente e devolve os limites dos grupos de empate."""
    ordem = np.argsort(-score, kind="mergesort")
    s = score[ordem]
    inicio = np.r_[0, np.flatnonzero(np.diff(s) != 0) + 1]
    return ordem, inicio


def auc_ap_ponderados(score, y, W):
    """AUROC e AP (definição do sklearn, com empates) para várias réplicas.

    W: matriz (R, n) de pesos por linha. Devolve dois vetores de tamanho R
    (NaN onde a réplica não tem positivo ou negativo).

    Um grupo de empate sem peso no topo do ranking (a linha de maior escore é
    de um município que a réplica não sorteou) tem precisão 0/0. Como o
    sklearn, ela vale 0 ali; o grupo não tem positivo, então não contribui.
    Sem isso, a AP inteira da réplica vira NaN e a réplica some do intervalo.
    """
    score = np.asarray(score, float)
    y = np.asarray(y, float)
    ordem, inicio = _prep(score, y)
    Wo = W[:, ordem]
    yo = y[ordem]
    Pg = np.add.reduceat(Wo * yo, inicio, axis=1)
    Ng = np.add.reduceat(Wo * (1 - yo), inicio, axis=1)
    totP, totN = Pg.sum(1), Ng.sum(1)
    cumP = np.cumsum(Pg, 1)
    cumN = np.cumsum(Ng, 1)
    antesP = cumP - Pg
    den = cumP + cumN
    prec = np.divide(cumP, den, out=np.zeros_like(cumP), where=den > 0)
    with np.errstate(invalid="ignore", divide="ignore"):
        auroc = (Ng * (antesP + 0.5 * Pg)).sum(1) / (totP * totN)
        ap = (Pg * prec).sum(1) / totP
    ruim = (totP == 0) | (totN == 0)
    auroc[ruim] = np.nan
    ap[ruim] = np.nan
    return auroc, ap


def pesos_bootstrap(municipios, n_rep=1000, seed=SEED):
    """Matriz (n_rep, n_municípios) com quantas vezes cada município foi sorteado."""
    rng = np.random.default_rng(seed)
    m = len(municipios)
    sorteio = rng.integers(0, m, size=(n_rep, m))
    W = np.zeros((n_rep, m))
    np.add.at(W, (np.arange(n_rep)[:, None], sorteio), 1)
    return W


def checar_metricas():
    """Confere a implementação vetorizada contra o sklearn, inclusive com peso
    zero na linha de maior escore."""
    rng = np.random.default_rng(0)
    y = rng.integers(0, 2, 500)
    s = np.round(rng.random(500), 1)  # força empates
    a, p = auc_ap_ponderados(s, y, np.ones((1, 500)))
    assert abs(a[0] - roc_auc_score(y, s)) < 1e-12
    assert abs(p[0] - average_precision_score(y, s)) < 1e-12
    for _ in range(50):
        y = rng.integers(0, 2, 300)
        s = np.round(rng.random(300), 2)
        w = rng.integers(0, 3, 300).astype(float)
        w[np.argmax(s)] = 0
        a, p = auc_ap_ponderados(s, y, w[None, :])
        assert abs(a[0] - roc_auc_score(y, s, sample_weight=w)) < 1e-12
        assert abs(p[0] - average_precision_score(y, s, sample_weight=w)) < 1e-12


def resumo_metrica(df, modelo, mascara, n_rep=1000, seed=SEED):
    """AUROC/AUPRC de um modelo num subconjunto de linhas.

    Ponto: média das dobras (como a Tabela 1). Faixa: mín e máx entre dobras.
    IC 95%: bootstrap por município, mesmo sorteio de municípios em todas as
    dobras, métrica recalculada por dobra e depois promediada.
    """
    sub = df[mascara]
    municipios = np.sort(df["cod_ibge"].unique())
    Wm = pesos_bootstrap(municipios, n_rep, seed)
    pos = {c: i for i, c in enumerate(municipios)}
    por_dobra, boot_auc, boot_ap = [], [], []
    for ty, g in sub.groupby("test_year"):
        y = g["y_true"].values
        if y.min() == y.max():
            continue
        idx = g["cod_ibge"].map(pos).values
        a1, p1 = auc_ap_ponderados(g[modelo].values, y, np.ones((1, len(g))))
        por_dobra.append((ty, a1[0], p1[0], len(g), int(y.sum())))
        a, p = auc_ap_ponderados(g[modelo].values, y, Wm[:, idx])
        boot_auc.append(a)
        boot_ap.append(p)
    if not por_dobra:
        return None
    pd_ = np.array([r[1:3] for r in por_dobra])
    ba = np.vstack(boot_auc).mean(0)
    bp = np.vstack(boot_ap).mean(0)
    n = sum(r[3] for r in por_dobra)
    npos = sum(r[4] for r in por_dobra)
    return {
        "n": n, "n_pos": npos, "prevalence": npos / n,
        "auroc": pd_[:, 0].mean(), "auroc_ci_lo": np.nanpercentile(ba, 2.5),
        "auroc_ci_hi": np.nanpercentile(ba, 97.5),
        "auroc_fold_min": pd_[:, 0].min(), "auroc_fold_max": pd_[:, 0].max(),
        "auprc": pd_[:, 1].mean(), "auprc_ci_lo": np.nanpercentile(bp, 2.5),
        "auprc_ci_hi": np.nanpercentile(bp, 97.5),
        "auprc_fold_min": pd_[:, 1].min(), "auprc_fold_max": pd_[:, 1].max(),
        "folds": len(por_dobra),
    }


def fracao_bootstrap(df, W, num, den):
    """num/den (booleanos por linha) juntando as dobras, IC por bootstrap de
    município (W: pesos por linha, já expandidos) e faixa entre dobras."""
    num = np.asarray(num, float)
    den = np.asarray(den, float)
    if den.sum() == 0:
        return dict(valor=np.nan, ci_lo=np.nan, ci_hi=np.nan, fold_min=np.nan,
                    fold_max=np.nan, n_den=0)
    ponto = (num * den).sum() / den.sum()
    with np.errstate(invalid="ignore", divide="ignore"):
        boot = (W * num * den).sum(1) / (W * den).sum(1)
    dobras = []
    for ty in sorted(df["test_year"].unique()):
        g = (df["test_year"] == ty).values
        if den[g].sum():
            dobras.append((num[g] * den[g]).sum() / den[g].sum())
    return dict(valor=ponto, ci_lo=np.nanpercentile(boot, 2.5),
                ci_hi=np.nanpercentile(boot, 97.5), fold_min=min(dobras),
                fold_max=max(dobras), n_den=int(den.sum()))


def pesos_por_linha(df, n_rep=1000, seed=SEED):
    """Pesos do bootstrap de municípios expandidos para as linhas de `df`."""
    municipios = np.sort(df["cod_ibge"].unique())
    idx = df["cod_ibge"].map({c: i for i, c in enumerate(municipios)}).values
    return pesos_bootstrap(municipios, n_rep, seed)[:, idx]


if __name__ == "__main__":
    checar_metricas()
    print("métricas vetorizadas conferem com o sklearn")
