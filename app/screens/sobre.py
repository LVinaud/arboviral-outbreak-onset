"""Tela: o que isto é, e principalmente o que não é."""
import streamlit as st

from i18n import numero, t
from lib import dados

st.title(t("sobre.titulo"))

st.markdown(t("sobre.texto"))

# ---------------------------------------------------------- tabela de cortes
lim = dados.limiares()
if lim is not None and len(lim):
    st.markdown(f"### {t('sobre.cortes_titulo')}")
    st.markdown(t("sobre.cortes_intro"))
    c1, c2 = st.columns(2)
    with c1:
        _lim_ok = lim[lim["oferecer"]] if "oferecer" in lim.columns else lim
        d = st.selectbox(t("sel.doenca"),
                         [x for x in dados.DOENCAS if x in set(_lim_ok.disease)],
                         format_func=dados.nome_doenca, key="sobre_doenca")
    with c2:
        defs = sorted(set(_lim_ok[_lim_ok.disease == d].definition))
        df_ = st.selectbox(t("sel.definicao"), defs, format_func=dados.nome_definicao,
                           key="sobre_def")
    sub = lim[(lim.disease == d) & (lim.definition == df_)].copy()
    if "oferecer" in sub.columns:
        sub.loc[~sub["oferecer"], "limiar"] = float("nan")
    tab = (sub.pivot_table(index="model", columns="h", values="limiar", dropna=False)
              .reindex([m for m in dados.MODELOS if m in set(sub.model)]))
    tab.index = [dados.nome_modelo(m) for m in tab.index]
    tab.columns = [dados.antecedencia(h) for h in tab.columns]
    st.dataframe(tab.style.format(lambda v: numero(v, 2), na_rep="—"), width="stretch")
    st.caption(t("sobre.cortes_legenda"))

# ----------------------------------------------------------------- autoria
# Links só aparecem quando preenchidos.
GITHUB = "https://github.com/LVinaud"
LINKEDIN = "https://www.linkedin.com/in/lazaro-vinaud/"

st.markdown(f"### {t('sobre.autoria_titulo')}")
_links = " · ".join(f"[{rotulo}]({url})" for rotulo, url in
                    [("GitHub", GITHUB), ("LinkedIn", LINKEDIN)] if url)
st.markdown(
    f"{t('sobre.autoria_intro')}\n\n"
    f"- **{t('sobre.autoria_aluno')}:** Lázaro Pereira Vinaud Neto"
    f"{(' · ' + _links) if _links else ''}\n"
    f"- **{t('sobre.autoria_orientador')}:** Prof. Dr. André Carlos Ponce de Leon "
    "Ferreira de Carvalho\n"
    f"- **{t('sobre.autoria_colaboracao')}:**\n"
    "    - Márcia Regina Martins Martinez Corso\n"
    "    - Luisa Amélia Paseto\n"
    "    - Marina Carvalho Arruda Barreto"
)
