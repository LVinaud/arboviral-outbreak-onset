"""Leitura dos artefatos que o pipeline produz.

Tudo aqui é cacheado pelo Streamlit: os parquets são pequenos (o maior tem
7,4 MB) e não mudam durante uma sessão, então vale carregar uma vez e manter.

Uma regra: este módulo lê arquivos e devolve DataFrames. Ele não sabe o que é
um surto, não decide limiar e não formata nada para a tela. Quem faz isso são
as telas e o `lib/modelos.py`.

Doenças, definições, modelos, faixas e situações circulam como códigos
("dengue", "rf", "alto"); o nome no idioma da tela sai das funções `nome_*`.

Onde ficam os arquivos: ver `arquivo`.
"""
import os
from pathlib import Path

import pandas as pd
import streamlit as st

from i18n import mes_extenso, numero, t

RAIZ = Path(__file__).resolve().parents[2]

# Os arquivos que o app lê têm sempre o mesmo caminho relativo, com as pastas
# train/ (o que o 03_train grava), master/ e lookup/. Na máquina de quem roda o
# pipeline, eles estão no data/ do repositório. Num clone sem data/train/, como
# o do Streamlit Community Cloud, cada arquivo que falta é baixado do
# repositório de dados público no Hugging Face Hub, que tem o mesmo layout e é
# atualizado pelo deploy/publicar.py. ARBOVIRAL_DADOS troca a pasta local e
# ARBOVIRAL_HF_REPO troca o repositório; ARBOVIRAL_HF_REPO vazio desliga o
# download.
HF_REPO_PADRAO = "LVinaud/arboviral-alerta-dados"
DIR_DADOS = Path(os.environ.get("ARBOVIRAL_DADOS") or RAIZ / "data")
HF_REPO = os.environ.get("ARBOVIRAL_HF_REPO", HF_REPO_PADRAO).strip() or None


def arquivo(relativo: str) -> Path | None:
    """Caminho local de um arquivo de dados, ou None se ele não existir.

    Usa a cópia local quando há uma; senão, baixa do repositório de dados
    (e o Hugging Face guarda em cache, então só a primeira vez é lenta)."""
    local = DIR_DADOS / relativo
    if local.exists():
        return local
    if HF_REPO is None:
        return None
    from huggingface_hub import hf_hub_download
    from huggingface_hub.errors import EntryNotFoundError

    try:
        return Path(hf_hub_download(HF_REPO, relativo, repo_type="dataset"))
    except EntryNotFoundError:
        return None


def ler_parquet(relativo: str, **kw) -> pd.DataFrame:
    caminho = arquivo(relativo)
    if caminho is None:
        raise FileNotFoundError(
            f"{relativo} não está em {DIR_DADOS}"
            + (f" nem em {HF_REPO}" if HF_REPO else
               "; rode o pipeline ou defina ARBOVIRAL_HF_REPO"))
    return pd.read_parquet(caminho, **kw)


DOENCAS = ["dengue", "zika", "chikungunya", "fa"]
DEFINICOES = ["inc100", "inc300", "canal", "zscore"]
# Ordem em que os modelos aparecem nos seletores. O padrão de cada doença está
# em MODELO_PADRAO.
MODELOS = ["rf", "xgb", "lgbm", "logreg"]


def nome_doenca(doenca: str) -> str:
    return t(f"doenca.{doenca}")


def doenca_na_frase(doenca: str) -> str:
    """O nome no meio de uma frase: "casos de dengue", "Zika cases"."""
    return t(f"doenca_minuscula.{doenca}")


def nome_definicao(definicao: str) -> str:
    return t(f"definicao.{definicao}")


def nome_modelo(modelo: str) -> str:
    return t(f"modelo.{modelo}")


# Situação do município no último mês com dados. É a distinção central do
# trabalho: um alerta para quem já está em surto confirma o que a equipe sabe;
# para quem não está, é o único que ainda deixa tempo de agir.
EM_SURTO = "em_surto"
SEM_SURTO = "sem_surto"
SEM_DADO = "sem_dado"


def situacao_de(em_surto) -> str:
    if pd.isna(em_surto):
        return SEM_DADO
    return EM_SURTO if int(em_surto) == 1 else SEM_SURTO


def nome_situacao(situacao: str) -> str:
    return t(f"situacao.{situacao}")


# Faixas, da mais grave para a mais leve. Os pontos onde cada uma começa NÃO
# são fixos: dependem do corte da combinação (ver `cortes_faixa`).
NOMES_FAIXA = ["critico", "alto", "moderado", "baixo"]


def nome_faixa(faixa: str) -> str:
    return t(f"faixa.{faixa}")


def cortes_faixa(corte: float) -> dict[str, float]:
    """Onde cada faixa começa, a partir do corte da combinação.

    O corte é o escore a partir do qual aquele modelo prevê surto naquela
    antecedência, e ele varia muito: 0,10 para o XGBoost seis meses à frente,
    0,55 para a floresta aleatória um mês à frente. Faixas fixas em 0,25, 0,50 e
    0,75 davam resultados contraditórios, com um município marcado "Moderado"
    no mapa e "surto previsto" na mesma tela.

    Então a faixa acompanha o corte, com a mesma regra da versão anterior da
    plataforma:
      alto      começa no corte, onde o modelo passa a prever surto;
      critico   começa no meio do caminho entre o corte e 1;
      moderado  começa na metade do corte;
      baixo     é o que fica abaixo disso.
    O corte é limitado a 0,05–0,95 para as faixas nunca colapsarem.
    """
    c = min(max(float(corte), 0.05), 0.95)
    return {"critico": c + (1 - c) / 2, "alto": c, "moderado": c / 2, "baixo": 0.0}


# Cores das faixas, as mesmas da versão anterior da plataforma: cor forte para
# texto e marcas, fundo claro e borda para etiquetas e cartões. A cor nunca
# aparece sozinha: o nome da faixa vai sempre junto.
CORES_FAIXA = {
    "critico":  {"cor": "#dc2626", "fundo": "#fef2f2", "borda": "#fecaca"},
    "alto":     {"cor": "#ea580c", "fundo": "#fff7ed", "borda": "#fed7aa"},
    "moderado": {"cor": "#a16207", "fundo": "#fefce8", "borda": "#fde68a"},
    "baixo":    {"cor": "#15803d", "fundo": "#f0fdf4", "borda": "#bbf7d0"},
}


def estilo_faixa(nome_exibido) -> str:
    """CSS de uma célula de tabela com o nome da faixa (para pandas Styler).

    Recebe o nome já traduzido, que é o que a tabela mostra."""
    codigo = {nome_faixa(f): f for f in NOMES_FAIXA}.get(nome_exibido)
    c = CORES_FAIXA.get(codigo)
    if not c:
        return ""
    return f"color: {c['cor']}; background-color: {c['fundo']}; font-weight: 600"


def intervalo_faixa(faixa: str, corte: float) -> str:
    """Intervalo de escore de uma faixa, em texto, para esta combinação."""
    i = {k: numero(v, 2) for k, v in cortes_faixa(corte).items()}
    return {
        "critico": t("faixa.a_partir_de", a=i["critico"]),
        "alto": t("faixa.de_a", a=i["alto"], b=i["critico"]),
        "moderado": t("faixa.de_a", a=i["moderado"], b=i["alto"]),
        "baixo": t("faixa.abaixo_de", a=i["moderado"]),
    }[faixa]


def cartoes_faixa(contagens: dict, corte: float) -> str:
    """Quatro cartões coloridos, do mais grave ao mais leve, com quantos
    municípios estão em cada faixa, o intervalo de escore e a ação curta."""
    partes = []
    for faixa in NOMES_FAIXA:
        c = CORES_FAIXA[faixa]
        n = int(contagens.get(faixa, 0))
        rotulo = t("comum.municipio") if n == 1 else t("comum.municipios")
        partes.append(
            f"<div style='flex:1 1 150px;background:{c['fundo']};"
            f"border:1px solid {c['borda']};border-left:5px solid {c['cor']};"
            f"border-radius:8px;padding:10px 14px'>"
            f"<div style='color:{c['cor']};font-size:12px;font-weight:700;"
            f"letter-spacing:.06em;text-transform:uppercase'>{nome_faixa(faixa)}</div>"
            f"<div style='color:{c['cor']};font-size:28px;font-weight:700;"
            f"line-height:1.2'>{n}</div>"
            f"<div style='color:#475569;font-size:12px'>"
            f"{t('faixa.cartao_rodape', rotulo=rotulo, intervalo=intervalo_faixa(faixa, corte))}"
            f"</div>"
            f"<div style='color:#0f172a;font-size:12px;font-weight:600;"
            f"margin-top:4px'>{t(f'acao_curta.{faixa}')}</div></div>"
        )
    return ("<div style='display:flex;flex-wrap:wrap;gap:10px;margin:6px 0 4px'>"
            + "".join(partes) + "</div>")


# O que costuma fazer sentido em cada faixa está em i18n/comum.py
# ("acao.<faixa>"), adaptado dos textos da versão anterior da plataforma. São
# posturas de preparo diante de um alerta, não recomendações tiradas do modelo:
# o modelo diz onde olhar, não o que causa surto nem o que o evita.
def acao_faixa(faixa: str) -> str:
    return t(f"acao.{faixa}")


def aviso_apoio() -> str:
    return f"{t('aviso.titulo')} {t('aviso.corpo')}"


def em_cada(x: float) -> str:
    """Proporção como contagem: "5 em cada 10", ou "1 em cada 4" abaixo de 30%,
    onde arredondar para décimos exageraria (26% viraria "3 em cada 10")."""
    if x <= 0:
        return t("comum.nenhum")
    if x < 0.3:
        return t("comum.um_em_cada", n=round(1 / x))
    return t("comum.n_em_cada_10", n=round(10 * x))


def meses_ate(ano: int, mes: int, hoje=None) -> int:
    """Meses inteiros de hoje até o mês previsto. Negativo se já passou.

    É o tempo real de preparo, menor que a antecedência do modelo: a
    antecedência conta a partir do último mês com dados, que fica meses atrás
    de hoje.
    """
    import datetime as _dt
    hoje = hoje or _dt.date.today()
    return (int(ano) - hoje.year) * 12 + (int(mes) - hoje.month)


def frase_prazo(meses: int) -> str:
    """O que dá para fazer com o tempo que falta até o mês previsto."""
    if meses < 0:
        return t("prazo.passou_um") if meses == -1 else t("prazo.passou_n", n=-meses)
    if meses == 0:
        return t("prazo.agora")
    chave = "prazo.curto" if meses <= 2 else "prazo.longo"
    return t(chave, tempo=antecedencia(meses))


def precisao_de(doenca: str, definicao: str, h: int, modelo: str) -> float | None:
    """Precisão dos alertas desta combinação nos anos de teste, com o corte de
    cada ano escolhido nos outros (ver Seção 7 do 03_train)."""
    lim = limiares()
    if lim is None or "precisao_fora_do_ano" not in lim.columns:
        return None
    r = lim[(lim.disease == doenca) & (lim.definition == definicao)
            & (lim.h == h) & (lim.model == modelo)]
    return float(r.precisao_fora_do_ano.iloc[0]) if len(r) else None


def faixa_de(p: float, corte: float) -> str:
    """Faixa de risco de um escore, dado o corte da combinação."""
    for faixa, inicio in cortes_faixa(corte).items():
        if p >= inicio:
            return faixa
    return "baixo"


@st.cache_data(show_spinner=False)
def municipios() -> pd.DataFrame:
    """Código, nome e população mais recente de cada município."""
    m = ler_parquet("master/municipio_mes.parquet",
                    columns=["cod_ibge", "municipio", "ano", "mes", "pop_residente"])
    ultimo = m.sort_values(["ano", "mes"]).groupby("cod_ibge").tail(1)
    return ultimo[["cod_ibge", "municipio", "pop_residente"]].reset_index(drop=True)


@st.cache_data(show_spinner=False)
def rotulos() -> pd.DataFrame:
    """As dezesseis colunas de surto, uma por doença e definição."""
    return ler_parquet("master/labels.parquet")


@st.cache_data(show_spinner=False)
def previsoes(doenca: str, definicao: str, h: int) -> pd.DataFrame | None:
    """Previsões de produção para os meses cujo desfecho ainda não existe.

    Devolve None quando a combinação não foi treinada, o que acontece nas seis
    que nunca registram surto em série nenhuma.
    """
    caminho = arquivo(f"train/predictions_producao/{doenca}_{definicao}_h{h}.parquet")
    return None if caminho is None else pd.read_parquet(caminho)


def _oferecidas() -> pd.DataFrame | None:
    """Linhas do arquivo de cortes que o aplicativo pode mostrar.

    O `03_train` marca `oferecer` quando o modelo teve AUROC médio de pelo
    menos 0,70 nos anos de teste. Um arquivo antigo, sem essa coluna, é aceito
    por inteiro.
    """
    lim = limiares()
    if lim is None:
        return None
    return lim[lim["oferecer"]] if "oferecer" in lim.columns else lim


@st.cache_data(show_spinner=False)
def combinacoes_disponiveis() -> pd.DataFrame:
    """Combinações de doença, definição e antecedência que o app oferece.

    Duas regras, as duas decididas no `03_train` e gravadas no arquivo de
    cortes:

    1. Validação. Precisa ter havido surto em pelo menos um dos anos de teste
       (2022 a 2024); sem isso não há como saber se o modelo acerta. Tira
       febre amarela inteira e zika com as definições por incidência.
    2. Utilidade. Pelo menos um modelo precisa ter AUROC médio de 0,70 ou
       mais. Abaixo disso o modelo ordena os municípios pouco melhor que o
       acaso. Tira dengue com canal endêmico e escore padronizado de 4 a 6
       meses, e chikungunya com as definições por incidência nas antecedências
       longas.

    Das 90 combinações treinadas, 48 ficam.

    Sai só do arquivo de cortes, sem listar a pasta de previsões: num servidor
    sem os dados, listar a pasta obrigaria a baixar as 90 tabelas antes de
    abrir a primeira tela. A previsão de cada combinação é lida quando pedida.
    """
    ok = _oferecidas()
    if ok is None:
        return pd.DataFrame(columns=["doenca", "definicao", "h"])
    return (ok[["disease", "definition", "h"]].drop_duplicates()
            .rename(columns={"disease": "doenca", "definition": "definicao"})
            .astype({"h": int}).reset_index(drop=True))


def modelos_oferecidos(doenca: str, definicao: str, h: int) -> list[str]:
    """Modelos que passam na regra de utilidade nesta combinação, na ordem de
    MODELOS. Em algumas combinações a regressão logística, ou até um modelo de
    árvores, fica abaixo de 0,70 e não aparece no seletor."""
    ok = _oferecidas()
    if ok is None:
        return list(MODELOS)
    presentes = set(ok[(ok.disease == doenca) & (ok.definition == definicao)
                       & (ok.h == int(h))].model)
    return [m for m in MODELOS if m in presentes]


@st.cache_data(show_spinner=False)
def features() -> pd.DataFrame:
    """A matriz de 125 preditores, exatamente a que treinou os modelos.

    É o que o SHAP explica. Vem pronta do `03_train` para o app não precisar
    reconstruí-la, o que levaria cerca de trinta segundos por sessão.
    """
    return ler_parquet("train/features.parquet")


def mes_por_extenso(ano: int, mes: int) -> str:
    return mes_extenso(ano, mes)


@st.cache_data(show_spinner=False)
def limiares() -> pd.DataFrame | None:
    """Ponto de operação por doença, definição, modelo e horizonte.

    Calculado pelo `03_train` maximizando F1 dentro de cada fold e agregando
    pela mediana. Cada modelo espalha os escores de um jeito (corte mediano de
    0,10 no LightGBM a 0,80 na regressão logística), e nos modelos de árvores
    o corte cai com a antecedência: no Random Forest, de 0,60 em h=1 para 0,30
    em h=6.
    """
    caminho = arquivo("train/limiares_operacao.parquet")
    return None if caminho is None else pd.read_parquet(caminho)


def limiar_de(doenca: str, definicao: str, h: int, modelo: str) -> float:
    """O corte desta combinação, ou 0,50 se não houver um calculado."""
    lim = limiares()
    if lim is None:
        return 0.50
    r = lim[(lim.disease == doenca) & (lim.definition == definicao)
            & (lim.h == h) & (lim.model == modelo)]
    return float(r.limiar.iloc[0]) if len(r) else 0.50


# Com que definição e modelo cada doença abre. Escolhidos comparando os
# modelos nos anos de teste, com atenção às antecedências de 4 a 6 meses, que
# são as mais usadas:
#   dengue       XGBoost, mais de 100/100 mil hab.  melhor AUROC em todas as
#                antecedências e nas quatro definições (0,837 com 6 meses,
#                contra 0,812 do Random Forest)
#   zika         Random Forest, canal endêmico      AUROC 0,957 com 6 meses,
#                contra 0,868 do XGBoost
#   chikungunya  Random Forest, canal endêmico      melhor AUROC de 1 a 6 meses
# Nas doenças raras o canal endêmico é a escolha natural: as definições
# absolutas quase nunca disparam.
DEFINICAO_PADRAO = {"dengue": "inc100", "zika": "canal", "chikungunya": "canal"}
MODELO_PADRAO = {"dengue": "xgb", "zika": "rf", "chikungunya": "rf"}


def indice_definicao_padrao(doenca: str, opcoes) -> int:
    lista = list(opcoes)
    alvo = DEFINICAO_PADRAO.get(doenca)
    return lista.index(alvo) if alvo in lista else 0


def indice_modelo_padrao(doenca: str, opcoes) -> int:
    lista = list(opcoes)
    alvo = MODELO_PADRAO.get(doenca)
    return lista.index(alvo) if alvo in lista else 0


def seletor(rotulo: str, opcoes, chave: str, padrao: int = 0, **kw):
    """Selectbox que lembra a escolha entre telas e não perde cliques.

    A escolha fica em `st.session_state[chave]` (por exemplo "cfg_modelo"), que
    sobrevive à troca de tela. O widget usa uma chave própria e fixa
    ("w_cfg_modelo"): se a identidade dele dependesse da posição inicial, como
    antes, cada mudança alterava essa posição e o Streamlit tratava o seletor
    como novo, descartando a escolha seguinte do usuário. A chave fixa também
    mantém a escolha quando o idioma muda e o rótulo do seletor muda junto.

    Se o valor guardado não está entre as opções (por exemplo, uma definição
    que não existe para a doença escolhida), cai no padrão.
    """
    opcoes = list(opcoes)
    wkey = f"w_{chave}"
    atual = st.session_state.get(wkey, st.session_state.get(chave))
    if atual not in opcoes:
        atual = opcoes[padrao] if opcoes else None
    st.session_state[wkey] = atual
    valor = st.selectbox(rotulo, opcoes, key=wkey, **kw)
    st.session_state[chave] = valor
    return valor


# Antecedência com que o aplicativo abre. Seis meses é o horizonte mais usado:
# é o tempo de comprar insumos, contratar e planejar uma campanha.
ANTECEDENCIA_PADRAO = 6


def seletor_antecedencia(opcoes, chave: str = "cfg_h", padrao: int = ANTECEDENCIA_PADRAO):
    """Seletor de antecedência que, se a escolhida não existe na combinação,
    vai para a mais próxima e avisa. Sem isso, quem estava em 6 meses e
    trocasse para uma definição que só vai até 3 cairia em 1 mês sem saber.
    Sem escolha anterior, abre em `padrao`, ou na mais próxima.

    As telas de previsão compartilham a chave "cfg_h"; a de desempenho usa uma
    própria, para abrir em 1 mês sem mexer nas outras."""
    hs = list(opcoes)
    pedido = st.session_state.get(f"w_{chave}", st.session_state.get(chave))
    alvo = padrao if pedido is None else int(pedido)
    indice = 0
    if hs:
        indice = min(range(len(hs)), key=lambda i: abs(int(hs[i]) - alvo))
    h = seletor(t("sel.antecedencia"), hs, chave, indice, format_func=antecedencia)
    if pedido is not None and int(pedido) not in [int(x) for x in hs]:
        st.caption(t("sel.antecedencia_indisponivel", pedido=antecedencia(pedido),
                     mostrada=antecedencia(h)))
    return h


def seletor_modelo(doenca: str, opcoes):
    """Seletor de modelo que avisa quando o modelo escolhido não está entre os
    oferecidos nesta combinação e abre no padrão da doença."""
    pedido = st.session_state.get("w_cfg_modelo", st.session_state.get("cfg_modelo"))
    tipo = seletor(t("sel.modelo"), opcoes, "cfg_modelo",
                   indice_modelo_padrao(doenca, opcoes), format_func=nome_modelo)
    if pedido is not None and pedido not in opcoes:
        st.caption(t("sel.modelo_indisponivel", modelo=nome_modelo(pedido)))
    return tipo


def seletores_previsao(rotulo_definicao: str = "sel.definicao"):
    """Os quatro seletores das telas de previsão (doença, definição,
    antecedência e modelo), lado a lado. Devolve os quatro valores.

    As telas de alertas, estado e município usavam o mesmo bloco copiado três
    vezes; aqui ele fica num lugar só."""
    disponiveis = combinacoes_disponiveis()
    c1, c2, c3, c4 = st.columns(4)
    doencas_ok = [d for d in DOENCAS if d in set(disponiveis.doenca)]
    anterior = st.session_state.get("cfg_doenca")
    with c1:
        doenca = seletor(t("sel.doenca"), doencas_ok, "cfg_doenca", format_func=nome_doenca)
    ao_trocar_doenca(anterior, doenca)

    defs_ok = sorted(set(disponiveis[disponiveis.doenca == doenca].definicao))
    with c2:
        definicao = seletor(t(rotulo_definicao), defs_ok, "cfg_definicao",
                            indice_definicao_padrao(doenca, defs_ok),
                            format_func=nome_definicao)
    hs_ok = sorted(set(disponiveis[(disponiveis.doenca == doenca)
                                   & (disponiveis.definicao == definicao)].h))
    with c3:
        h = seletor_antecedencia(hs_ok)
    with c4:
        tipo = seletor_modelo(doenca, modelos_oferecidos(doenca, definicao, h))
    return doenca, definicao, h, tipo


def abrir_municipio(cod_ibge: int, origem: str) -> None:
    """Leva para a tela do município, na configuração atual.

    Doença, definição, antecedência e modelo já estão na sessão (os seletores
    os gravam), então basta dizer qual município abrir. Pelo código IBGE, e não
    pelo nome: nome de município não é chave, e dentro do estado há nomes que
    só diferem por acento. `origem` é um código ("alertas", "mapa", "top15",
    "vizinhos:<nome>") que a tela do município traduz.
    """
    st.session_state["ir_para_municipio"] = int(cod_ibge)
    st.session_state["origem_municipio"] = origem
    st.switch_page("screens/municipio.py")


def ao_trocar_doenca(anterior, doenca: str) -> None:
    """Se o usuário trocou de doença, definição e modelo voltam ao padrão dela.

    Sem isso, quem estava vendo dengue com XGBoost e mudasse para zika
    continuaria no XGBoost, que é justamente o modelo mais fraco para zika.
    A antecedência é mantida, porque ela não depende da doença.
    """
    if anterior is not None and anterior != doenca:
        for k in ("cfg_definicao", "w_cfg_definicao", "cfg_modelo", "w_cfg_modelo"):
            st.session_state.pop(k, None)


def antecedencia(h: int) -> str:
    return t("comum.um_mes") if int(h) == 1 else t("comum.n_meses", n=int(h))


def frase_corte(h: int, corte: float) -> str:
    """O corte explicado em palavras, para a tela nunca dizer "limiar".

    Gestor não precisa saber o que é ponto de operação; precisa saber a partir
    de que escore o modelo está dizendo "vem surto" naquela antecedência.
    """
    return t("comum.frase_corte", antecedencia=antecedencia(h), corte=numero(corte, 2))


@st.cache_data(show_spinner=False)
def coordenadas() -> pd.DataFrame:
    """Latitude e longitude de cada município, do lookup das estações INMET."""
    d = pd.read_excel(arquivo("lookup/municipios_sp_estacoes_inmet.xlsx"))
    d = d.rename(columns={"Código Município Completo": "cod_ibge",
                          "LATITUDE": "lat", "LONGITUDE": "lon"})
    return d[["cod_ibge", "lat", "lon"]].dropna()
