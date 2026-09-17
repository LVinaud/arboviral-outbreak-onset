"""O histórico de casos: mapa animado mês a mês e série do estado.

Nada aqui depende de modelo, definição de surto ou antecedência. São os casos
confirmados notificados, como estão na tabela mestre, de janeiro de 2015 até o
último mês consolidado.
"""
import altair as alt
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

import i18n
from i18n import inteiro, t
from lib import dados

# O tamanho mostra o número de casos (ver tamanho_bolinhas); a cor, a
# incidência, em cinco faixas iguais para todas as doenças. Os cortes de 100 e
# 300 casos por 100 mil habitantes são os mesmos das definições de surto do
# aplicativo. A rampa é azul, do claro ao escuro, para não se confundir com as
# faixas de risco (vermelho, laranja, amarelo e verde) do outro mapa da mesma
# tela; começa no tom 250 porque os mais claros somem sobre o fundo do mapa.
# Validada como rampa ordinal pelo validador do guia de visualização.
FAIXAS_INCIDENCIA = [10, 100, 300, 1000]
CORES_INCIDENCIA = ["#86b6ef", "#5598e7", "#2a78d6", "#1c5cab", "#0d366b"]


def _escala_em_degraus(cores: list[str]) -> list[list]:
    """Escala de cor do Plotly em degraus, uma cor inteira por faixa."""
    n, escala = len(cores), []
    for i, c in enumerate(cores):
        escala += [[i / n, c], [(i + 1) / n, c]]
    return escala


COR_BASE = "rgba(148, 163, 184, 0.55)"
DIAMETRO_MINIMO = 4
DIAMETRO_MAXIMO = 90
EXPOENTE = 0.35


@st.cache_data(show_spinner=False)
def casos_por_mes(doenca: str) -> pd.DataFrame:
    """Casos confirmados por município e mês.

    Nulo vira zero: na tabela mestre, nulo em casos significa que não houve
    nenhuma notificação naquele município naquele mês.
    """
    col = f"{doenca}_casos"
    m = dados.ler_parquet("master/municipio_mes.parquet",
                          columns=["cod_ibge", "ano", "mes", "pop_residente", col])
    m = m.rename(columns={col: "casos"})
    m["casos"] = m["casos"].fillna(0)
    # Incidência com a população daquele ano, não a de hoje.
    m["incidencia"] = m["casos"] / m["pop_residente"] * 1e5
    return m


@st.cache_data(show_spinner=False)
def serie_estado(doenca: str) -> pd.DataFrame:
    """Total de casos do estado em cada mês."""
    s = casos_por_mes(doenca).groupby(["ano", "mes"], as_index=False)["casos"].sum()
    s["data"] = pd.to_datetime(dict(year=s.ano, month=s.mes, day=1))
    return s


def serie_municipio(doenca: str, cod_ibge: int) -> pd.DataFrame:
    """Casos de um município em cada mês, no mesmo formato de serie_estado."""
    m = casos_por_mes(doenca)
    s = m.loc[m.cod_ibge == cod_ibge, ["ano", "mes", "casos"]].sort_values(["ano", "mes"])
    s = s.reset_index(drop=True)
    s["data"] = pd.to_datetime(dict(year=s.ano, month=s.mes, day=1))
    return s


def grafico_mensal(serie: pd.DataFrame, chave: str) -> None:
    """Casos mês a mês, com seletor de ano. É o mesmo gráfico na tela do estado
    e na do município; `chave` separa os seletores de uma e de outra.

    `serie` tem as colunas ano, mes, casos e data.
    """
    anos = sorted(int(a) for a in serie.ano.unique())
    c1, c2 = st.columns([1, 2])
    with c1:
        # "todos" é código; o rótulo sai traduzido. Com o texto como opção, a
        # escolha se perderia ao trocar de idioma.
        ano = st.selectbox(t("hist.ano"), ["todos"] + anos[::-1], key=f"{chave}_ano",
                           format_func=lambda a: t("hist.todos_anos") if a == "todos" else str(a))
    # O eixo vertical é o mesmo para todos os anos: o maior mês da série
    # inteira. Se cada ano tivesse a própria escala, um ano fraco pareceria tão
    # alto quanto a epidemia de 2024. A caixa abaixo permite ajustar ao ano para
    # ver os detalhes dos anos fracos, que na escala comum ficam achatados.
    ajustar = False
    if ano != "todos":
        with c2:
            st.write("")
            ajustar = st.checkbox(t("hist.ajustar"), value=False, key=f"{chave}_ajustar",
                                  help=t("hist.ajustar_ajuda"))
    teto = float(serie.casos.max())
    # Sem nenhum caso na série, o eixo iria de 0 a 0.
    dominio = [0, teto if teto > 0 else 1]

    if ano == "todos":
        graf = alt.Chart(serie).mark_line(strokeWidth=2).encode(
            x=alt.X("data:T", title=None, axis=alt.Axis(format="%Y")),
            y=alt.Y("casos:Q", title=t("hist.eixo_casos")),
            tooltip=[alt.Tooltip("data:T", title=t("hist.dica_mes"), format="%m/%Y"),
                     alt.Tooltip("casos:Q", title=t("hist.dica_casos"), format=",.0f")],
        )
    else:
        abrev = i18n.meses_abrev()
        um = serie[serie.ano == ano].copy()
        um["rotulo_mes"] = [abrev[m - 1] for m in um.mes]
        graf = alt.Chart(um).mark_bar(cornerRadiusTopLeft=3, cornerRadiusTopRight=3).encode(
            x=alt.X("rotulo_mes:N", sort=abrev, title=None, scale=alt.Scale(domain=abrev)),
            y=alt.Y("casos:Q", title=t("hist.eixo_casos"),
                    scale=alt.Scale() if ajustar else alt.Scale(domain=dominio)),
            tooltip=[alt.Tooltip("rotulo_mes:N", title=t("hist.dica_mes")),
                     alt.Tooltip("casos:Q", title=t("hist.dica_casos"), format=",.0f")],
        )
    st.altair_chart(graf.properties(height=280).configure(locale=i18n.locale_altair()),
                    width="stretch")

    if teto == 0:
        st.caption(t("hist.nenhum_caso"))
    elif ano == "todos":
        pico = serie.loc[serie.casos.idxmax()]
        st.caption(t("hist.pico", mes=i18n.mes_extenso(int(pico.ano), int(pico.mes)),
                     n=inteiro(pico.casos)))
    else:
        tot = int(serie.loc[serie.ano == ano, "casos"].sum())
        n = int((serie.ano == ano).sum())
        texto = t("hist.total", ano=ano, n=inteiro(tot))
        if not ajustar:
            texto = t("hist.eixo_fixo", teto=inteiro(teto), texto=texto)
        if n < 12:
            texto += t("hist.ano_incompleto", n=n)
        st.caption(texto + ".")


def faixa_incidencia(incidencia: np.ndarray) -> np.ndarray:
    """Índice da faixa de incidência (0 a 4). Cada faixa inclui o limite de
    baixo: 100 casos por 100 mil cai em "100 a 300"."""
    return np.searchsorted(FAIXAS_INCIDENCIA, np.asarray(incidencia, dtype=float),
                           side="right")


@st.cache_data(show_spinner=False)
def maximo_absoluto() -> float:
    """Maior número de casos num município em um mês, somando todas as doenças
    da tabela. Hoje é a cidade de São Paulo em abril de 2024, com dengue."""
    cols = [f"{d}_casos" for d in dados.DOENCAS]
    m = dados.ler_parquet("master/municipio_mes.parquet")
    return float(m[[c for c in cols if c in m.columns]].max().max())


def tamanho_bolinhas(casos: np.ndarray) -> np.ndarray:
    """Diâmetro da bolha: potência 0,35 do número de casos.

    Entre a raiz quadrada e o log. A raiz (expoente 0,5), usada na versão
    anterior da plataforma, deixava quase tudo como um ponto: 139 casos davam
    5 pixels. O log resolvia os meses comuns mas comprimia o topo, e 10 mil
    casos ficavam quase do tamanho dos 199 mil de São Paulo em 2024. Com 0,35,
    a mediana dos meses com caso fica visível e os maiores continuam bem
    maiores: 139 casos dão 10 pixels, 10 mil dão 34 e o máximo, 90.

    A escala é a mesma para todas as doenças e todos os meses: bolhas do mesmo
    tamanho significam o mesmo número de casos. Se cada doença usasse o próprio
    máximo, os 276 casos de zika do pior mês ganhariam o tamanho dos 199 mil de
    dengue.
    """
    frac = np.clip(np.asarray(casos, dtype=float) / maximo_absoluto(), 0, 1)
    return DIAMETRO_MINIMO + (DIAMETRO_MAXIMO - DIAMETRO_MINIMO) * frac ** EXPOENTE


def legenda_tamanhos(maximo_doenca: float) -> list[tuple[int, float]]:
    """Valores de referência para a legenda de tamanhos, até o máximo da doença."""
    refs = [10, 100, 1_000, 10_000, 100_000]
    refs = [r for r in refs if r <= max(maximo_doenca, 10)]
    return [(r, float(tamanho_bolinhas(np.array([r]))[0])) for r in refs]


@st.cache_data(show_spinner=False)
def figura_mapa(doenca: str, lang: str) -> dict:
    """Mapa animado, um quadro por mês, devolvido como dicionário para caber
    no cache (o objeto Figure não é serializável de forma estável).

    `lang` entra na chave do cache: sem ele, o mapa ficaria no idioma de quem o
    montou primeiro."""
    abrev = i18n.meses_abrev()
    casos = casos_por_mes(doenca)
    geo = dados.coordenadas().merge(dados.municipios(), on="cod_ibge", how="left")
    casos = casos.merge(geo, on="cod_ibge", how="inner")

    # Camada fixa: todos os municípios como pontos cinza, para o contorno do
    # estado aparecer mesmo nos meses com poucos casos.
    base = go.Scattermap(
        lat=geo["lat"].round(3), lon=geo["lon"].round(3), mode="markers",
        marker=dict(size=3, color=COR_BASE), hoverinfo="skip", showlegend=False,
    )

    meses = casos[["ano", "mes"]].drop_duplicates().sort_values(["ano", "mes"])
    quadros, passos = [], []
    for ano, mes in meses.itertuples(index=False):
        # Maiores primeiro: as menores são desenhadas por cima e não somem.
        m = casos[(casos.ano == ano) & (casos.mes == mes) & (casos.casos > 0)]
        m = m.sort_values("casos", ascending=False)
        nome = f"{abrev[mes - 1]} {ano}"
        quadros.append(go.Frame(
            name=nome, traces=[1],
            data=[go.Scattermap(
                lat=m["lat"].round(3), lon=m["lon"].round(3), mode="markers",
                marker=dict(size=tamanho_bolinhas(m["casos"].to_numpy()).round(1),
                            sizemode="diameter",
                            color=((faixa_incidencia(m["incidencia"]) + 0.5)
                                   / len(CORES_INCIDENCIA)).round(3),
                            coloraxis="coloraxis", opacity=0.8),
                # Lista de pares, e não np.stack: empilhar nome com número
                # transformaria o número em texto e o separador de milhar sumiria.
                customdata=list(zip(m["municipio"], m["casos"].astype(int).tolist(),
                                    m["incidencia"].round(1).tolist())),
                hovertemplate=(f"<b>%{{customdata[0]}}</b><br>{nome}<br>"
                               f"%{{customdata[1]:,}} {t('mapa_hist.casos')}<br>"
                               f"%{{customdata[2]:,.1f}} {t('mapa_hist.por_100k')}"
                               "<extra></extra>"),
                showlegend=False,
            )],
        ))
        passos.append(dict(
            method="animate", label=nome,
            args=[[nome], dict(mode="immediate", frame=dict(duration=0, redraw=True),
                               transition=dict(duration=0))],
        ))

    fig = go.Figure(data=[base, quadros[0].data[0]], frames=quadros)
    n = len(CORES_INCIDENCIA)
    fig.update_layout(
        map=dict(style="carto-positron", center=dict(lat=-22.4, lon=-48.6), zoom=5.4),
        height=560, margin=dict(l=0, r=0, t=0, b=100),
        separators=i18n.separadores_plotly(),
        coloraxis=dict(
            colorscale=_escala_em_degraus(CORES_INCIDENCIA), cmin=0, cmax=1,
            colorbar=dict(title=dict(text=t("mapa_hist.barra")),
                          tickvals=[(i + 0.5) / n for i in range(n)],
                          ticktext=[t(f"mapa_hist.faixa_{i}") for i in range(n)],
                          thickness=14, len=0.75),
        ),
        sliders=[dict(
            active=0, x=0.1, y=0, xanchor="left", yanchor="top", len=0.88,
            pad=dict(t=30, b=10), steps=passos,
            currentvalue=dict(prefix=t("mapa_hist.mes"), visible=True, xanchor="left",
                              font=dict(size=14)),
        )],
        updatemenus=[dict(
            type="buttons", direction="left", showactive=False,
            x=0.0, y=0, xanchor="left", yanchor="top", pad=dict(t=30, b=10),
            buttons=[
                dict(label="▶", method="animate",
                     args=[None, dict(frame=dict(duration=500, redraw=True),
                                      transition=dict(duration=0),
                                      fromcurrent=True, mode="immediate")]),
                dict(label="⏸", method="animate",
                     args=[[None], dict(frame=dict(duration=0, redraw=False),
                                        mode="immediate")]),
            ],
        )],
    )
    return fig.to_dict()
