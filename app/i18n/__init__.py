"""Idioma da interface: português e inglês.

Todo texto que aparece na tela sai de `t("chave")`. Os textos ficam nos módulos
deste pacote, um por tela mais o `comum`, cada um com um dicionário `PT` e um
`EN` lado a lado, para quem editar uma frase ver a tradução dela logo abaixo.
`tests/test_i18n.py` confere que os dois têm as mesmas chaves e os mesmos
campos variáveis.

Os códigos internos não mudam com o idioma: a doença continua "dengue", o
modelo "rf", a faixa "alto". Só o rótulo exibido muda.

O idioma vem, nesta ordem, do seletor da barra lateral, do parâmetro `?lang=`
do endereço e do idioma do navegador: português se o navegador estiver em
português, inglês em qualquer outro caso.
"""
from string import Formatter

import streamlit as st
from streamlit.runtime.scriptrunner import get_script_run_ctx

from i18n import alertas, comparacao, comum, desempenho, estado, municipio, sobre, variaveis

IDIOMAS = {"pt": "Português", "en": "English"}
# Chave do seletor e nome do parâmetro no endereço.
CHAVE = "lang"

_MODULOS = [comum, alertas, estado, municipio, desempenho, sobre, comparacao, variaveis]


def _juntar(nome: str) -> dict[str, str]:
    tudo: dict[str, str] = {}
    for modulo in _MODULOS:
        parte = getattr(modulo, nome)
        repetidas = set(tudo) & set(parte)
        assert not repetidas, f"chaves repetidas em {modulo.__name__}: {repetidas}"
        tudo.update(parte)
    return tudo


TEXTOS = {"pt": _juntar("PT"), "en": _juntar("EN")}


def idioma_do_navegador() -> str:
    local = (st.context.locale or "").lower()
    return "en" if local and not local.startswith("pt") else "pt"


# Último idioma usado numa execução do app. Só é lido fora de uma execução,
# quando não há sessão para consultar: é o caso do AppTest, que formata as
# opções dos seletores depois que a execução termina. Dentro do app, o idioma
# vem sempre da sessão de quem está usando.
_ultimo = "pt"


def idioma() -> str:
    global _ultimo
    if get_script_run_ctx() is None:
        return _ultimo
    escolhido = st.session_state.get(CHAVE)
    if escolhido not in IDIOMAS:
        escolhido = st.query_params.get(CHAVE)
    _ultimo = escolhido if escolhido in IDIOMAS else idioma_do_navegador()
    return _ultimo


def seletor_idioma() -> str:
    """Seletor no topo da barra lateral, ligado ao `?lang=` do endereço.

    Na primeira execução da sessão, o idioma vem do endereço (`?lang=en`) ou,
    sem ele, do navegador. Depois, o endereço acompanha o seletor, para um
    link copiado abrir no mesmo idioma. É feito à mão, e não com o `bind` do
    Streamlit, porque o `bind` grava o rótulo do botão (`?lang=English`) em vez
    do código."""
    if st.session_state.get(CHAVE) not in IDIOMAS:
        do_endereco = st.query_params.get(CHAVE)
        st.session_state[CHAVE] = (do_endereco if do_endereco in IDIOMAS
                                   else idioma_do_navegador())
    st.sidebar.segmented_control(
        "Idioma / Language", list(IDIOMAS), format_func=IDIOMAS.get,
        required=True, key=CHAVE, width="stretch",
    )
    atual = idioma()
    if st.query_params.get(CHAVE) != atual:
        st.query_params[CHAVE] = atual
    return atual


def t(chave: str, **campos) -> str:
    """Texto no idioma atual. Chave inexistente é erro, para não aparecer um
    código cru na tela sem ninguém perceber."""
    texto = TEXTOS[idioma()].get(chave, TEXTOS["pt"][chave])
    return texto.format(**campos) if campos else texto


def campos_de(texto: str) -> set[str]:
    """Nomes dos campos variáveis de um texto, por exemplo {"mes", "n"}."""
    return {nome for _, nome, _, _ in Formatter().parse(texto) if nome}


# ------------------------------------------------------------------ números
def numero(x: float, casas: int = 2, milhar: bool = True) -> str:
    """Número no padrão do idioma: 1.234,5 em português, 1,234.5 em inglês."""
    texto = f"{x:,.{casas}f}" if milhar else f"{x:.{casas}f}"
    if idioma() == "pt":
        texto = texto.replace(",", "\0").replace(".", ",").replace("\0", ".")
    return texto


def inteiro(n: float) -> str:
    return numero(n, 0)


def pct(fracao: float, casas: int = 0) -> str:
    """Fração como porcentagem: 0,513 vira "51%"."""
    return numero(100 * fracao, casas, milhar=False) + "%"


def locale_altair() -> dict:
    if idioma() == "pt":
        return {"number": {"decimal": ",", "thousands": ".", "grouping": [3],
                           "currency": ["R$ ", ""]}}
    return {"number": {"decimal": ".", "thousands": ",", "grouping": [3],
                       "currency": ["$", ""]}}


def separadores_plotly() -> str:
    """Decimal e milhar para o `separators` do Plotly."""
    return ",." if idioma() == "pt" else ".,"


# -------------------------------------------------------------------- meses
_MESES = {
    "pt": ["janeiro", "fevereiro", "março", "abril", "maio", "junho", "julho",
           "agosto", "setembro", "outubro", "novembro", "dezembro"],
    "en": ["January", "February", "March", "April", "May", "June", "July",
           "August", "September", "October", "November", "December"],
}
_MESES_ABREV = {
    "pt": ["jan", "fev", "mar", "abr", "mai", "jun",
           "jul", "ago", "set", "out", "nov", "dez"],
    "en": ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
           "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"],
}


def nome_mes(mes: int) -> str:
    return _MESES[idioma()][int(mes) - 1]


def meses_abrev() -> list[str]:
    return list(_MESES_ABREV[idioma()])


def mes_extenso(ano: int, mes: int) -> str:
    """"junho de 2026" ou "June 2026"."""
    return t("comum.mes_ano", mes=nome_mes(mes), ano=int(ano))


def maiuscula(texto: str) -> str:
    """Só a primeira letra: "junho de 2026" vira "Junho de 2026"."""
    return texto[:1].upper() + texto[1:]
