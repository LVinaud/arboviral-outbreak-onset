"""Textos da tela do estado (`screens/estado.py`)."""

PT = {
    "estado.titulo": "Visão do estado",
    "estado.erro_modelo": "Modelo não ajustado para esta combinação.",
    "estado.legenda_topo": "Previsão para **{alvo}**, com dados até {obs}. {corte}.",
    "estado.m_municipios": "Municípios",
    "estado.m_previsto": "Com surto previsto",
    "estado.m_previsto_ajuda": "Municípios com escore igual ou acima de {corte}: {frase}.",
    "estado.m_sem_surto": "Desses, sem surto no momento",
    "estado.m_sem_surto_ajuda": "Os que ainda deixam tempo de agir.",
    "estado.m_mediano": "Escore mediano",

    "estado.mapa_titulo": "Onde o risco está concentrado",
    "estado.sem_coordenadas": "Sem coordenadas disponíveis.",
    "estado.dica_escore": "Escore",
    "estado.dica_populacao": "População",
    "estado.mapa_legenda": "Clique num círculo para abrir o município, com a mesma "
                           "doença, definição, horizonte e modelo. Cor pela faixa de "
                           "risco, tamanho pela população. O mapa mistura de propósito "
                           "uma cidade de meio milhão com uma de três mil habitantes: "
                           "risco e porte são perguntas diferentes, e o tamanho existe "
                           "para que uma cidade pequena no topo seja lida como uma "
                           "cidade pequena no topo.",

    "estado.dist_titulo": "Como os escores se distribuem",
    "estado.dist_subtitulo": "**Distribuição do escore**",
    "estado.contar_por": "Contar por",
    "estado.contar_municipios": "Número de municípios",
    "estado.contar_populacao": "População",
    "estado.eixo_habitantes": "Habitantes",
    "estado.eixo_municipios": "Municípios",
    "estado.eixo_escore": "Escore a partir de",
    "estado.menos_de_01": "menos de 0,1%",
    "estado.resumo_pop": "{hab} habitantes, {pct} da população do estado,",
    "estado.resumo_mun": "{n} dos {total} municípios",
    "estado.dist_legenda": "A maior parte do estado fica à esquerda porque, num mês "
                           "qualquer, poucos municípios estão em risco. A partir de "
                           "{corte} ficam os municípios para os quais o modelo prevê "
                           "surto: {resumo} neste mês.",
    "estado.porte_subtitulo": "**Escore por porte do município**",
    "estado.porte_0": "menos de 10 mil",
    "estado.porte_1": "10 a 50 mil",
    "estado.porte_2": "50 a 200 mil",
    "estado.porte_3": "mais de 200 mil",
    "estado.col_porte": "Porte",
    "estado.col_municipios": "Municípios",
    "estado.col_escore_mediano": "Escore mediano",
    "estado.col_com_surto": "Com surto previsto",
    "estado.porte_legenda": "O modelo é mais fraco nos municípios pequenos, onde poucos "
                            "casos já bastam para caracterizar surto.",
    "estado.comeco_subtitulo": "**Começo de surto contra continuação, neste mês**",
    "estado.col_situacao": "Situação no mês observado",
    "estado.comeco_legenda": "Os municípios já em surto recebem escore mais alto, e é "
                             "por isso que uma métrica agregada parece boa: ela é "
                             "dominada por um caso que a contagem de casos do mês já "
                             "resolveria. O que interessa é a linha de cima.",

    "estado.top_titulo": "Os quinze maiores escores",
    "estado.col_municipio": "Município",
    "estado.col_populacao": "População",
    "estado.col_faixa": "Faixa",
    "estado.col_escore": "Escore",
    "estado.col_situacao_curta": "Situação",
    "estado.top_legenda": "Clique numa linha para abrir o município.",

    "estado.hist_legenda_tamanho": "{n} casos",
    "estado.hist_legenda": "Aperte ▶ para ver mês a mês, ou arraste a barra para ir a "
                           "um mês. Cada bolha é um município com casos naquele mês. O "
                           "tamanho mostra quantos casos houve; a cor mostra a "
                           "incidência, isto é, quantos casos por 100 mil habitantes. "
                           "As duas contam coisas diferentes: uma cidade grande pode "
                           "ter muitos casos e incidência baixa (bolha grande e clara), "
                           "e uma cidade pequena, poucos casos e incidência alta (bolha "
                           "pequena e escura). As duas escalas são as mesmas para todos "
                           "os meses e todas as doenças, e as faixas de 100 e 300 casos "
                           "por 100 mil são as mesmas das definições de surto do "
                           "aplicativo. Os pontos cinza são os municípios sem caso.",
    "estado.hist_mensal": "Casos de {doenca} no estado, mês a mês",
}

EN = {
    "estado.titulo": "State overview",
    "estado.erro_modelo": "Model not fitted for this combination.",
    "estado.legenda_topo": "Forecast for **{alvo}**, with data up to {obs}. {corte}.",
    "estado.m_municipios": "Municipalities",
    "estado.m_previsto": "Outbreak forecast",
    "estado.m_previsto_ajuda": "Municipalities with a score of {corte} or more: {frase}.",
    "estado.m_sem_surto": "Of those, not in outbreak now",
    "estado.m_sem_surto_ajuda": "The ones that still leave time to act.",
    "estado.m_mediano": "Median score",

    "estado.mapa_titulo": "Where the risk is concentrated",
    "estado.sem_coordenadas": "No coordinates available.",
    "estado.dica_escore": "Score",
    "estado.dica_populacao": "Population",
    "estado.mapa_legenda": "Click a circle to open the municipality, with the same "
                           "disease, definition, horizon and model. Colour shows the "
                           "risk level, size shows the population. The map mixes a city "
                           "of half a million with a town of three thousand on purpose: "
                           "risk and size are different questions, and size is there so "
                           "that a small town at the top is read as a small town at the "
                           "top.",

    "estado.dist_titulo": "How the scores are distributed",
    "estado.dist_subtitulo": "**Score distribution**",
    "estado.contar_por": "Count by",
    "estado.contar_municipios": "Number of municipalities",
    "estado.contar_populacao": "Population",
    "estado.eixo_habitantes": "Residents",
    "estado.eixo_municipios": "Municipalities",
    "estado.eixo_escore": "Score from",
    "estado.menos_de_01": "less than 0.1%",
    "estado.resumo_pop": "{hab} residents, {pct} of the state's population,",
    "estado.resumo_mun": "{n} of the {total} municipalities",
    "estado.dist_legenda": "Most of the state sits on the left because, in any given "
                           "month, few municipalities are at risk. From {corte} upwards "
                           "are the municipalities for which the model forecasts an "
                           "outbreak: {resumo} this month.",
    "estado.porte_subtitulo": "**Score by municipality size**",
    "estado.porte_0": "under 10,000",
    "estado.porte_1": "10,000 to 50,000",
    "estado.porte_2": "50,000 to 200,000",
    "estado.porte_3": "over 200,000",
    "estado.col_porte": "Size",
    "estado.col_municipios": "Municipalities",
    "estado.col_escore_mediano": "Median score",
    "estado.col_com_surto": "Outbreak forecast",
    "estado.porte_legenda": "The model is weaker in small municipalities, where a few "
                            "cases are already enough to count as an outbreak.",
    "estado.comeco_subtitulo": "**Outbreak onset versus continuation, this month**",
    "estado.col_situacao": "Status in the observed month",
    "estado.comeco_legenda": "Municipalities already in outbreak get higher scores, and "
                             "that is why an aggregate metric looks good: it is "
                             "dominated by a case the month's case count would already "
                             "settle. What matters is the top row.",

    "estado.top_titulo": "The fifteen highest scores",
    "estado.col_municipio": "Municipality",
    "estado.col_populacao": "Population",
    "estado.col_faixa": "Level",
    "estado.col_escore": "Score",
    "estado.col_situacao_curta": "Status",
    "estado.top_legenda": "Click a row to open the municipality.",

    "estado.hist_legenda_tamanho": "{n} cases",
    "estado.hist_legenda": "Press ▶ to play month by month, or drag the slider to jump "
                           "to a month. Each bubble is a municipality with cases in that "
                           "month. Size shows how many cases there were; colour shows "
                           "incidence, that is, cases per 100,000 residents. They tell "
                           "different things: a large city can have many cases and low "
                           "incidence (a large, light bubble), and a small town few "
                           "cases and high incidence (a small, dark bubble). Both scales "
                           "are the same for every month and every disease, and the "
                           "100 and 300 per 100,000 bands match the app's outbreak "
                           "definitions. Grey dots are municipalities with no cases.",
    "estado.hist_mensal": "{doenca} cases in the state, month by month",
}
