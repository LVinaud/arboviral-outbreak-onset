"""Comparação de um município com os de porte parecido e com os vizinhos.

Responde "como este município está em relação a municípios parecidos com ele",
a pergunta que o gestor faz. Comparar com a média do estado não informa: ela
mistura a capital com cidades de três mil habitantes.

É posição, não causa. Estar abaixo dos pares em cobertura de esgoto não quer
dizer que o esgoto provoca surto; a versão anterior da plataforma testou
retirar variáveis apontadas como importantes e nem sempre a previsão piorou.
A tela mostra onde o município está, e o gestor tira a conclusão.

Adaptado de `comparacao/indicadores.py` da versão anterior.
"""
from dataclasses import dataclass

import numpy as np
import pandas as pd
import streamlit as st

from i18n import t
from lib import dados

# Faixas de população do IBGE: reconhecíveis e com municípios suficientes em
# cada uma para a posição dentro do grupo dizer alguma coisa. O nome de cada
# faixa está em i18n/comparacao.py ("comp.porte.<índice>").
FAIXAS_PORTE = [0, 5_000, 10_000, 20_000, 50_000, 100_000, 500_000, 10**12]
# A capital tem 11,9 milhões de habitantes e o segundo maior município não
# chega a 1,5 milhão: não há grupo de comparação honesto para ela.
COD_CAPITAL = 3550308
# Com menos pares que isso, a posição no grupo vira ruído.
MIN_PARES = 8


@dataclass(frozen=True)
class Indicador:
    coluna: str
    # Nome, unidade e fonte ficam em i18n/comparacao.py, com a coluna como
    # parte da chave ("comp.ind.<coluna>", "comp.unidade.<coluna>",
    # "comp.fonte.<coluna>"); o tema em "comp.tema.<tema>".
    tema: str
    # True: mais é melhor; False: menos é melhor; None: só contexto, sem
    # melhor ou pior (densidade, área urbanizada).
    maior_melhor: bool | None

    @property
    def rotulo(self) -> str:
        return t(f"comp.ind.{self.coluna}")

    @property
    def unidade(self) -> str:
        return t(f"comp.unidade.{self.coluna}")

    @property
    def fonte(self) -> str:
        return t(f"comp.fonte.{self.coluna}")

    @property
    def nome_tema(self) -> str:
        return t(f"comp.tema.{self.tema}")


INDICADORES = [
    Indicador("iag0001_atend_agua_pct", "saneamento", True),
    Indicador("ies0001_atend_esgoto_pct", "saneamento", True),
    Indicador("ies0007_esgoto_tratado_pct", "saneamento", True),
    Indicador("iap0001_vias_pavimentadas_pct", "saneamento", True),
    Indicador("esf_cobertura_pct", "saude", True),
    Indicador("equipes_por_10k", "saude", True),
    Indicador("latencia_dengue", "saude", False),
    Indicador("cob_vac_fa_pct", "saude", True),
    Indicador("densidade_hab_km2", "contexto", None),
    Indicador("pct_nao_vegetado", "contexto", None),
    Indicador("idhm_2010", "contexto", None),
]


def faixa_de_porte(pop: float) -> int:
    """Índice da faixa de população, de 0 (até 5 mil) a 6 (mais de 500 mil)."""
    for i in range(len(FAIXAS_PORTE) - 1):
        if FAIXAS_PORTE[i] <= pop < FAIXAS_PORTE[i + 1]:
            return i
    return len(FAIXAS_PORTE) - 2


def nome_porte(indice: int) -> str:
    return t(f"comp.porte.{int(indice)}")


@st.cache_data(show_spinner=False)
def tabela_indicadores() -> pd.DataFrame:
    """Uma linha por município: o último valor disponível de cada indicador.

    Cada fonte tem calendário próprio (o saneamento só existe até 2024, a
    atenção primária chega ao último mês), então vale o último valor publicado
    de cada uma, e a tela diz de quando ele é.
    """
    colunas = ["cod_ibge", "ano", "mes", "pop_residente", "esf_qt_equipes",
               "dengue_latencia_mediana"]
    colunas += [i.coluna for i in INDICADORES]
    m = dados.ler_parquet("master/municipio_mes.parquet")
    m = m[[c for c in dict.fromkeys(colunas) if c in m.columns]]
    m = m.sort_values(["cod_ibge", "ano", "mes"])
    # Equipes em números absolutos enganam entre portes: três equipes são muito
    # numa cidade de cinco mil habitantes e quase nada numa de trezentos mil.
    m["equipes_por_10k"] = m["esf_qt_equipes"] / m["pop_residente"] * 10_000

    saida = m.groupby("cod_ibge").agg(pop_residente=("pop_residente", "last"))
    for ind in INDICADORES:
        if ind.coluna == "latencia_dengue":
            continue
        if ind.coluna in m.columns:
            saida[ind.coluna] = m.dropna(subset=[ind.coluna]).groupby("cod_ibge")[ind.coluna].last()
    # Latência de um mês só é ruidosa (um caso atrasado muda tudo): mediana dos
    # últimos 12 meses em que houve caso notificado.
    lat = m.dropna(subset=["dengue_latencia_mediana"])
    saida["latencia_dengue"] = (lat.groupby("cod_ibge")["dengue_latencia_mediana"]
                                .apply(lambda s: s.tail(12).median()))
    saida["porte"] = saida["pop_residente"].fillna(0).map(faixa_de_porte)
    return saida.reset_index()


def posicao_no_grupo(cod_ibge: int) -> dict:
    """Onde o município fica, indicador a indicador, entre os do mesmo porte.

    `posicao` vai de 0 a 100. Nos indicadores com melhor e pior, é a parte dos
    pares que está pior que o município (100 = melhor do grupo). Nos de
    contexto, é a parte dos pares com valor menor. Empates contam pela metade:
    sem isso, um município com 100% de água, empatado com metade do grupo,
    apareceria como "melhor que 50%".
    """
    tab = tabela_indicadores()
    linha = tab[tab.cod_ibge == cod_ibge]
    if linha.empty:
        return {"itens": [], "porte": None, "n_grupo": 0, "capital": False}
    linha = linha.iloc[0]
    grupo = tab[(tab.porte == linha.porte) & (tab.cod_ibge != cod_ibge)]

    itens = []
    for ind in INDICADORES:
        if ind.coluna not in tab.columns or pd.isna(linha[ind.coluna]):
            continue
        pares = grupo[ind.coluna].dropna()
        if len(pares) < MIN_PARES:
            continue
        valor = float(linha[ind.coluna])
        if ind.maior_melhor is False:
            abaixo = (pares > valor).mean()
        else:
            abaixo = (pares < valor).mean()
        iguais = (pares == valor).mean()
        itens.append({"indicador": ind, "valor": valor,
                      "mediana": float(pares.median()),
                      "posicao": 100 * float(abaixo + iguais / 2),
                      "n_pares": int(len(pares))})
    return {"itens": itens, "porte": linha.porte, "n_grupo": int(len(grupo)),
            "capital": int(cod_ibge) == COD_CAPITAL}


def vizinhos(cod_ibge: int, n: int = 8) -> pd.DataFrame:
    """Os n municípios mais próximos, com a distância em km, e o próprio.

    Vizinhança responde a outra pergunta que o porte: o mosquito não respeita
    divisa, então o que acontece ao lado importa mesmo quando o vizinho tem
    outro tamanho. Distância entre as coordenadas de referência de cada
    município, pela fórmula do haversine.
    """
    geo = dados.coordenadas()
    alvo = geo[geo.cod_ibge == cod_ibge]
    if alvo.empty:
        return geo.head(0).assign(distancia_km=[])
    lat0, lon0 = np.radians(float(alvo.lat.iloc[0])), np.radians(float(alvo.lon.iloc[0]))
    lat, lon = np.radians(geo.lat.to_numpy()), np.radians(geo.lon.to_numpy())
    a = (np.sin((lat - lat0) / 2) ** 2
         + np.cos(lat0) * np.cos(lat) * np.sin((lon - lon0) / 2) ** 2)
    geo = geo.assign(distancia_km=2 * 6371 * np.arcsin(np.sqrt(a)))
    return geo.nsmallest(n + 1, "distancia_km").reset_index(drop=True)
