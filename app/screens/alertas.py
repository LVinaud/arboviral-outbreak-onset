"""Tela: a fila de atenção do mês.

Esta é a tela que carrega o argumento do trabalho. A coluna que separa
municípios que já estão em surto daqueles que não estão não é um detalhe
de apresentação: é a distinção inteira, na forma em que um gestor a usa.

Um alerta num município que já está em surto confirma o que a equipe já sabe.
Um alerta num município que não está em surto é o único que ainda deixa tempo
de agir, e é também o mais difícil de acertar. Um filtro permite mostrar só
esses; ele começa desligado, para a lista mostrar o estado inteiro.

O que conta como "surto previsto" e onde cada faixa começa dependem da
combinação escolhida (doença, definição, antecedência e modelo): ver
`dados.cortes_faixa`.
"""
import pandas as pd
import streamlit as st

from i18n import inteiro, maiuscula, numero, t
from lib import dados

st.title(t("alertas.titulo"))

# ---------------------------------------------------------------- seletores
if dados.combinacoes_disponiveis().empty:
    st.error(t("erro.sem_previsoes_producao"))
    st.stop()

# Cada seletor lembra a escolha entre telas (ver dados.seletor).
doenca, definicao, h, tipo = dados.seletores_previsao("sel.o_que_conta")

# ------------------------------------------------------------------- dados
prev = dados.previsoes(doenca, definicao, h)
if prev is None or prev.empty:
    st.warning(t("erro.nao_treinada"))
    st.stop()

prev = prev[prev.model == tipo]
if prev.empty:
    st.warning(t("alertas.erro_modelo", modelo=dados.nome_modelo(tipo)))
    st.stop()

# As previsões cobrem os h meses sem desfecho. O gestor quer a mais recente,
# que é a que observa o último mês consolidado.
ultimo = prev.sort_values(["ano", "mes"]).iloc[-1]
obs_ano, obs_mes = int(ultimo["ano"]), int(ultimo["mes"])
prev = prev[(prev.ano == obs_ano) & (prev.mes == obs_mes)].copy()
alvo_ano, alvo_mes = int(prev.ano_alvo.iloc[0]), int(prev.mes_alvo.iloc[0])

# Corte e faixas desta combinação.
corte = dados.limiar_de(doenca, definicao, h, tipo)
inicio_faixa = dados.cortes_faixa(corte)

# Estado atual: o município já estava em surto no mês observado?
rot = dados.rotulos()
coluna_rotulo = f"{doenca}_{definicao}"
if coluna_rotulo in rot.columns:
    estado = rot.loc[
        (rot.ano == obs_ano) & (rot.mes == obs_mes),
        ["cod_ibge", coluna_rotulo],
    ].rename(columns={coluna_rotulo: "em_surto"})
    prev = prev.merge(estado, on="cod_ibge", how="left")
else:
    prev["em_surto"] = pd.NA

prev = prev.merge(dados.municipios(), on="cod_ibge", how="left")
prev["faixa"] = prev.proba.map(lambda x: dados.faixa_de(x, corte))
prev["surto_previsto"] = prev.proba >= corte
prev["situacao"] = prev.em_surto.map(dados.situacao_de)

st.caption(t("alertas.legenda_topo",
             alvo=dados.mes_por_extenso(alvo_ano, alvo_mes),
             obs=dados.mes_por_extenso(obs_ano, obs_mes),
             corte=maiuscula(dados.frase_corte(h, corte))))

# ------------------------------------------------------------------ resumo
em_surto = prev[prev.situacao == dados.EM_SURTO]
alerta = prev[prev.surto_previsto]

m1, m2, m3, m4 = st.columns(4)
m1.metric(t("alertas.m_avaliados"), inteiro(len(prev)))
m2.metric(t("alertas.m_previsto"), inteiro(len(alerta)),
          help=t("alertas.m_previsto_ajuda", corte=numero(corte, 2),
                 frase=dados.frase_corte(h, corte)))
m3.metric(t("alertas.m_sem_surto"),
          inteiro(len(alerta[alerta.situacao == dados.SEM_SURTO])),
          help=t("alertas.m_sem_surto_ajuda"))
m4.metric(t("alertas.m_ja_em_surto"), inteiro(len(em_surto)))

# Quantos municípios em cada faixa, com as cores da versão anterior.
st.markdown(dados.cartoes_faixa(prev.faixa.value_counts().to_dict(), corte),
            unsafe_allow_html=True)
st.caption(t("alertas.legenda_cartoes"))
st.info(f"**{t('aviso.titulo')}** {t('aviso.corpo')}")

st.divider()

# ------------------------------------------------------------------- lista
# Controles numa linha própria, acima da tabela: numa coluna estreita ao lado
# dela, o texto do filtro ficava cortado. Chaves fixas, para a escolha não se
# perder quando o idioma muda o rótulo.
f1, f2, f3 = st.columns([2, 1, 1], vertical_alignment="bottom")
with f1:
    apenas_sem_surto = st.toggle(t("alertas.filtro_sem_surto"), value=False,
                                 key="alertas_so_sem_surto",
                                 help=t("alertas.filtro_sem_surto_ajuda"))
with f2:
    faixa_minima = st.selectbox(t("alertas.faixa_minima"), dados.NOMES_FAIXA, index=2,
                                format_func=dados.nome_faixa, key="alertas_faixa_minima",
                                help=t("alertas.faixa_minima_ajuda"))
with f3:
    quantos = st.number_input(t("alertas.quantos"), 10, 645, 50, 10, key="alertas_quantos")

tabela = prev.copy()
if apenas_sem_surto:
    tabela = tabela[tabela.situacao == dados.SEM_SURTO]
tabela = tabela[tabela.proba >= inicio_faixa[faixa_minima]]
tabela = tabela.nlargest(int(quantos), "proba")

if tabela.empty:
    st.info(t("alertas.vazio", faixa=dados.nome_faixa(faixa_minima)))
else:
    col_escore = t("alertas.col_escore")
    col_pop = t("alertas.col_populacao")
    col_codigo = t("alertas.col_codigo")
    col_faixa = t("alertas.col_faixa")
    mostrar = pd.DataFrame({
        t("alertas.col_municipio"): tabela.municipio.values,
        col_codigo: tabela.cod_ibge.astype(int).values,
        col_pop: tabela.pop_residente.values,
        t("alertas.col_situacao"): tabela.situacao.map(dados.nome_situacao).values,
        col_faixa: tabela.faixa.map(dados.nome_faixa).values,
        col_escore: tabela.proba.values,
    })
    # Faixa colorida. Com um Styler, o Streamlit exibe os valores formatados
    # por ele, então os números também são formatados aqui.
    estilizada = (mostrar.style
                  .map(dados.estilo_faixa, subset=[col_faixa])
                  .format({col_escore: lambda v: numero(v, 2), col_codigo: "{:d}",
                           col_pop: lambda v: (t("comum.sem_dado") if pd.isna(v)
                                               else inteiro(v))}))
    # Clicar numa linha abre o município com a mesma doença, definição,
    # antecedência e modelo desta tela.
    sel = st.dataframe(
        estilizada,
        hide_index=True,
        width="stretch",
        on_select="rerun", selection_mode="single-row", key="tabela_alertas",
        column_config={
            col_escore: st.column_config.ProgressColumn(
                col_escore, min_value=0.0, max_value=1.0, format="%.2f"),
        },
    )
    _linhas = (sel.get("selection", {}) or {}).get("rows", []) if sel else []
    if _linhas:
        dados.abrir_municipio(int(tabela.iloc[_linhas[0]].cod_ibge), "alertas")
    st.caption(t("alertas.listados", n=len(tabela)))

# --------------------------------------------------------------- honestidade
with st.expander(t("alertas.como_ler")):
    st.markdown(t("alertas.como_ler_texto", corte=numero(corte, 2),
                  obs=dados.mes_por_extenso(obs_ano, obs_mes),
                  antecedencia=dados.antecedencia(h)))
