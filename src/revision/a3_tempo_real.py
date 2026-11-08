"""A3. Avaliação em tempo real, sem retreinar.

Convenção de emissão: a previsão da linha t sai no início do mês t+2, quando os
casos de t-1 completam ~60 dias; clima até t. Assim, h = 1 é nowcast de um mês já
encerrado, h = 2 prevê o mês que começa na emissão (sem dado desse mês nem do
anterior) e h = 3 é o primeiro horizonte com um mês inteiro de antecedência.

Parte 1: onset/continuação relativos ao último mês consolidado (t-1), h = 1..6.
  onset = calmo em t-1 e surto em t+h; continuação = surto em t-1 e em t+h.
  Conta quantos desses onsets já estavam em surto em t (ou t+1, quando t+1 é
  anterior ao alvo, isto é, h >= 2): começaram antes da emissão, mas ainda não
  eram visíveis nela.
Parte 2: auditoria das features que podem carregar informação não publicada na
  data de emissão (valores anuais do próprio ano ou de anos posteriores).
"""
import numpy as np
import pandas as pd

from comum import NOMES, OUT_DIR, ROOT, carregar

MODELOS = ["rf", "xgb", "lgbm", "logreg", "persistence_tm1", "climatology_corr"]

# ---------------------------------------------------------------- parte 1
linhas, decomp = [], []
for h in range(1, 7):
    df = carregar(h)
    calmo = df["s_tm1"] == 0
    onset = calmo & (df["y_true"] == 1)
    cont = (df["s_tm1"] == 1) & (df["y_true"] == 1)
    ja_em_t = onset & (df["s_t"] == 1)
    ja_em_tp1 = onset & (df["s_t"] == 0) & (df["s_tp1"] == 1) if h >= 2 else onset & False
    ja_comecou = ja_em_t | ja_em_tp1
    limpo = onset & ~ja_comecou
    alvo = {1: "mes ja encerrado", 2: "mes que comeca na emissao"}.get(
        h, f"{h - 2} mes(es) inteiro(s) a frente")
    decomp.append({"h": h, "alvo_na_emissao": alvo,
                   "n_onset_ref_tm1": int(onset.sum()),
                   "ja_em_surto_em_t": int(ja_em_t.sum()),
                   "ja_em_surto_em_t1_nao_t": int(ja_em_tp1.sum()),
                   "pct_ja_comecou": ja_comecou.sum() / onset.sum(),
                   "n_onset_limpo": int(limpo.sum()),
                   "n_continuacao_ref_tm1": int(cont.sum()),
                   "n_onset_ref_t_paper": int(((df["s_t"] == 0) & (df["y_true"] == 1)).sum())})
    for m in MODELOS:
        alerta = df[m] >= 0.5
        linhas.append({"h": h, "model": m,
                       "recall_onset_ref_tm1": alerta[onset].mean(),
                       "recall_onset_ja_comecou": alerta[ja_comecou].mean() if ja_comecou.any() else np.nan,
                       "recall_onset_limpo": alerta[limpo].mean(),
                       "recall_cont_ref_tm1": alerta[cont].mean(),
                       "falso_alarme_calmos_tm1": alerta[calmo & (df["y_true"] == 0)].mean()})

dec = pd.DataFrame(decomp)
rec = pd.DataFrame(linhas)
dec.to_csv(OUT_DIR / "a3_onsets_ref_tm1.csv", index=False)
rec.to_csv(OUT_DIR / "a3_recall_ref_tm1.csv", index=False)
print(dec.round(3).to_string(index=False))
print()
mostra = rec.copy()
mostra["model"] = mostra["model"].map(NOMES)
for c in mostra.columns[2:]:
    mostra[c] = (100 * mostra[c]).round(1)
print(mostra.to_string(index=False))

# ---------------------------------------------------------------- parte 2
# Para cada fonte anual ou por edição: em que anos ela tem valor publicado e
# como o 02_master leva esse valor para os meses (junção por ano, ffill, bfill).
M = ROOT / "data" / "master"


def anos(arquivo, coluna):
    t = pd.read_parquet(M / arquivo)
    return sorted(t.loc[t[coluna].notna(), "ano"].unique().tolist())


FONTES = [
    # fonte, arquivo, coluna de referência, regra de junção, features, família,
    # defasagem de publicação documentada no repositório
    ("IBGE população", "ibge_wide.parquet", "pop_residente", "ano da linha; 2023 = Censo 2022 (ffill)",
     ["pop_residente", "densidade_hab_km2", "(denominador de *_incid_*)"], "socioeconomic",
     "não documentada (estimativas anuais; Censo 2022 emendado em 2022)"),
    ("IBGE PIB", "ibge_wide.parquet", "pib_mil_reais", "ano da linha; vazio a partir de 2024 (vira 0 no treino)",
     ["pib_per_capita"], "socioeconomic", "não documentada (série termina em 2023)"),
    ("CAPAG", "capag_wide.parquet", "capag", "ano da linha",
     ["capag_* (one-hot)"], "socioeconomic", "não documentada"),
    ("SIM/SINASC (mortalidade materna)", "mortalidade_materna_wide.parquet", "rmm_por_100k_nv", "ano da linha",
     ["rmm_por_100k_nv"], "socioeconomic", "~2 anos para consolidar (01, fontes 6 e SINASC)"),
    ("Vacinação febre amarela", "vacinacao_fa_wide.parquet", "cob_vac_fa_pct", "ano da linha",
     ["cob_vac_fa_pct"], "health services", "não documentada"),
    ("MapBiomas", "mapbiomas_wide.parquet", "pct_floresta", "ano da linha",
     ["pct_floresta", "pct_agricultura", "pct_nao_vegetado", "pct_agua", "pct_natural_nao_florestal"],
     "environment", "não documentada (coleção anual)"),
    ("SINISA (saneamento)", "sinisa_wide.parquet", "iag0001_atend_agua_pct", "edições 2023 e 2024, ffill + bfill até 2015",
     ["iag0001_atend_agua_pct", "ies0001_atend_esgoto_pct", "ies0007_esgoto_tratado_pct",
      "iap0001_vias_pavimentadas_pct"], "sanitation", "edição N publica o ano N-1 (01, fonte SINISA)"),
    ("MUNIC", "munic_wide.parquet", "msau28_pacs", "edições 2018, 2020, 2021, ffill + bfill",
     ["msau*", "mgrd*", "mmam2612_moradia_risco"], "health services / environment", "não documentada"),
    ("Habitação (Censo)", "habitacao_wide.parquet", "num_favelas", "Censo 2010 até 2021, Censo 2022 a partir de 2022",
     ["num_favelas", "pop_favelas"], "socioeconomic", "não documentada"),
]

abl = pd.read_csv(ROOT / "data" / "train" / "tables" / "table_ablation_groups.csv")
abl_media = abl.groupby("group")["delta_auprc"].mean()

aud = []
for fonte, arq, col, regra, feats, familia, defas in FONTES:
    a = anos(arq, col)
    # Ano de referência do valor que cada ano de linha de teste recebe.
    usado = {}
    for y in (2021, 2022, 2023, 2024):
        if "bfill" in regra:
            depois = [x for x in a if x >= y]
            antes = [x for x in a if x <= y]
            usado[y] = antes[-1] if antes else depois[0]
        elif "Censo 2010" in regra:
            usado[y] = 2010 if y < 2022 else 2022
        elif "Censo 2022" in regra and y == 2023:
            usado[y] = 2022
        else:
            usado[y] = y if y in a else None
    olhando_frente = [y for y, u in usado.items() if u is not None and u >= y]
    familias = [f.strip() for f in familia.split("/")]
    aud.append({"fonte": fonte, "features": ", ".join(feats), "familia": familia,
                "anos_publicados": f"{a[0]}-{a[-1]}" if len(a) > 3 else str(a),
                "regra_juncao": regra,
                "ano_do_dado_por_ano_da_linha": "; ".join(f"{y}->{u}" for y, u in usado.items()),
                "linhas_de_teste_com_dado_do_proprio_ano_ou_posterior": ", ".join(map(str, olhando_frente)) or "nenhuma",
                "defasagem_documentada": defas,
                "ablacao_familia_delta_auprc": "; ".join(f"{f}: {abl_media.get(f, np.nan):+.4f}" for f in familias)})

# Fontes mensais com defasagem própria (entram com lag 1, mês t-1).
aud += [
    {"fonte": "SIH-SUS (internações)", "features": "<doença>_internacoes_sih_lag1", "familia": "target history",
     "anos_publicados": "mensal", "regra_juncao": "mês t-1",
     "ano_do_dado_por_ano_da_linha": "mês t-1",
     "linhas_de_teste_com_dado_do_proprio_ano_ou_posterior": "depende da defasagem do SIH (~60 dias na emissão)",
     "defasagem_documentada": "não documentada; o 01 só nota que internações atrasam em relação à onda",
     "ablacao_familia_delta_auprc": f"target history (inteira): {abl_media['target history']:+.4f}"},
    {"fonte": "e-Gestor APS (ESF)", "features": "esf_cobertura_pct_lag1, esf_qt_equipes_lag1", "familia": "health services",
     "anos_publicados": "mensal", "regra_juncao": "mês t-1", "ano_do_dado_por_ano_da_linha": "mês t-1",
     "linhas_de_teste_com_dado_do_proprio_ano_ou_posterior": "não, se publicado em até ~60 dias",
     "defasagem_documentada": "não documentada", "ablacao_familia_delta_auprc": f"health services: {abl_media['health services']:+.4f}"},
    {"fonte": "NASA POWER (clima)", "features": "t2m, prectotcorr, rh2m, ws10m, ps (mês t, lags e média de 3)",
     "familia": "climate", "anos_publicados": "diário", "regra_juncao": "mês t",
     "ano_do_dado_por_ano_da_linha": "mês t", "linhas_de_teste_com_dado_do_proprio_ano_ou_posterior": "não (mês t já terminou na emissão)",
     "defasagem_documentada": "diário a ~3 dias do presente (01, fonte NASA POWER)",
     "ablacao_familia_delta_auprc": f"climate: {abl_media['climate']:+.4f}"},
]
aud = pd.DataFrame(aud)
aud.to_csv(OUT_DIR / "a3_auditoria_features.csv", index=False)
print()
print(aud[["fonte", "ano_do_dado_por_ano_da_linha", "linhas_de_teste_com_dado_do_proprio_ano_ou_posterior",
           "ablacao_familia_delta_auprc"]].to_string(index=False))
