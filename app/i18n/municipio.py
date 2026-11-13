"""Textos da tela do município (`screens/municipio.py`)."""

PT = {
    "mun.titulo": "Município",
    "mun.populacao": "População",
    "mun.aberto_de": "Aberto a partir {origem}, na mesma configuração.",
    "mun.origem.alertas": "da tela de alertas",
    "mun.origem.mapa": "do mapa do estado",
    "mun.origem.top15": "da lista dos maiores escores do estado",
    "mun.origem.vizinhos": "da lista de vizinhos de {nome}",
    "mun.origem.outra": "de outra tela",
    "mun.sem_previsao": "Sem previsão para este município nesta combinação.",

    "mun.m_escore": "Escore",
    "mun.m_faixa": "Faixa",
    "mun.m_faixa_ajuda": "Nesta combinação: Crítico a partir de {critico}, Alto a partir "
                         "de {alto}, Moderado a partir de {moderado}.",
    "mun.m_previsto": "Surto previsto?",
    "mun.m_previsto_ajuda": "{frase}. O corte muda com o modelo e com o horizonte; a "
                            "aba Sobre explica por quê.",
    "mun.m_mes": "Mês previsto",
    "mun.m_mes_ajuda": "Calculado com dados até {obs}.",
    "mun.ja_em_surto": "Em {mes}, último mês com dados, este município "
                       "**já estava em surto**.",
    "mun.nao_em_surto": "Em {mes}, último mês com dados, este município "
                        "**não estava em surto**.",

    "mun.acao_faixa": "Faixa {faixa}",
    "mun.acao_titulo": "O que costuma fazer sentido neste nível",
    "mun.acao_precisao": "Dimensione pela precisão real: nos anos de teste, {n} alertas "
                         "desta combinação se confirmaram. A resposta proporcional é "
                         "preparar, não gastar todo o orçamento num alerta.",

    "mun.shap_titulo": "O que pesou nesta previsão",
    "mun.shap_sem_linha": "Sem linha de features para este município e mês.",
    "mun.shap_calculando": "Calculando as contribuições...",
    "mun.shap_falhou": "Não foi possível explicar esta previsão.",
    "mun.shap_valor": "valor: {v}",
    "mun.shap_desce": "&larr; puxa o risco para baixo",
    "mun.shap_sobe": "empurra para cima &rarr;",
    "mun.shap_resumo": "As dez variáveis que mais mexeram no escore deste município: "
                       "<span style='color:{cor_sobe};font-weight:700'>{n_sobe} "
                       "empurraram o risco para cima</span> e <span style='color:"
                       "{cor_desce};font-weight:700'>{n_desce} puxaram para baixo</span>.",
    "mun.shap_legenda": "O peso é o valor SHAP: quanto aquela variável moveu esta "
                        "previsão a partir da média do modelo. Ele está na escala "
                        "interna do modelo, então serve para comparar as variáveis "
                        "entre si, não para somar ao escore. São as dez maiores em "
                        "módulo, entre as 125 que o modelo usa.",

    "mun.hist_sem_serie": "Sem série de casos para esta doença neste município.",
    "mun.hist_mensal": "Casos de {doenca} em {nome}, mês a mês",

    "mun.comp_titulo": "{nome} ao lado de municípios parecidos",
    "mun.porte_titulo": "Entre os municípios de porte parecido",
    "mun.porte_capital": "A capital não tem municípios de porte parecido no estado: o "
                         "segundo maior não chega a um oitavo da população dela. Veja "
                         "os vizinhos abaixo.",
    "mun.porte_sem_indicadores": "Sem indicadores suficientes para comparar este município.",
    "mun.porte_habitantes": "tem {n} habitantes e ",
    "mun.porte_intro": "{nome} {hab}está no grupo de **{porte}**, com mais {n} "
                       "municípios. Cada régua mostra onde ele fica entre esses pares: o "
                       "traço do meio é a mediana, <span style='color:{cor_melhor};"
                       "font-weight:700'>azul</span> é melhor que a maioria e <span "
                       "style='color:{cor_pior};font-weight:700'>vermelho</span>, pior.",
    "mun.porte_linha": "{nome}: <b>{valor}</b> · mediana do grupo: {mediana} · {fonte}",
    "mun.porte_maior": "maior que {p}% dos pares",
    "mun.porte_menor": "menor que {p}% dos pares",
    "mun.porte_melhor": "melhor que {p}% dos pares",
    "mun.porte_pior": "pior que {p}% dos pares",
    "mun.regua_menor": "&larr; menor",
    "mun.regua_maior": "maior &rarr;",
    "mun.regua_pior": "&larr; pior",
    "mun.regua_melhor": "melhor &rarr;",
    "mun.regua_mediana": "mediana",
    "mun.porte_legenda": "É posição, não causa. Estar abaixo dos pares num indicador não "
                         "quer dizer que ele provoca surto; mostra só onde o município "
                         "está. O contexto não tem melhor nem pior, e serve para situar "
                         "o município.",

    "mun.viz_titulo": "Os vizinhos",
    "mun.viz_sem_coordenadas": "Sem coordenadas para este município.",
    "mun.viz_periodo_ano": "{inicio} a {fim} de {ano}",
    "mun.viz_periodo_dois_anos": "{inicio} de {ano_inicio} a {fim} de {ano}",
    "mun.viz_intro": "Os {n} municípios mais próximos de {nome}. O mosquito não respeita "
                     "divisa: o que acontece ao lado importa mesmo quando o vizinho tem "
                     "outro tamanho. Faixa e escore são da mesma doença, definição, "
                     "horizonte e modelo escolhidos no topo.",
    "mun.viz_este": "{nome} (este município)",
    "mun.viz_col_municipio": "Município",
    "mun.viz_col_distancia": "Distância",
    "mun.viz_col_populacao": "População",
    "mun.viz_col_faixa": "Faixa",
    "mun.viz_col_escore": "Escore",
    "mun.viz_col_casos": "Casos por 100 mil hab. ({periodo})",
    "mun.viz_legenda": "Clique num vizinho para abrir a tela dele na mesma configuração. "
                       "A distância é em linha reta, entre os pontos de referência de "
                       "cada município.",
}

EN = {
    "mun.titulo": "Municipality",
    "mun.populacao": "Population",
    "mun.aberto_de": "Opened from {origem}, with the same settings.",
    "mun.origem.alertas": "the alerts page",
    "mun.origem.mapa": "the state map",
    "mun.origem.top15": "the state's highest scores list",
    "mun.origem.vizinhos": "the list of neighbours of {nome}",
    "mun.origem.outra": "another page",
    "mun.sem_previsao": "No forecast for this municipality in this combination.",

    "mun.m_escore": "Score",
    "mun.m_faixa": "Level",
    "mun.m_faixa_ajuda": "In this combination: Critical from {critico}, High from {alto}, "
                         "Moderate from {moderado}.",
    "mun.m_previsto": "Outbreak forecast?",
    "mun.m_previsto_ajuda": "{frase}. The cut changes with the model and the horizon; "
                            "the About page explains why.",
    "mun.m_mes": "Forecast month",
    "mun.m_mes_ajuda": "Computed with data up to {obs}.",
    "mun.ja_em_surto": "In {mes}, the last month with data, this municipality **was "
                       "already in outbreak**.",
    "mun.nao_em_surto": "In {mes}, the last month with data, this municipality **was not "
                        "in outbreak**.",

    "mun.acao_faixa": "{faixa} level",
    "mun.acao_titulo": "What usually makes sense at this level",
    "mun.acao_precisao": "Size the response by the measured precision: across the test "
                         "years, {n} alerts from this combination turned out to be "
                         "outbreaks. The proportionate response is to prepare, not to "
                         "spend the whole budget on one alert.",

    "mun.shap_titulo": "What drove this forecast",
    "mun.shap_sem_linha": "No feature row for this municipality and month.",
    "mun.shap_calculando": "Computing the contributions...",
    "mun.shap_falhou": "Could not explain this forecast.",
    "mun.shap_valor": "value: {v}",
    "mun.shap_desce": "&larr; pulls the risk down",
    "mun.shap_sobe": "pushes it up &rarr;",
    "mun.shap_resumo": "The ten variables that moved this municipality's score the most: "
                       "<span style='color:{cor_sobe};font-weight:700'>{n_sobe} pushed "
                       "the risk up</span> and <span style='color:{cor_desce};"
                       "font-weight:700'>{n_desce} pulled it down</span>.",
    "mun.shap_legenda": "The weight is the SHAP value: how much that variable moved this "
                        "forecast away from the model's average. It is on the model's "
                        "internal scale, so it is for comparing variables with each "
                        "other, not for adding up to the score. These are the ten "
                        "largest in absolute value, out of the 125 the model uses.",

    "mun.hist_sem_serie": "No case series for this disease in this municipality.",
    "mun.hist_mensal": "{doenca} cases in {nome}, month by month",

    "mun.comp_titulo": "{nome} next to similar municipalities",
    "mun.porte_titulo": "Among municipalities of similar size",
    "mun.porte_capital": "The state capital has no municipality of similar size in the "
                         "state: the second largest has less than an eighth of its "
                         "population. See the neighbours below.",
    "mun.porte_sem_indicadores": "Not enough indicators to compare this municipality.",
    "mun.porte_habitantes": "has {n} residents and ",
    "mun.porte_intro": "{nome} {hab}is in the **{porte}** group, with {n} other "
                       "municipalities. Each bar shows where it stands among these "
                       "peers: the middle mark is the median, <span style='color:"
                       "{cor_melhor};font-weight:700'>blue</span> is better than most "
                       "and <span style='color:{cor_pior};font-weight:700'>red</span>, "
                       "worse.",
    "mun.porte_linha": "{nome}: <b>{valor}</b> · group median: {mediana} · {fonte}",
    "mun.porte_maior": "higher than {p}% of peers",
    "mun.porte_menor": "lower than {p}% of peers",
    "mun.porte_melhor": "better than {p}% of peers",
    "mun.porte_pior": "worse than {p}% of peers",
    "mun.regua_menor": "&larr; lower",
    "mun.regua_maior": "higher &rarr;",
    "mun.regua_pior": "&larr; worse",
    "mun.regua_melhor": "better &rarr;",
    "mun.regua_mediana": "median",
    "mun.porte_legenda": "This is position, not cause. Being below peers on an indicator "
                         "does not mean it causes outbreaks; it only shows where the "
                         "municipality stands. Context indicators have no better or "
                         "worse, and are there to situate the municipality.",

    "mun.viz_titulo": "The neighbours",
    "mun.viz_sem_coordenadas": "No coordinates for this municipality.",
    "mun.viz_periodo_ano": "{inicio} to {fim} {ano}",
    "mun.viz_periodo_dois_anos": "{inicio} {ano_inicio} to {fim} {ano}",
    "mun.viz_intro": "The {n} municipalities closest to {nome}. Mosquitoes do not respect "
                     "borders: what happens next door matters even when the neighbour is "
                     "a different size. Level and score use the same disease, "
                     "definition, horizon and model chosen at the top.",
    "mun.viz_este": "{nome} (this one)",
    "mun.viz_col_municipio": "Municipality",
    "mun.viz_col_distancia": "Distance",
    "mun.viz_col_populacao": "Population",
    "mun.viz_col_faixa": "Level",
    "mun.viz_col_escore": "Score",
    "mun.viz_col_casos": "Cases per 100,000 res. ({periodo})",
    "mun.viz_legenda": "Click a neighbour to open its page with the same settings. "
                       "Distance is a straight line between each municipality's "
                       "reference point.",
}
