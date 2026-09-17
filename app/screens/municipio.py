"""Tela: um município, a previsão dele e as razões por trás dela.

O ponto desta tela é que um alerta sem motivo não é discutível. Um gestor que
sabe que a cidade vizinha vem notificando há dois meses, ou que um indicador
está mal medido na região dele, precisa poder pesar isso contra o ranking. Sem
as razões, só resta acreditar ou ignorar.
"""
import pandas as pd
import streamlit as st

import i18n
from i18n import inteiro, maiuscula, numero, t
from lib import comparacao, dados, historico, modelos
from lib.rotulos import rotular

st.title(t("mun.titulo"))

if dados.combinacoes_disponiveis().empty:
    st.error(t("erro.sem_previsoes"))
    st.stop()

muns = dados.municipios().sort_values("municipio")


def _origem_legivel(origem: str | None) -> str:
    """O código que a outra tela gravou ("alertas", "vizinhos:Lucélia") em texto."""
    if not origem:
        return t("mun.origem.outra")
    if origem.startswith("vizinhos:"):
        return t("mun.origem.vizinhos", nome=origem.split(":", 1)[1])
    return t(f"mun.origem.{origem}")


# Município vindo de um clique em outra tela. A configuração (doença,
# definição, antecedência e modelo) já está na sessão, e cada seletor abaixo
# abre no valor guardado (ver dados.seletor).
_cod_sessao = st.session_state.pop("ir_para_municipio", None)
_origem = st.session_state.pop("origem_municipio", None)
_nome_sessao = None
if _cod_sessao is not None:
    _achado = muns[muns.cod_ibge == _cod_sessao]
    if not _achado.empty:
        _nome_sessao = _achado.municipio.iloc[0]
        st.session_state["cfg_municipio"] = _nome_sessao
        st.session_state.pop("w_cfg_municipio", None)

# ---------------------------------------------------------------- seletores
c1, c2 = st.columns([2, 1])
with c1:
    nome = dados.seletor(t("sel.municipio"), muns.municipio.tolist(), "cfg_municipio")
cod = int(muns.loc[muns.municipio == nome, "cod_ibge"].iloc[0])
pop = muns.loc[muns.municipio == nome, "pop_residente"].iloc[0]
with c2:
    st.metric(t("mun.populacao"), inteiro(pop) if pd.notna(pop) else t("comum.sem_dado"))

doenca, definicao, h, tipo = dados.seletores_previsao()

if _nome_sessao:
    st.caption(t("mun.aberto_de", origem=_origem_legivel(_origem)))

# ------------------------------------------------------------------ previsão
prev = dados.previsoes(doenca, definicao, h)
if prev is None:
    st.warning(t("erro.nao_treinada"))
    st.stop()
linha_prev = prev[(prev.cod_ibge == cod) & (prev.model == tipo)]
if linha_prev.empty:
    st.warning(t("mun.sem_previsao"))
    st.stop()
linha_prev = linha_prev.sort_values(["ano", "mes"]).iloc[-1]

obs_ano, obs_mes = int(linha_prev["ano"]), int(linha_prev["mes"])
alvo_ano, alvo_mes = int(linha_prev["ano_alvo"]), int(linha_prev["mes_alvo"])
p = float(linha_prev["proba"])

st.divider()
e1, e0, e2, e3 = st.columns([1, 1, 1, 2])
e1.metric(t("mun.m_escore"), numero(p, 2))
_lim = dados.limiar_de(doenca, definicao, h, tipo)
_ini = {k: numero(v, 2) for k, v in dados.cortes_faixa(_lim).items()}
e0.metric(t("mun.m_faixa"), dados.nome_faixa(dados.faixa_de(p, _lim)),
          help=t("mun.m_faixa_ajuda", critico=_ini["critico"], alto=_ini["alto"],
                 moderado=_ini["moderado"]))
e2.metric(t("mun.m_previsto"), t("comum.sim") if p >= _lim else t("comum.nao"),
          help=t("mun.m_previsto_ajuda", frase=maiuscula(dados.frase_corte(h, _lim))))
e3.metric(t("mun.m_mes"), maiuscula(dados.mes_por_extenso(alvo_ano, alvo_mes)),
          help=t("mun.m_mes_ajuda", obs=dados.mes_por_extenso(obs_ano, obs_mes)))

# Situação no último mês com dados. Só o fato: com antecedência de vários
# meses, um surto previsto pode começar em qualquer mês até o previsto, e um
# surto em curso pode acabar antes dele. Dizer "é um começo" ou "confirma o que
# a equipe já vê" seria afirmar o que a previsão não sabe.
rot = dados.rotulos()
col_rot = f"{doenca}_{definicao}"
situacao = None
if col_rot in rot.columns:
    r = rot[(rot.cod_ibge == cod) & (rot.ano == obs_ano) & (rot.mes == obs_mes)]
    if not r.empty and pd.notna(r[col_rot].iloc[0]):
        situacao = dados.situacao_de(r[col_rot].iloc[0])

_mes_dados = dados.mes_por_extenso(obs_ano, obs_mes)
if situacao == dados.EM_SURTO:
    st.info(t("mun.ja_em_surto", mes=_mes_dados))
elif situacao == dados.SEM_SURTO:
    st.success(t("mun.nao_em_surto", mes=_mes_dados))

# ------------------------------------------------------------------- ações
# O que costuma fazer sentido nesta faixa, na cor dela. Prazo e precisão só
# aparecem quando há alerta, que é quando servem para dimensionar a resposta.
# O prazo conta de hoje até o mês previsto, não a antecedência do modelo.
_faixa = dados.faixa_de(p, _lim)
_cores = dados.CORES_FAIXA[_faixa]
_partes = [dados.acao_faixa(_faixa)]
_prec = dados.precisao_de(doenca, definicao, h, tipo)
if _faixa in ("alto", "critico"):
    _partes.append(dados.frase_prazo(dados.meses_ate(alvo_ano, alvo_mes)))
if _faixa in ("alto", "critico") and _prec is not None:
    _partes.append(t("mun.acao_precisao", n=dados.em_cada(_prec)))
st.markdown(
    f"<div style='background:{_cores['fundo']};border:1px solid {_cores['borda']};"
    f"border-left:5px solid {_cores['cor']};border-radius:8px;padding:14px 18px;"
    "margin:4px 0 12px'>"
    f"<div style='font-size:12px;font-weight:700;letter-spacing:.06em;"
    f"text-transform:uppercase;color:{_cores['cor']}'>"
    f"{t('mun.acao_faixa', faixa=dados.nome_faixa(_faixa))}</div>"
    "<div style='font-size:17px;font-weight:700;color:#0f172a;margin:2px 0 8px'>"
    f"{t('mun.acao_titulo')}</div>"
    + "".join(f"<p style='font-size:14px;color:#1e293b;line-height:1.55;"
              f"margin:0 0 8px'>{texto}</p>" for texto in _partes)
    + f"<p style='font-size:12px;color:#475569;margin:10px 0 0'>"
    f"{t('acao.ressalva')}</p>"
    f"<p style='font-size:13px;font-weight:700;color:#0f172a;margin:6px 0 0'>"
    f"{dados.aviso_apoio()}</p></div>",
    unsafe_allow_html=True,
)

# -------------------------------------------------------------- explicação
# Cores divergentes da paleta de referência do guia de visualização: vermelho
# para o que empurra o risco para cima, azul para o que puxa para baixo. O
# sentido também está no sinal do peso e na direção da barra, não só na cor.
COR_SOBE, COR_DESCE = "#e34948", "#2a78d6"
TINTA, TINTA_2 = "#0f172a", "#475569"


def _valor_legivel(v) -> str:
    """Valor da variável no padrão do idioma e sem casas inúteis."""
    if pd.isna(v):
        return t("comum.sem_dado")
    v = round(float(v), 2)
    if abs(v) >= 1000:
        return inteiro(v)
    if v == int(v):
        return f"{int(v)}"
    texto = numero(v, 2, milhar=False)
    return texto.rstrip("0")


def _barras_shap(contrib: pd.DataFrame) -> str:
    """Lista de variáveis com barras que saem do centro, da que mais mexeu no
    risco, para cima ou para baixo, à que menos mexeu."""
    contrib = contrib.sort_values("shap", key=lambda c: c.abs(), ascending=False)
    maior = float(contrib.shap.abs().max()) or 1.0
    # A barra mais longa ocupa 38% da largura: sobra espaço para o número.
    linhas = []
    for _, r in contrib.iterrows():
        sobe = r.shap > 0
        cor = COR_SOBE if sobe else COR_DESCE
        largura = 38 * abs(r.shap) / maior
        lado, raio = (("left", "0 4px 4px 0") if sobe else ("right", "4px 0 0 4px"))
        peso = ("+" if sobe else "-") + numero(abs(r.shap), 2)
        linhas.append(
            "<div style='display:flex;flex-wrap:wrap;align-items:center;gap:4px 16px;"
            "padding:9px 0;border-top:1px solid #eef2f6'>"
            "<div style='flex:1 1 260px;min-width:0'>"
            f"<div style='font-size:14px;font-weight:600;color:{TINTA}'>"
            f"{rotular(r.variavel)}</div>"
            f"<div style='font-size:12px;color:{TINTA_2}'>"
            f"{t('mun.shap_valor', v=_valor_legivel(r.valor))}</div></div>"
            "<div style='flex:1 1 240px;position:relative;height:24px'>"
            "<div style='position:absolute;left:50%;top:0;bottom:0;width:1px;"
            "background:#cbd5e1'></div>"
            f"<div style='position:absolute;{lado}:50%;top:4px;height:16px;"
            f"width:{largura:.1f}%;background:{cor};border-radius:{raio}'></div>"
            f"<div style='position:absolute;{lado}:calc(50% + {largura:.1f}% + 6px);"
            f"top:2px;font-size:12px;font-weight:700;color:{TINTA}'>{peso}</div>"
            "</div></div>"
        )
    cabecalho = (
        "<div style='display:flex;flex-wrap:wrap;gap:4px 16px;padding-bottom:6px'>"
        "<div style='flex:1 1 260px'></div>"
        "<div style='flex:1 1 240px;display:flex;font-size:12px;font-weight:700'>"
        f"<span style='flex:1;text-align:right;padding-right:8px;color:{COR_DESCE}'>"
        f"{t('mun.shap_desce')}</span>"
        f"<span style='flex:1;text-align:left;padding-left:8px;color:{COR_SOBE}'>"
        f"{t('mun.shap_sobe')}</span>"
        "</div></div>"
    )
    return ("<div style='border:1px solid #e2e8f0;border-radius:10px;"
            "padding:12px 16px 4px;background:#ffffff'>"
            + cabecalho + "".join(linhas) + "</div>")


st.subheader(t("mun.shap_titulo"))

feats = dados.features()
linha_feat = feats[(feats.cod_ibge == cod) & (feats.ano == obs_ano) & (feats.mes == obs_mes)]

if linha_feat.empty:
    st.caption(t("mun.shap_sem_linha"))
else:
    with st.spinner(t("mun.shap_calculando")):
        contrib = modelos.explicar(doenca, definicao, h, tipo, cod, obs_ano, obs_mes,
                                   _linha=linha_feat)
    if contrib is None or contrib.empty:
        st.caption(t("mun.shap_falhou"))
    else:
        st.markdown(t("mun.shap_resumo", cor_sobe=COR_SOBE, cor_desce=COR_DESCE,
                      n_sobe=int((contrib.shap > 0).sum()),
                      n_desce=int((contrib.shap < 0).sum())),
                    unsafe_allow_html=True)
        st.markdown(_barras_shap(contrib), unsafe_allow_html=True)
        st.caption(t("mun.shap_legenda"))

# ---------------------------------------------------------------- histórico
# O mesmo gráfico da tela do estado (historico.grafico_mensal), só com os casos
# deste município.
_nome_doenca = dados.doenca_na_frase(doenca)
st.subheader(maiuscula(t("hist.titulo", doenca=_nome_doenca)))
_serie = historico.serie_municipio(doenca, cod)
if _serie.empty:
    st.caption(t("mun.hist_sem_serie"))
else:
    _ult = _serie.iloc[-1]
    st.caption(t("hist.periodo", doenca=_nome_doenca,
                 mes=dados.mes_por_extenso(int(_ult.ano), int(_ult.mes))))
    st.markdown(f"**{maiuscula(t('mun.hist_mensal', doenca=_nome_doenca, nome=nome))}**")
    historico.grafico_mensal(_serie, "hist_mun")

# ------------------------------------------------------------- comparação
# Posição do município entre os de porte parecido e entre os vizinhos. É
# posição, não causa: ver lib/comparacao.py.
COR_MELHOR, COR_PIOR, COR_CONTEXTO = COR_DESCE, COR_SOBE, "#64748b"


def _numero(v: float, unidade: str) -> str:
    if abs(v) >= 100:
        texto = inteiro(v)
    elif abs(v) < 1:
        texto = numero(v, 2, milhar=False)
    else:
        texto = numero(v, 1, milhar=False)
        texto = texto[:-2] if texto[-2:] in (",0", ".0") else texto
    if not unidade:
        return texto
    return f"{texto}{unidade}" if unidade == "%" else f"{texto} {unidade}"


def _regua(item: dict) -> str:
    """Uma linha: o indicador, os valores e a régua de posição no grupo."""
    ind, pos = item["indicador"], item["posicao"]
    # Abaixo da mediana, a frase diz de quantos pares ele é menor ou pior:
    # "maior que 7% dos pares" é verdade, mas soa como se estivesse acima.
    if ind.maior_melhor is None:
        cor = COR_CONTEXTO
        frase = (t("mun.porte_maior", p=f"{pos:.0f}") if pos >= 50
                 else t("mun.porte_menor", p=f"{100 - pos:.0f}"))
    elif pos >= 50:
        cor, frase = COR_MELHOR, t("mun.porte_melhor", p=f"{pos:.0f}")
    else:
        cor, frase = COR_PIOR, t("mun.porte_pior", p=f"{100 - pos:.0f}")
    linha = t("mun.porte_linha", nome=nome, valor=_numero(item["valor"], ind.unidade),
              mediana=_numero(item["mediana"], ind.unidade), fonte=ind.fonte)
    return (
        "<div style='display:flex;flex-wrap:wrap;align-items:center;gap:4px 16px;"
        "padding:9px 0;border-top:1px solid #eef2f6'>"
        "<div style='flex:1 1 280px;min-width:0'>"
        f"<div style='font-size:14px;font-weight:600;color:{TINTA}'>{ind.rotulo}</div>"
        f"<div style='font-size:12px;color:{TINTA_2}'>{linha}</div></div>"
        "<div style='flex:1 1 240px'>"
        "<div style='position:relative;height:18px'>"
        "<div style='position:absolute;left:0;right:0;top:6px;height:6px;"
        "border-radius:3px;background:#e2e8f0'></div>"
        "<div style='position:absolute;left:50%;top:2px;width:2px;height:14px;"
        "background:#94a3b8'></div>"
        f"<div style='position:absolute;left:{pos:.1f}%;top:2px;width:14px;height:14px;"
        f"transform:translateX(-50%);border-radius:50%;background:{cor};"
        "border:2px solid #ffffff;box-shadow:0 0 0 1px #cbd5e1'></div></div>"
        f"<div style='font-size:12px;font-weight:600;color:{TINTA};margin-top:2px'>"
        f"{frase}</div></div></div>"
    )


def _cabecalho_tema(nome_tema: str, contexto: bool) -> str:
    esq, dir_ = ((t("mun.regua_menor"), t("mun.regua_maior")) if contexto
                 else (t("mun.regua_pior"), t("mun.regua_melhor")))
    cor_esq, cor_dir = ((COR_CONTEXTO, COR_CONTEXTO) if contexto
                        else (COR_PIOR, COR_MELHOR))
    return (
        "<div style='display:flex;flex-wrap:wrap;gap:4px 16px;padding:14px 0 6px'>"
        f"<div style='flex:1 1 280px;font-size:12px;font-weight:700;"
        f"letter-spacing:.06em;text-transform:uppercase;color:{TINTA_2}'>{nome_tema}</div>"
        "<div style='flex:1 1 240px;display:flex;justify-content:space-between;"
        "font-size:12px;font-weight:700'>"
        f"<span style='color:{cor_esq}'>{esq}</span>"
        f"<span style='color:{TINTA_2}'>{t('mun.regua_mediana')}</span>"
        f"<span style='color:{cor_dir}'>{dir_}</span></div></div>"
    )


st.divider()
st.subheader(t("mun.comp_titulo", nome=nome))

# ---- porte parecido
st.markdown(f"#### {t('mun.porte_titulo')}")
_pos = comparacao.posicao_no_grupo(cod)
if _pos["capital"]:
    st.info(t("mun.porte_capital"))
elif not _pos["itens"]:
    st.caption(t("mun.porte_sem_indicadores"))
else:
    _hab = t("mun.porte_habitantes", n=inteiro(pop)) if pd.notna(pop) else ""
    st.markdown(t("mun.porte_intro", nome=nome, hab=_hab,
                  porte=comparacao.nome_porte(_pos["porte"]), n=_pos["n_grupo"],
                  cor_melhor=COR_MELHOR, cor_pior=COR_PIOR),
                unsafe_allow_html=True)
    _blocos = []
    for tema in dict.fromkeys(i["indicador"].tema for i in _pos["itens"]):
        _itens = [i for i in _pos["itens"] if i["indicador"].tema == tema]
        _ctx = _itens[0]["indicador"].maior_melhor is None
        _blocos.append(_cabecalho_tema(_itens[0]["indicador"].nome_tema, _ctx)
                       + "".join(_regua(i) for i in _itens))
    st.markdown("<div style='border:1px solid #e2e8f0;border-radius:10px;"
                "padding:2px 16px 8px;background:#ffffff'>" + "".join(_blocos)
                + "</div>", unsafe_allow_html=True)
    st.caption(t("mun.porte_legenda"))

# ---- vizinhos
st.markdown(f"#### {t('mun.viz_titulo')}")
_viz = comparacao.vizinhos(cod, n=8)
if _viz.empty:
    st.caption(t("mun.viz_sem_coordenadas"))
else:
    _atual = prev[(prev.model == tipo) & (prev.ano == obs_ano) & (prev.mes == obs_mes)]
    _casos = historico.casos_por_mes(doenca)
    _fim = obs_ano * 12 + obs_mes
    _idx = _casos.ano * 12 + _casos.mes
    _recentes = (_casos[(_idx > _fim - 3) & (_idx <= _fim)]
                 .groupby("cod_ibge", as_index=False)["casos"].sum())
    _tab = (_viz.merge(muns[["cod_ibge", "municipio", "pop_residente"]], on="cod_ibge")
            .merge(_atual[["cod_ibge", "proba"]], on="cod_ibge", how="left")
            .merge(_recentes, on="cod_ibge", how="left")
            .sort_values("distancia_km").reset_index(drop=True))
    _tab["incidencia"] = _tab.casos / _tab.pop_residente * 1e5

    _mes_ini = (_fim - 3) % 12 + 1  # primeiro dos três meses, de 1 a 12
    _periodo = (t("mun.viz_periodo_ano", inicio=i18n.nome_mes(_mes_ini),
                  fim=i18n.nome_mes(obs_mes), ano=obs_ano)
                if _mes_ini < obs_mes else
                t("mun.viz_periodo_dois_anos", inicio=i18n.nome_mes(_mes_ini),
                  ano_inicio=obs_ano - 1, fim=i18n.nome_mes(obs_mes), ano=obs_ano))
    st.markdown(t("mun.viz_intro", n=len(_tab) - 1, nome=nome))
    col_pop, col_faixa, col_escore = (t("mun.viz_col_populacao"), t("mun.viz_col_faixa"),
                                      t("mun.viz_col_escore"))
    col_casos = t("mun.viz_col_casos", periodo=_periodo)
    _mostrar = pd.DataFrame({
        t("mun.viz_col_municipio"): [t("mun.viz_este", nome=m) if c == cod else m
                                     for m, c in zip(_tab.municipio, _tab.cod_ibge)],
        t("mun.viz_col_distancia"): [("" if c == cod else f"{d:.0f} km")
                                     for d, c in zip(_tab.distancia_km, _tab.cod_ibge)],
        col_pop: _tab.pop_residente,
        col_faixa: [dados.nome_faixa(dados.faixa_de(x, _lim)) if pd.notna(x)
                    else t("faixa.sem_previsao") for x in _tab.proba],
        col_escore: _tab.proba,
        col_casos: _tab.incidencia,
    })
    _estilo = (_mostrar.style
               .map(dados.estilo_faixa, subset=[col_faixa])
               .format({col_escore: lambda v: numero(v, 2),
                        col_pop: lambda v: (t("comum.sem_dado") if pd.isna(v)
                                            else inteiro(v)),
                        col_casos: lambda v: (t("comum.sem_dado") if pd.isna(v)
                                              else numero(v, 1))}))
    # A chave muda com o município: ao abrir um vizinho, esta mesma tela é
    # desenhada de novo, e uma seleção guardada na chave antiga abriria o
    # vizinho outra vez, sem parar.
    _sel = st.dataframe(
        _estilo, hide_index=True, width="stretch",
        on_select="rerun", selection_mode="single-row", key=f"vizinhos_{cod}",
        column_config={col_escore: st.column_config.ProgressColumn(
            col_escore, min_value=0.0, max_value=1.0, format="%.2f")},
    )
    _linhas = (_sel.get("selection", {}) or {}).get("rows", []) if _sel else []
    if _linhas and int(_tab.cod_ibge.iloc[_linhas[0]]) != cod:
        dados.abrir_municipio(int(_tab.cod_ibge.iloc[_linhas[0]]), f"vizinhos:{nome}")
    st.caption(t("mun.viz_legenda"))
