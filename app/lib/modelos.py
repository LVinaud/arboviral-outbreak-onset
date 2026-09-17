"""Carregamento dos modelos de produção e explicação por SHAP.

Os modelos ficam em `data/train/models_producao/`, um por doença, definição,
horizonte e tipo. São os que o `03_train` ajusta com toda a série rotulada, ao
contrário dos de `models/`, que são por fold e servem para reproduzir o artigo.

Cuidado ao mexer aqui: a ordem das colunas que o modelo recebe tem que ser a
mesma do treino. O `alinhar_features` existe só para isso e não deve ser
contornado por conveniência.
"""
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
import streamlit as st

from i18n import t
from lib.dados import DIR_MODELOS

EXCLUIR = ["cod_ibge", "ano", "mes", "target", "target_year"]


@st.cache_resource(show_spinner=False)
def carregar_modelo(doenca: str, definicao: str, h: int, tipo: str):
    """Um modelo de produção, cacheado entre execuções da mesma sessão.

    `cache_resource` e não `cache_data`: o objeto é um modelo treinado, não
    serializa bem e não deve ser copiado a cada acesso.
    """
    caminho = DIR_MODELOS / f"{doenca}_{definicao}_h{h}_{tipo}.joblib"
    if not caminho.exists():
        return None
    return joblib.load(caminho)


def _classificador(modelo):
    """O estimador de dentro, quando o modelo é um Pipeline."""
    return modelo.named_steps["clf"] if hasattr(modelo, "named_steps") else modelo


def alinhar_features(modelo, linha: pd.DataFrame) -> pd.DataFrame:
    """Põe as colunas na ordem que o modelo espera.

    Um DataFrame com as mesmas colunas em ordem diferente produz previsão
    silenciosamente errada em alguns estimadores, então isso não é zelo
    excessivo.
    """
    clf = _classificador(modelo)
    esperadas = getattr(clf, "feature_names_in_", None)
    x = linha.drop(columns=[c for c in EXCLUIR if c in linha.columns], errors="ignore")
    if esperadas is None:
        return x.fillna(0)
    faltando = [c for c in esperadas if c not in x.columns]
    for c in faltando:
        x[c] = 0.0
    return x[list(esperadas)].fillna(0)


def prever(modelo, linha: pd.DataFrame) -> float:
    x = alinhar_features(modelo, linha)
    return float(modelo.predict_proba(x)[:, 1][0])


@st.cache_data(show_spinner=False)
def explicar(doenca: str, definicao: str, h: int, tipo: str,
             cod_ibge: int, ano: int, mes: int, _linha: pd.DataFrame,
             topo: int = 10) -> pd.DataFrame | None:
    """Contribuição de cada variável para esta previsão, por SHAP.

    Devolve uma linha por variável, com o valor que ela assumiu e quanto
    empurrou o risco para cima (positivo) ou para baixo (negativo). Só as
    `topo` maiores em módulo.

    Os argumentos soltos existem para o cache ter chave: `_linha` começa com
    underscore para o Streamlit não tentar fazer hash do DataFrame.
    """
    import shap

    modelo = carregar_modelo(doenca, definicao, h, tipo)
    if modelo is None:
        return None
    x = alinhar_features(modelo, _linha)
    clf = _classificador(modelo)

    try:
        if tipo in ("rf", "xgb", "lgbm"):
            explicador = shap.TreeExplainer(clf)
            valores = explicador.shap_values(x)
            # Floresta aleatória devolve uma matriz por classe; queremos a positiva.
            if isinstance(valores, list):
                valores = valores[1]
            valores = np.asarray(valores)
            if valores.ndim == 3:
                valores = valores[:, :, 1]
            base = explicador.expected_value
            base = base[1] if isinstance(base, (list, np.ndarray)) and np.size(base) > 1 else float(np.ravel(base)[0])
        else:
            # Regressão logística: o modelo é um Pipeline com imputação e
            # padronização, então o SHAP linear precisa dos dados já transformados.
            transformado = modelo[:-1].transform(x)
            explicador = shap.LinearExplainer(clf, transformado)
            valores = np.asarray(explicador.shap_values(transformado))
            base = float(np.ravel(explicador.expected_value)[0])
    except Exception as erro:  # noqa: BLE001
        st.caption(t("erro.explicacao", erro=erro))
        return None

    contrib = pd.DataFrame({
        "variavel": list(x.columns),
        "valor": x.iloc[0].to_numpy(),
        "shap": np.ravel(valores)[: x.shape[1]],
    })
    contrib["abs"] = contrib["shap"].abs()
    contrib = contrib.nlargest(topo, "abs").drop(columns="abs")
    contrib.attrs["base"] = base
    return contrib.reset_index(drop=True)
