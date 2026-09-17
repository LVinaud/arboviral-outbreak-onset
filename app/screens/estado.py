"""Tela: o estado inteiro num relance.

Um coordenador estadual não decide município por município: ele decide onde
concentrar atenção neste mês. Esta tela responde a isso com um mapa dos 645 e
com as distribuições por trás dele.

O mapa mistura deliberadamente uma cidade de meio milhão com uma de três mil
habitantes. Risco e porte são perguntas diferentes, e esconder as pequenas
atrás das grandes seria responder à pergunta errada. O tamanho da bolha mostra
a população, para uma cidade pequena no topo da lista ser lida como uma cidade
pequena no topo da lista.
"""
import numpy as np
import pandas as pd
import streamlit as st

import i18n
from i18n import inteiro, maiuscula, numero, t
from lib import dados, historico

st.title(t("estado.titulo"))

if dados.combinacoes_disponiveis().empty:
    st.error(t("erro.sem_previsoes"))
    st.stop()

# Cada seletor lembra a escolha entre telas (ver dados.seletor).
doenca, definicao, h, tipo = dados.seletores_previsao()

prev = dados.previsoes(doenca, definicao, h)
if prev is None or prev.empty:
    st.warning(t("erro.nao_treinada"))
    st.stop()
prev = prev[prev.model == tipo]
if prev.empty:
    st.warning(t("estado.erro_modelo"))
    st.stop()

ultimo = prev.sort_values(["ano", "mes"]).iloc[-1]
obs_ano, obs_mes = int(ultimo["ano"]), int(ultimo["mes"])
prev = prev[(prev.ano == obs_ano) & (prev.mes == obs_mes)].copy()
alvo_ano, alvo_mes = int(prev.ano_alvo.iloc[0]), int(prev.mes_alvo.iloc[0])

limiar = dados.limiar_de(doenca, definicao, h, tipo)

# Situação no mês observado, que é a distinção central do trabalho.
rot = dados.rotulos()
col_rot = f"{doenca}_{definicao}"
if col_rot in rot.columns:
    estado = rot.loc[(rot.ano == obs_ano) & (rot.mes == obs_mes),
                     ["cod_ibge", col_rot]].rename(columns={col_rot: "em_surto"})
    prev = prev.merge(estado, on="cod_ibge", how="left")
else:
    prev["em_surto"] = np.nan

prev = prev.merge(dados.municipios(), on="cod_ibge", how="left")
prev = prev.merge(dados.coordenadas(), on="cod_ibge", how="left")
prev["faixa"] = prev.proba.map(lambda x: dados.faixa_de(x, limiar))
prev["acima_do_limiar"] = prev.proba >= limiar

st.caption(t("estado.legenda_topo",
             alvo=dados.mes_por_extenso(alvo_ano, alvo_mes),
             obs=dados.mes_por_extenso(obs_ano, obs_mes),
             corte=maiuscula(dados.frase_corte(h, limiar))))

# ------------------------------------------------------------------- resumo
m1, m2, m3, m4 = st.columns(4)
m1.metric(t("estado.m_municipios"), inteiro(len(prev)))
m2.metric(t("estado.m_previsto"), inteiro(prev.acima_do_limiar.sum()),
          help=t("estado.m_previsto_ajuda", corte=numero(limiar, 2),
                 frase=dados.frase_corte(h, limiar)))
m3.metric(t("estado.m_sem_surto"),
          inteiro((prev.acima_do_limiar & (prev.em_surto == 0)).sum()),
          help=t("estado.m_sem_surto_ajuda"))
m4.metric(t("estado.m_mediano"), numero(prev.proba.median(), 2))

st.divider()

# --------------------------------------------------------------------- mapa
st.subheader(t("estado.mapa_titulo"))

mapa = prev.dropna(subset=["lat", "lon"]).copy()

if mapa.empty:
    st.caption(t("estado.sem_coordenadas"))
else:
    import plotly.graph_objects as go

    # Tamanho pela população em escala comprimida, a mesma que a versão
    # anterior da plataforma usava: sem isso a capital vira um disco que cobre
    # a Grande São Paulo inteira e esconde os vizinhos. Expoente 0,28 e não
    # raiz quadrada porque a população do estado varia quatro ordens de
    # grandeza; depois reescalada linearmente para a faixa de 6 a 32 pixels.
    # Em pixels, e não em metros, para o círculo não mudar de tamanho ao dar
    # zoom.
    _p = mapa["pop_residente"].fillna(0).clip(lower=1) ** 0.28
    mapa["tamanho"] = 6 + 26 * (_p - _p.min()) / max(_p.max() - _p.min(), 1e-9)

    # A cor é a FAIXA, não o escore contínuo. Uma escala contínua com barra de
    # cor convidaria a ler "0,46" como "46% de chance", que é precisamente a
    # leitura que o escore não suporta: ele ordena municípios, não estima
    # probabilidade. A faixa já embute o corte daquela combinação. As cores são
    # as mesmas da tela de alertas (dados.CORES_FAIXA).
    fig = go.Figure()
    for faixa, cores in dados.CORES_FAIXA.items():
        sub = mapa[mapa.faixa == faixa]
        if sub.empty:
            continue
        fig.add_trace(go.Scattermap(
            lat=sub["lat"], lon=sub["lon"], mode="markers", name=dados.nome_faixa(faixa),
            marker=dict(size=sub["tamanho"], color=cores["cor"], opacity=0.85),
            customdata=np.stack([sub["municipio"], sub["proba"],
                                 sub["pop_residente"].fillna(0),
                                 sub["cod_ibge"]], axis=-1),
            hovertemplate=("<b>%{customdata[0]}</b><br>"
                           f"{t('estado.dica_escore')}: %{{customdata[1]:.2f}}<br>"
                           f"{t('estado.dica_populacao')}: %{{customdata[2]:,.0f}}"
                           "<extra></extra>"),
        ))
    fig.update_layout(
        map=dict(style="carto-positron", center=dict(lat=-22.4, lon=-48.6), zoom=5.4),
        margin=dict(l=0, r=0, t=0, b=0), height=520,
        separators=i18n.separadores_plotly(),
        legend=dict(orientation="h", yanchor="bottom", y=0.01, xanchor="center", x=0.5,
                    bgcolor="rgba(255,255,255,0.7)"),
    )
    # on_select devolve o ponto clicado. O customdata carrega o código IBGE
    # junto do nome, porque nome de município não é chave: São Paulo tem
    # homônimos em outros estados e, dentro do estado, nomes que só diferem por
    # acento. O código é o que identifica.
    evento = st.plotly_chart(fig, width="stretch",
                             on_select="rerun", selection_mode="points",
                             key="mapa_estado")
    pontos = (evento.get("selection", {}) or {}).get("points", []) if evento else []
    if pontos:
        cd = pontos[0].get("customdata")
        if cd:
            dados.abrir_municipio(int(cd[3]), "mapa")

    st.caption(t("estado.mapa_legenda"))

st.divider()

# ---------------------------------------------------------------- estatística
st.subheader(t("estado.dist_titulo"))

g1, g2 = st.columns(2)
with g1:
    st.markdown(t("estado.dist_subtitulo"))
    contar = st.radio(t("estado.contar_por"), ["municipios", "populacao"],
                      format_func=lambda c: t(f"estado.contar_{c}"),
                      horizontal=True, key="dist_contar")

    # Barras de 0,05 fechadas à esquerda: um município com escore igual ao
    # corte cai na barra que começa no corte, como em "surto previsto".
    LARGURA = 0.05
    inicios = np.round(np.arange(0, 1, LARGURA), 2)
    barra = (np.floor(prev.proba.clip(0, 0.9999) / LARGURA) * LARGURA).round(2)
    if contar == "populacao":
        valores = prev.pop_residente.fillna(0).groupby(barra).sum()
        eixo_y = t("estado.eixo_habitantes")
    else:
        valores = barra.value_counts()
        eixo_y = t("estado.eixo_municipios")
    valores = valores.reindex(inicios, fill_value=0)
    eixo_x = t("estado.eixo_escore")
    dist = pd.DataFrame({eixo_x: [numero(x, 2) for x in inicios],
                         eixo_y: valores.to_numpy()})
    st.bar_chart(dist, x=eixo_x, y=eixo_y, height=250)

    acima = prev.proba >= limiar
    if contar == "populacao":
        total = prev.pop_residente.fillna(0).sum()
        parte = prev.loc[acima, "pop_residente"].fillna(0).sum()
        frac = parte / total if total else 0.0
        pct_txt = t("estado.menos_de_01") if 0 < frac < 0.001 else i18n.pct(frac, 1)
        resumo = t("estado.resumo_pop", hab=inteiro(parte), pct=pct_txt)
    else:
        resumo = t("estado.resumo_mun", n=int(acima.sum()), total=len(prev))
    st.caption(t("estado.dist_legenda", corte=numero(limiar, 2), resumo=resumo))

with g2:
    st.markdown(t("estado.porte_subtitulo"))
    faixas_pop = [(0, 1e4), (1e4, 5e4), (5e4, 2e5), (2e5, 1e9)]
    linhas = []
    for i, (lo, hi) in enumerate(faixas_pop):
        sub = prev[(prev.pop_residente >= lo) & (prev.pop_residente < hi)]
        if len(sub):
            linhas.append({t("estado.col_porte"): t(f"estado.porte_{i}"),
                           t("estado.col_municipios"): len(sub),
                           t("estado.col_escore_mediano"): numero(sub.proba.median(), 3),
                           t("estado.col_com_surto"): int(sub.acima_do_limiar.sum())})
    st.dataframe(pd.DataFrame(linhas), hide_index=True, width="stretch")
    st.caption(t("estado.porte_legenda"))

# ------------------------------------------------- começo contra continuação
st.markdown(t("estado.comeco_subtitulo"))
tab = prev.groupby(prev.em_surto.map({0: dados.SEM_SURTO, 1: dados.EM_SURTO}),
                   dropna=True).agg(
    municipios=("cod_ibge", "size"),
    escore_mediano=("proba", "median"),
    com_surto_previsto=("acima_do_limiar", "sum"),
).reset_index(names="situacao")
# "Não está em surto" primeiro: é a linha que interessa.
tab = tab.sort_values("situacao", key=lambda s: s != dados.SEM_SURTO)
tab = pd.DataFrame({
    t("estado.col_situacao"): tab.situacao.map(dados.nome_situacao).values,
    t("estado.col_municipios"): tab.municipios.values,
    t("estado.col_escore_mediano"): [numero(v, 3) for v in tab.escore_mediano],
    t("estado.col_com_surto"): tab.com_surto_previsto.astype(int).values,
})
st.dataframe(tab, hide_index=True, width="stretch")
st.caption(t("estado.comeco_legenda"))

st.divider()

# ---------------------------------------------------------------- os maiores
st.subheader(t("estado.top_titulo"))
_maiores = prev.nlargest(15, "proba")
col_pop, col_faixa, col_escore = (t("estado.col_populacao"), t("estado.col_faixa"),
                                  t("estado.col_escore"))
top = pd.DataFrame({
    t("estado.col_municipio"): _maiores.municipio.values,
    col_pop: _maiores.pop_residente.values,
    col_faixa: _maiores.faixa.map(dados.nome_faixa).values,
    col_escore: _maiores.proba.values,
    t("estado.col_situacao_curta"): _maiores.em_surto.map(
        {0: dados.SEM_SURTO, 1: dados.EM_SURTO}).fillna(dados.SEM_DADO)
        .map(dados.nome_situacao).values,
})
# Faixa colorida como na tela de alertas. Com um Styler, o Streamlit exibe os
# valores formatados por ele, então os números também são formatados aqui.
top_estilizada = (top.style
                  .map(dados.estilo_faixa, subset=[col_faixa])
                  .format({col_escore: lambda v: numero(v, 2),
                           col_pop: lambda v: (t("comum.sem_dado") if pd.isna(v)
                                               else inteiro(v))}))

# Clicar numa linha abre o município. É o caminho garantido: traces de mapa do
# Plotly nem sempre emitem o evento de seleção que o Streamlit escuta, então a
# tabela existe como forma confiável de chegar ao mesmo lugar.
sel = st.dataframe(
    top_estilizada, hide_index=True, width="stretch",
    on_select="rerun", selection_mode="single-row", key="top15",
    column_config={
        col_escore: st.column_config.ProgressColumn(col_escore, min_value=0.0,
                                                    max_value=1.0, format="%.2f"),
    },
)
_linhas = (sel.get("selection", {}) or {}).get("rows", []) if sel else []
if _linhas:
    dados.abrir_municipio(int(_maiores.iloc[_linhas[0]].cod_ibge), "top15")
st.caption(t("estado.top_legenda"))

st.divider()

# ------------------------------------------------------------ o passado
# Esta seção só depende da doença: são os casos confirmados, sem modelo.

_nome_doenca = dados.doenca_na_frase(doenca)
st.subheader(maiuscula(t("hist.titulo", doenca=_nome_doenca)))

_serie = historico.serie_estado(doenca)
_ult = _serie.iloc[-1]
st.caption(t("hist.periodo", doenca=_nome_doenca,
             mes=dados.mes_por_extenso(int(_ult.ano), int(_ult.mes))))

st.plotly_chart(historico.figura_mapa(doenca, i18n.idioma()), width="stretch",
                key="mapa_historico")

# Legenda de tamanhos: o mapa não tem uma nativa. Círculos desenhados com o
# mesmo diâmetro que as bolhas teriam.
_max_doenca = float(historico.casos_por_mes(doenca).casos.max())
_itens = "".join(
    f"<span style='display:inline-flex;align-items:center;gap:6px;margin-right:18px'>"
    f"<span style='display:inline-block;width:{px:.0f}px;height:{px:.0f}px;"
    f"border-radius:50%;background:#3987e5;opacity:.8'></span>"
    f"{t('estado.hist_legenda_tamanho', n=inteiro(n))}</span>"
    for n, px in historico.legenda_tamanhos(_max_doenca)
)
st.markdown(f"<div style='display:flex;flex-wrap:wrap;align-items:center;"
            f"margin:4px 0 8px'>{_itens}</div>", unsafe_allow_html=True)
st.caption(t("estado.hist_legenda"))

st.markdown(f"**{maiuscula(t('estado.hist_mensal', doenca=_nome_doenca))}**")
historico.grafico_mensal(_serie, "hist")
