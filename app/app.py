"""Plataforma de alerta precoce de arboviroses: ponto de entrada.

Regra de arquitetura: o app depende dos artefatos que os notebooks produzem,
e os notebooks não sabem que o app existe. Nada em `notebooks/` importa daqui.

O app lê três coisas, todas geradas pelo `03_train`:
  data/train/predictions_producao/  as previsões dos meses sem desfecho
  data/train/models_producao/       os modelos que o SHAP explica
  data/train/features.parquet       a matriz que alimenta o SHAP

O app é bilíngue (português e inglês); ver `i18n/__init__.py`.

Uso:
    streamlit run app/app.py
"""
import sys
from pathlib import Path

import streamlit as st

# O Streamlit executa este arquivo como script, então `lib`, `i18n` e `screens`
# só são importáveis se o diretório do app estiver no path.
sys.path.insert(0, str(Path(__file__).resolve().parent))

import i18n  # noqa: E402
from i18n import t  # noqa: E402

st.set_page_config(
    page_title=t("app.titulo_aba"),
    page_icon="🦟",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Antes das páginas, para os títulos do menu já saírem no idioma escolhido.
i18n.seletor_idioma()

TELAS = [
    st.Page("screens/alertas.py", title=t("nav.alertas"), icon=":material/warning:",
            default=True),
    st.Page("screens/estado.py", title=t("nav.estado"), icon=":material/map:"),
    st.Page("screens/municipio.py", title=t("nav.municipio"),
            icon=":material/location_city:"),
    st.Page("screens/desempenho.py", title=t("nav.desempenho"), icon=":material/insights:"),
    st.Page("screens/sobre.py", title=t("nav.sobre"), icon=":material/info:"),
]

pagina = st.navigation(TELAS)

st.sidebar.divider()
st.sidebar.markdown(t("app.aviso_curto"))
st.sidebar.caption(t("app.rodape"))

pagina.run()
