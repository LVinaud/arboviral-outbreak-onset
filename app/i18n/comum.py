"""Textos compartilhados entre as telas: navegação, nomes de doenças,
definições, modelos e faixas, seletores, ações por faixa e avisos."""

PT = {
    # --------------------------------------------------------- aplicativo
    "app.titulo_aba": "Alerta de arboviroses",
    "app.aviso_curto": "**As previsões podem estar erradas.** Use o sistema como "
                       "apoio à decisão, não como a decisão em si.",
    "app.rodape": "Previsões geradas por modelos treinados com dezesseis fontes "
                  "públicas brasileiras. O escore não é a probabilidade de um surto "
                  "ocorrer: é a posição do município na fila de atenção deste mês.",
    "nav.alertas": "Alertas do mês",
    "nav.estado": "Visão do estado",
    "nav.municipio": "Município",
    "nav.desempenho": "Desempenho medido",
    "nav.sobre": "Sobre",

    # ------------------------------------------------------------ códigos
    "doenca.dengue": "Dengue",
    "doenca.zika": "Zika",
    "doenca.chikungunya": "Chikungunya",
    "doenca.fa": "Febre amarela",
    # Nome no meio de uma frase ("casos de dengue").
    "doenca_minuscula.dengue": "dengue",
    "doenca_minuscula.zika": "zika",
    "doenca_minuscula.chikungunya": "chikungunya",
    "doenca_minuscula.fa": "febre amarela",
    "definicao.inc100": "Mais de 100 casos por 100 mil habitantes",
    "definicao.inc300": "Mais de 300 casos por 100 mil habitantes",
    "definicao.canal": "Acima do normal histórico do município (canal endêmico)",
    "definicao.zscore": "Mais de dois desvios acima da média do município",
    "modelo.rf": "Random Forest",
    "modelo.xgb": "XGBoost",
    "modelo.lgbm": "LightGBM",
    "modelo.logreg": "Regressão logística",
    "faixa.critico": "Crítico",
    "faixa.alto": "Alto",
    "faixa.moderado": "Moderado",
    "faixa.baixo": "Baixo",
    "faixa.sem_previsao": "sem previsão",
    "situacao.em_surto": "Já em surto",
    "situacao.sem_surto": "Não está em surto",
    "situacao.sem_dado": "Sem dado",

    # ------------------------------------------------------------ formatos
    "comum.mes_ano": "{mes} de {ano}",
    "comum.um_mes": "1 mês",
    "comum.n_meses": "{n} meses",
    "comum.sem_dado": "sem dado",
    "comum.municipio": "município",
    "comum.municipios": "municípios",
    "comum.nenhum": "nenhum",
    "comum.um_em_cada": "1 em cada {n}",
    "comum.n_em_cada_10": "{n} em cada 10",
    "comum.sim": "Sim",
    "comum.nao": "Não",

    # ------------------------------------------------------------ seletores
    "sel.doenca": "Doença",
    "sel.definicao": "Definição de surto",
    "sel.o_que_conta": "O que conta como surto",
    "sel.antecedencia": "Horizonte (meses à frente)",
    "sel.modelo": "Modelo",
    "sel.municipio": "Município",
    "sel.antecedencia_indisponivel": "{pedido} não está disponível nesta combinação; "
                                     "mostrando {mostrada}.",
    "sel.modelo_indisponivel": "{modelo} não está disponível nesta combinação: não "
                               "passou no critério de qualidade (aba Sobre).",
    "comum.frase_corte": "{antecedencia} à frente do mês dos dados, este modelo prevê "
                         "surto a partir do escore {corte}",

    # ------------------------------------------------------------ faixas
    "faixa.a_partir_de": "a partir de {a}",
    "faixa.de_a": "de {a} a {b}",
    "faixa.abaixo_de": "abaixo de {a}",
    "faixa.cartao_rodape": "{rotulo} · escore {intervalo}",
    "acao_curta.critico": "Acionar o plano de contingência",
    "acao_curta.alto": "Preparar insumos e equipe",
    "acao_curta.moderado": "Acompanhar de perto",
    "acao_curta.baixo": "Manter a notificação em dia",
    "acao.critico": (
        "Sinal forte, bem acima do escore a partir do qual o modelo prevê "
        "surto. Além do preparo, costuma fazer sentido acionar o plano de "
        "contingência do município e comunicar a vigilância regional, para que "
        "a resposta não dependa só da capacidade local."
    ),
    "acao.alto": (
        "O modelo prevê surto. Com antecedência, cabe preparar: revisar o "
        "estoque de insumos, dimensionar a equipe, organizar ações de campo, "
        "como visitas e eliminação de criadouros, e alinhar com a vigilância "
        "regional."
    ),
    "acao.moderado": (
        "Há sinal, mas abaixo do escore a partir do qual o modelo prevê surto. "
        "É o momento de olhar, não de mobilizar: vale acompanhar se o escore "
        "sobe nos próximos meses e conversar com a equipe de vigilância sobre "
        "o que ela está vendo no município."
    ),
    "acao.baixo": (
        "O modelo não vê sinal de surto para o mês previsto. Isso não é garantia de "
        "tranquilidade: o sistema não captura todos os surtos, e parte deles "
        "escapa. O que mais atrapalha a previsão é o atraso de notificação, "
        "então manter o SINAN em dia é o que mais protege a leitura dos "
        "próximos meses."
    ),
    "acao.ressalva": (
        "Estas são posturas de preparo diante de um alerta, não recomendações "
        "tiradas do modelo. O protocolo do seu município e a orientação da "
        "vigilância valem mais do que qualquer coisa escrita aqui."
    ),
    "aviso.titulo": "Esta previsão pode estar errada.",
    "aviso.corpo": "Use o sistema como apoio à decisão, junto com o que a equipe de "
                   "vigilância sabe do município, e nunca como a decisão em si.",
    "prazo.passou_um": "O mês previsto já passou há 1 mês: a previsão mostra o que o "
                       "modelo teria dito na época.",
    "prazo.passou_n": "O mês previsto já passou há {n} meses: a previsão mostra o que "
                      "o modelo teria dito na época.",
    "prazo.agora": "O mês previsto é o mês atual: dá para reforçar o que já está em "
                   "campo, não para preparar.",
    "prazo.curto": "Faltam {tempo} para o mês previsto: dá para mobilizar o que já "
                   "existe, não para comprar o que não existe.",
    "prazo.longo": "Faltam {tempo} para o mês previsto: ainda há prazo para o que "
                   "depende de processo, como compra, contratação e convênio.",

    # ------------------------------------------------------------ erros
    "erro.sem_previsoes": "Nenhuma previsão em disco. Rode o `03_train.ipynb`.",
    "erro.sem_previsoes_producao": "Nenhuma previsão em disco. Rode o `03_train.ipynb` "
                                   "com `RODAR_PRODUCAO = True` para gerar "
                                   "`data/train/predictions_producao/`.",
    "erro.nao_treinada": "Combinação não treinada.",
    "erro.modelo_nao_ajustado": "O modelo {modelo} não foi ajustado para esta combinação.",
    "erro.explicacao": "Não foi possível explicar esta previsão: {erro}",

    # ------------------------------------------------------------ histórico
    "hist.ano": "Ano",
    "hist.todos_anos": "Todos os anos",
    "hist.ajustar": "Ajustar a escala a este ano",
    "hist.ajustar_ajuda": "Por padrão, o eixo vai até o maior mês de toda a série, "
                          "para os anos serem comparáveis.",
    "hist.eixo_casos": "Casos confirmados",
    "hist.dica_mes": "Mês",
    "hist.dica_casos": "Casos",
    "hist.nenhum_caso": "Nenhum caso confirmado em toda a série.",
    "hist.pico": "O maior mês da série foi {mes}, com {n} casos.",
    "hist.total": "Total de {ano}: {n} casos",
    "hist.eixo_fixo": "O eixo vai até {teto} casos, o maior mês da série, para "
                      "comparar os anos. {texto}",
    "hist.ano_incompleto": ", somando só {n} meses: o ano ainda não terminou ou os "
                           "meses seguintes ainda não foram consolidados",
    "hist.periodo": "Casos confirmados de {doenca} notificados, de janeiro de 2015 a "
                    "{mes}, o último mês com dados consolidados.",
    "hist.titulo": "Como a {doenca} se comportou no passado",
    "mapa_hist.casos": "casos",
    "mapa_hist.por_100k": "por 100 mil habitantes",
    "mapa_hist.barra": "Casos por<br>100 mil hab.",
    "mapa_hist.mes": "Mês: ",
    "mapa_hist.faixa_0": "menos de 10",
    "mapa_hist.faixa_1": "10 a 100",
    "mapa_hist.faixa_2": "100 a 300",
    "mapa_hist.faixa_3": "300 a 1.000",
    "mapa_hist.faixa_4": "1.000 ou mais",
}

EN = {
    # --------------------------------------------------------- aplicativo
    "app.titulo_aba": "Arbovirus outbreak alert",
    "app.aviso_curto": "**Forecasts can be wrong.** Use the system to support "
                       "decisions, not as the decision itself.",
    "app.rodape": "Forecasts from models trained on sixteen Brazilian public data "
                  "sources. The score is not the probability that an outbreak will "
                  "happen: it is the municipality's place in this month's attention "
                  "queue.",
    "nav.alertas": "This month's alerts",
    "nav.estado": "State overview",
    "nav.municipio": "Municipality",
    "nav.desempenho": "Measured performance",
    "nav.sobre": "About",

    # ------------------------------------------------------------ códigos
    "doenca.dengue": "Dengue",
    "doenca.zika": "Zika",
    "doenca.chikungunya": "Chikungunya",
    "doenca.fa": "Yellow fever",
    "doenca_minuscula.dengue": "dengue",
    "doenca_minuscula.zika": "Zika",
    "doenca_minuscula.chikungunya": "chikungunya",
    "doenca_minuscula.fa": "yellow fever",
    "definicao.inc100": "More than 100 cases per 100,000 residents",
    "definicao.inc300": "More than 300 cases per 100,000 residents",
    "definicao.canal": "Above the municipality's historical range (endemic channel)",
    "definicao.zscore": "More than two standard deviations above the municipality's mean",
    "modelo.rf": "Random Forest",
    "modelo.xgb": "XGBoost",
    "modelo.lgbm": "LightGBM",
    "modelo.logreg": "Logistic regression",
    "faixa.critico": "Critical",
    "faixa.alto": "High",
    "faixa.moderado": "Moderate",
    "faixa.baixo": "Low",
    "faixa.sem_previsao": "no forecast",
    "situacao.em_surto": "Already in outbreak",
    "situacao.sem_surto": "Not in outbreak",
    "situacao.sem_dado": "No data",

    # ------------------------------------------------------------ formatos
    "comum.mes_ano": "{mes} {ano}",
    "comum.um_mes": "1 month",
    "comum.n_meses": "{n} months",
    "comum.sem_dado": "no data",
    "comum.municipio": "municipality",
    "comum.municipios": "municipalities",
    "comum.nenhum": "none",
    "comum.um_em_cada": "1 in every {n}",
    "comum.n_em_cada_10": "{n} in every 10",
    "comum.sim": "Yes",
    "comum.nao": "No",

    # ------------------------------------------------------------ seletores
    "sel.doenca": "Disease",
    "sel.definicao": "Outbreak definition",
    "sel.o_que_conta": "What counts as an outbreak",
    "sel.antecedencia": "Months ahead",
    "sel.modelo": "Model",
    "sel.municipio": "Municipality",
    "sel.antecedencia_indisponivel": "{pedido} is not available for this combination; "
                                     "showing {mostrada}.",
    "sel.modelo_indisponivel": "{modelo} is not available for this combination: it did "
                               "not pass the quality criterion (see About).",
    "comum.frase_corte": "{antecedencia} ahead of the data month, this model forecasts "
                         "an outbreak from a score of {corte}",

    # ------------------------------------------------------------ faixas
    "faixa.a_partir_de": "{a} and above",
    "faixa.de_a": "{a} to {b}",
    "faixa.abaixo_de": "below {a}",
    "faixa.cartao_rodape": "{rotulo} · score {intervalo}",
    "acao_curta.critico": "Activate the contingency plan",
    "acao_curta.alto": "Prepare supplies and staff",
    "acao_curta.moderado": "Watch closely",
    "acao_curta.baixo": "Keep notifications up to date",
    "acao.critico": (
        "Strong signal, well above the score at which the model forecasts an "
        "outbreak. Beyond preparing, it usually makes sense to activate the "
        "municipality's contingency plan and inform regional surveillance, so the "
        "response does not rest on local capacity alone."
    ),
    "acao.alto": (
        "The model forecasts an outbreak. With lead time, preparing is warranted: "
        "review the stock of supplies, size the team, organise field work, such as "
        "home visits and removal of breeding sites, and align with regional "
        "surveillance."
    ),
    "acao.moderado": (
        "There is a signal, but below the score at which the model forecasts an "
        "outbreak. This is a moment to watch, not to mobilise: it is worth "
        "following whether the score rises in the coming months and talking with "
        "the surveillance team about what they are seeing in the municipality."
    ),
    "acao.baixo": (
        "The model sees no outbreak signal for the forecast month. That is not a "
        "guarantee: the system does not catch every outbreak, and some slip "
        "through. What hurts the forecast most is notification delay, so keeping "
        "SINAN up to date is what best protects the reading of the coming months."
    ),
    "acao.ressalva": (
        "These are preparedness postures in the face of an alert, not "
        "recommendations derived from the model. Your municipality's protocol and "
        "surveillance guidance prevail over anything written here."
    ),
    "aviso.titulo": "This forecast can be wrong.",
    "aviso.corpo": "Use the system to support decisions, together with what the "
                   "surveillance team knows about the municipality, and never as the "
                   "decision itself.",
    "prazo.passou_um": "The forecast month was 1 month ago: the forecast shows what "
                       "the model would have said at the time.",
    "prazo.passou_n": "The forecast month was {n} months ago: the forecast shows what "
                      "the model would have said at the time.",
    "prazo.agora": "The forecast month is the current month: there is time to "
                   "reinforce what is already in the field, not to prepare.",
    "prazo.curto": "{tempo} left until the forecast month: enough to mobilise what "
                   "already exists, not to purchase what does not.",
    "prazo.longo": "{tempo} left until the forecast month: there is still time for "
                   "what depends on process, such as purchasing, hiring and agreements.",

    # ------------------------------------------------------------ erros
    "erro.sem_previsoes": "No forecasts on disk. Run `03_train.ipynb`.",
    "erro.sem_previsoes_producao": "No forecasts on disk. Run `03_train.ipynb` with "
                                   "`RODAR_PRODUCAO = True` to generate "
                                   "`data/train/predictions_producao/`.",
    "erro.nao_treinada": "This combination was not trained.",
    "erro.modelo_nao_ajustado": "The {modelo} model was not fitted for this combination.",
    "erro.explicacao": "Could not explain this forecast: {erro}",

    # ------------------------------------------------------------ histórico
    "hist.ano": "Year",
    "hist.todos_anos": "All years",
    "hist.ajustar": "Fit the scale to this year",
    "hist.ajustar_ajuda": "By default the axis goes up to the largest month in the "
                          "whole series, so years can be compared.",
    "hist.eixo_casos": "Confirmed cases",
    "hist.dica_mes": "Month",
    "hist.dica_casos": "Cases",
    "hist.nenhum_caso": "No confirmed cases in the whole series.",
    "hist.pico": "The largest month in the series was {mes}, with {n} cases.",
    "hist.total": "{ano} total: {n} cases",
    "hist.eixo_fixo": "The axis goes up to {teto} cases, the largest month in the "
                      "series, so years can be compared. {texto}",
    "hist.ano_incompleto": ", adding up only {n} months: the year is not over yet or "
                           "the following months have not been consolidated",
    "hist.periodo": "Confirmed {doenca} cases notified from January 2015 to {mes}, "
                    "the last month with consolidated data.",
    "hist.titulo": "How {doenca} behaved in the past",
    "mapa_hist.casos": "cases",
    "mapa_hist.por_100k": "per 100,000 residents",
    "mapa_hist.barra": "Cases per<br>100,000 res.",
    "mapa_hist.mes": "Month: ",
    "mapa_hist.faixa_0": "under 10",
    "mapa_hist.faixa_1": "10 to 100",
    "mapa_hist.faixa_2": "100 to 300",
    "mapa_hist.faixa_3": "300 to 1,000",
    "mapa_hist.faixa_4": "1,000 or more",
}
