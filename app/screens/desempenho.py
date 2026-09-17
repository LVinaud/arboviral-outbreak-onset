"""Tela: o que o modelo acerta, medido, e o que ele não acerta.

Existe porque a tela de alertas mostra um escore e um escore sozinho convida a
confiar. No topo ficam os números das combinações que o aplicativo abre por
padrão, com uma explicação curta de cada um. Embaixo, como esses números mudam
de 1 a 6 meses de antecedência.

Precisão e cobertura vêm de `limiares_operacao.parquet` (Seção 7 do
`03_train`), medidas com o corte de cada ano de teste escolhido só nos outros
anos. AUROC e AUPRC são a média dos três anos de teste.
"""
import altair as alt
import pandas as pd
import streamlit as st

import i18n
from i18n import numero, t
from lib import dados

st.title(t("des.titulo"))
st.caption(t("des.legenda_topo"))

# Uma cor por métrica, só para ligar cada cartão à explicação dele; o nome da
# métrica aparece sempre junto. Nenhuma delas é vermelho, laranja, amarelo ou
# verde, que são as cores das faixas de risco. Paleta validada pelo validador
# do guia de visualização (quatro cores, todos os pares).
CORES_METRICA = {
    "precisao": "#1baf7a",
    "cobertura": "#e87ba4",
    "auroc": "#2a78d6",
    "auprc": "#4a3aa7",
}
TINTA, TINTA_2, TINTA_3 = "#0f172a", "#475569", "#64748b"


def _nome_metrica(codigo: str) -> str:
    return t(f"des.metrica.{codigo}")


def _dec(x: float) -> str:
    """Decimal no padrão do idioma; três casas quando o número é muito pequeno."""
    return numero(x, 3 if abs(x) < 0.1 else 2)


def _ladrilho(codigo: str, valor: str, nota: str) -> str:
    cor = CORES_METRICA[codigo]
    return (
        f"<div style='background:{cor}14;border-left:4px solid {cor};"
        f"border-radius:6px;padding:8px 10px'>"
        f"<div style='font-size:12px;font-weight:700;letter-spacing:.05em;"
        f"text-transform:uppercase;color:{TINTA_2}'>{_nome_metrica(codigo)}</div>"
        f"<div style='font-size:26px;font-weight:700;line-height:1.2;"
        f"color:{TINTA}'>{valor}</div>"
        f"<div style='font-size:12px;color:{TINTA_2}'>{nota}</div></div>"
    )


def _cartao(doenca: str, r: pd.Series) -> str:
    ladrilhos = "".join([
        _ladrilho("auroc", _dec(r.auroc), t("des.sorteio", v=numero(0.5, 2))),
        _ladrilho("auprc", _dec(r.auprc), t("des.sorteio", v=_dec(r.taxa_surto))),
        _ladrilho("precisao", i18n.pct(r.precisao_fora_do_ano),
                  t("des.n_alertas", n=dados.em_cada(r.precisao_fora_do_ano))),
        _ladrilho("cobertura", i18n.pct(r.recall_fora_do_ano),
                  t("des.n_surtos", n=dados.em_cada(r.recall_fora_do_ano))),
    ])
    return (
        "<div style='border:1px solid #e2e8f0;border-radius:10px;"
        "padding:14px 16px;background:#ffffff;margin-bottom:8px'>"
        f"<div style='font-size:21px;font-weight:700;color:{TINTA}'>"
        f"{dados.nome_doenca(doenca)}</div>"
        # Três linhas reservadas: a definição da dengue ocupa uma a menos, e
        # sem isso os ladrilhos dela ficariam desalinhados dos outros cartões.
        f"<div style='font-size:13px;color:{TINTA_2};margin:2px 0 12px;"
        "line-height:1.6;min-height:4.8em'>"
        f"{dados.nome_definicao(r.definition)}<br>"
        f"{t('des.modelo', modelo=dados.nome_modelo(r.model))}</div>"
        "<div style='display:grid;grid-template-columns:1fr 1fr;gap:8px'>"
        f"{ladrilhos}</div>"
        f"<div style='font-size:12px;color:{TINTA_3};margin-top:12px'>"
        f"{t('des.rodape_cartao', corte=numero(r.limiar, 2), n=i18n.inteiro(r.n_pos))}"
        "</div></div>"
    )


def _explicacao(codigo: str, pergunta: str, texto: str) -> str:
    cor = CORES_METRICA[codigo]
    return (
        f"<div style='background:{cor}0f;border-left:4px solid {cor};"
        "border-radius:6px;padding:12px 14px'>"
        f"<div style='font-size:15px;font-weight:700;color:{TINTA}'>"
        f"<span style='display:inline-block;width:10px;height:10px;"
        f"border-radius:2px;background:{cor};margin-right:8px'></span>"
        f"{_nome_metrica(codigo)}: {pergunta}</div>"
        f"<div style='font-size:14px;color:{TINTA_2};margin-top:6px;"
        f"line-height:1.5'>{texto}</div></div>"
    )


# ------------------------------------------ as combinações padrão do app
lim = dados.limiares()
colunas_novas = {"auprc", "taxa_surto", "n_pos",
                 "precisao_fora_do_ano", "recall_fora_do_ano"}
if lim is None or not colunas_novas <= set(lim.columns):
    st.warning(t("des.sem_colunas"))
    st.stop()

padroes = []
for doenca, definicao in dados.DEFINICAO_PADRAO.items():
    sub = lim[(lim.disease == doenca) & (lim.definition == definicao)
              & (lim.model == dados.MODELO_PADRAO[doenca])]
    if not sub.empty:
        padroes.append((doenca, sub.set_index("h")))

hs = sorted(set.intersection(*[set(s.index) for _, s in padroes])) if padroes else []
if not hs:
    st.warning(t("des.sem_padroes"))
    st.stop()

st.subheader(t("des.padroes_titulo"))
c_sel, c_txt = st.columns([1, 3], vertical_alignment="bottom")
with c_sel:
    # Seletor próprio desta tela, que abre em 1 mês: aqui interessa ver o
    # melhor caso primeiro, e a escolha não mexe na antecedência das outras.
    h = dados.seletor_antecedencia(hs, chave="desempenho_h", padrao=1)
with c_txt:
    st.caption(t("des.previsoes_com", antecedencia=dados.antecedencia(h)))

linha = {d: s.loc[h] for d, s in padroes}
for coluna, (doenca, _) in zip(st.columns(len(padroes)), padroes):
    with coluna:
        st.markdown(_cartao(doenca, linha[doenca]), unsafe_allow_html=True)

# ------------------------------------------ o que cada número quer dizer
st.markdown(f"#### {t('des.significado')}")

ex = linha.get("dengue", next(iter(linha.values())))
onde = t("des.na_dengue") if "dengue" in linha else t("des.aqui")
blocos = [
    _explicacao("precisao", t("des.precisao_pergunta"),
                t("des.precisao_texto", onde=onde, n=dados.em_cada(ex.precisao_fora_do_ano))),
    _explicacao("cobertura", t("des.cobertura_pergunta"),
                t("des.cobertura_texto", onde=onde, n=dados.em_cada(ex.recall_fora_do_ano))),
    _explicacao("auroc", t("des.auroc_pergunta"),
                t("des.auroc_texto", onde=onde, v=_dec(ex.auroc), n=round(100 * ex.auroc))),
    _explicacao("auprc", t("des.auprc_pergunta"), t("des.auprc_texto")),
]
st.markdown(
    "<div style='display:grid;grid-template-columns:repeat(auto-fit,"
    "minmax(320px,1fr));gap:12px;margin-bottom:12px'>" + "".join(blocos) + "</div>",
    unsafe_allow_html=True,
)

st.markdown(t("des.opostos"))

# Exemplo de AUPRC com a doença em que o sorteio fica mais longe.
raro_d = min(linha, key=lambda d: linha[d].taxa_surto)
raro = linha[raro_d]
vezes = raro.auprc / raro.taxa_surto if raro.taxa_surto else float("nan")
st.markdown(t("des.exemplo_auprc", doenca=dados.doenca_na_frase(raro_d), v=_dec(raro.auprc),
              sorteio=_dec(raro.taxa_surto), vezes=f"{vezes:.0f}"))
if "zika" in linha:
    st.info(t("des.zika_poucos", n=int(linha["zika"].n_pos)))

with st.expander(t("des.como_medido")):
    st.markdown(t("des.como_medido_texto"))

st.divider()

# ------------------------------------------ o que acontece mais longe
st.subheader(t("des.horizonte_titulo"))
st.markdown(t("des.horizonte_intro"))

ORDEM = ["precisao", "cobertura", "auroc", "auprc"]
# Forma além da cor: precisão e cobertura têm cores próximas para quem não
# distingue verde de rosa, e as linhas das duas se cruzam.
FORMAS = {"precisao": ("circle", "●"), "cobertura": ("square", "■"),
          "auroc": ("triangle-up", "▲"), "auprc": ("diamond", "◆")}
COLUNA_METRICA = {"precisao": "precisao_fora_do_ano", "cobertura": "recall_fora_do_ano",
                  "auroc": "auroc", "auprc": "auprc"}


def _longa(serie: pd.DataFrame) -> pd.DataFrame:
    """Uma linha por antecedência e métrica, com o valor já escrito para a dica."""
    linhas = []
    for h_, r in serie.iterrows():
        for codigo in ORDEM:
            v = float(r[COLUNA_METRICA[codigo]])
            texto = i18n.pct(v) if codigo in ("precisao", "cobertura") else _dec(v)
            linhas.append({"h": int(h_), "metrica": codigo, "nome": _nome_metrica(codigo),
                           "valor": v, "meses": dados.antecedencia(h_), "texto": texto})
    return pd.DataFrame(linhas)


def _grafico(doenca: str, serie: pd.DataFrame) -> alt.LayerChart:
    base = alt.Chart(_longa(serie)).encode(
        x=alt.X("h:Q", title=t("des.eixo_antecedencia"), scale=alt.Scale(domain=[1, 6]),
                axis=alt.Axis(values=list(range(1, 7)), format="d")),
        y=alt.Y("valor:Q", title=None, scale=alt.Scale(domain=[0, 1]),
                axis=alt.Axis(format=".1f", tickCount=5)),
        color=alt.Color("metrica:N", legend=None,
                        scale=alt.Scale(domain=ORDEM,
                                        range=[CORES_METRICA[m] for m in ORDEM])),
        tooltip=[alt.Tooltip("nome:N", title=t("des.dica_metrica")),
                 alt.Tooltip("meses:N", title=t("des.dica_antecedencia")),
                 alt.Tooltip("texto:N", title=t("des.dica_valor"))],
    )
    linhas = base.mark_line(strokeWidth=2)
    pontos = base.mark_point(size=70, filled=True, opacity=1).encode(
        shape=alt.Shape("metrica:N", legend=None,
                        scale=alt.Scale(domain=ORDEM,
                                        range=[FORMAS[m][0] for m in ORDEM])))
    escolhida = alt.Chart(pd.DataFrame({"h": [int(h)]})).mark_rule(
        strokeDash=[4, 4], color="#94a3b8", strokeWidth=1.5).encode(x="h:Q")
    return (escolhida + linhas + pontos).properties(
        height=260, title=alt.TitleParams(dados.nome_doenca(doenca), anchor="start",
                                          fontSize=16))


# Legenda única para os três gráficos, com cor e forma.
st.markdown(
    "<div style='display:flex;flex-wrap:wrap;gap:18px;margin:4px 0 8px'>"
    + "".join(f"<span style='font-size:14px;color:{TINTA}'>"
              f"<span style='color:{CORES_METRICA[m]};margin-right:6px'>"
              f"{FORMAS[m][1]}</span>{_nome_metrica(m)}</span>" for m in ORDEM)
    + "</div>",
    unsafe_allow_html=True,
)

for coluna, (doenca, serie) in zip(st.columns(len(padroes)), padroes):
    with coluna:
        st.altair_chart(_grafico(doenca, serie).configure(locale=i18n.locale_altair()),
                        width="stretch")
        a, b = serie.loc[min(serie.index)], serie.loc[max(serie.index)]
        st.caption(t("des.horizonte_resumo",
                     de=dados.antecedencia(min(serie.index)),
                     para=dados.antecedencia(max(serie.index)),
                     p1=i18n.pct(a.precisao_fora_do_ano), p2=i18n.pct(b.precisao_fora_do_ano),
                     c1=i18n.pct(a.recall_fora_do_ano), c2=i18n.pct(b.recall_fora_do_ano),
                     a1=_dec(a.auroc), a2=_dec(b.auroc)))

st.markdown(t("des.ordem_resiste"))

# O porquê de a precisão cair mais que a cobertura, com os números da dengue.
# Só aparece se os números contarem essa história.
if "dengue" in linha:
    serie_d = dict(padroes)["dengue"]
    a, b = serie_d.loc[min(serie_d.index)], serie_d.loc[max(serie_d.index)]
    queda_prec = a.precisao_fora_do_ano - b.precisao_fora_do_ano
    queda_cob = a.recall_fora_do_ano - b.recall_fora_do_ano
    if b.limiar < a.limiar and queda_prec > queda_cob:
        st.markdown(t("des.dengue_precisao",
                      c1=numero(a.limiar, 2), h1=dados.antecedencia(min(serie_d.index)),
                      c2=numero(b.limiar, 2), h2=dados.antecedencia(max(serie_d.index)),
                      r1=i18n.pct(a.recall_fora_do_ano), r2=i18n.pct(b.recall_fora_do_ano),
                      p1=i18n.pct(a.precisao_fora_do_ano),
                      p2=i18n.pct(b.precisao_fora_do_ano)))
