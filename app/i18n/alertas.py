"""Textos da tela de alertas do mês (`screens/alertas.py`)."""

PT = {
    "alertas.titulo": "Alertas do mês",
    "alertas.erro_modelo": "O modelo {modelo} não foi ajustado para esta combinação.",
    "alertas.legenda_topo": "Previsão para **{alvo}**, feita com dados até {obs}. {corte}.",
    "alertas.m_avaliados": "Municípios avaliados",
    "alertas.m_previsto": "Com surto previsto",
    "alertas.m_previsto_ajuda": "Municípios nas faixas Alto ou Crítico, isto é, com "
                                "escore igual ou acima de {corte}: {frase}.",
    "alertas.m_sem_surto": "Desses, sem surto no momento",
    "alertas.m_sem_surto_ajuda": "São os que ainda deixam tempo de agir, e os mais "
                                 "difíceis de acertar.",
    "alertas.m_ja_em_surto": "Já em surto no mês observado",
    "alertas.legenda_cartoes": "Alto e Crítico são os municípios com surto previsto. "
                               "Os intervalos de escore mudam com a doença, a "
                               "definição, a antecedência e o modelo; a aba Sobre "
                               "explica de onde vêm. Abra um município para ver o "
                               "que costuma fazer sentido na faixa dele.",
    "alertas.filtro_sem_surto": "Só municípios que não estão em surto no momento",
    "alertas.filtro_sem_surto_ajuda": "Esconde quem já está em surto. Os alertas que "
                                      "sobram são os que ainda deixam tempo de agir.",
    "alertas.faixa_minima": "Mostrar a partir da faixa",
    "alertas.faixa_minima_ajuda": "Alto e Crítico são os municípios com surto previsto. "
                                  "Moderado mostra também os que estão se aproximando "
                                  "do corte.",
    "alertas.quantos": "Quantos mostrar",
    "alertas.vazio": "Nenhum município na faixa {faixa} ou acima. Em meses de baixa "
                     "transmissão isso é esperado; escolha uma faixa mais baixa para "
                     "ver quem está mais perto do corte.",
    "alertas.col_municipio": "Município",
    "alertas.col_codigo": "Código IBGE",
    "alertas.col_populacao": "População",
    "alertas.col_situacao": "Situação no mês observado",
    "alertas.col_faixa": "Faixa",
    "alertas.col_escore": "Escore",
    "alertas.listados": "{n} municípios listados. Clique numa linha para ver por que o "
                        "município foi apontado.",
    "alertas.como_ler": "Como ler estes números",
    "alertas.como_ler_texto": """
O escore vai de 0 a 1 e ordena os municípios pela atenção que merecem neste
mês. **Ele não é a probabilidade de que um surto vá acontecer.** Um escore de
0,60 não quer dizer 60% de chance: quer dizer que o município está à frente de
quase todos os outros na fila.

O escore a partir do qual o modelo prevê surto muda de uma combinação para
outra. Nesta, é **{corte}**. Cada modelo espalha os escores de um jeito, e
nos modelos de árvores os escores caem conforme a previsão se afasta; por isso
o corte é calculado para cada combinação, e as faixas acompanham o corte. A aba
Sobre explica o cálculo.

A coluna de situação vem do rótulo observado em {obs}, e é a distinção que o
trabalho mede. Prever que um surto continua é fácil, porque a contagem de casos
do mês já diz quase tudo. Prever que um surto começa é o que muda o que uma
secretaria consegue fazer, e é onde o modelo acerta bem menos.

A antecedência conta a partir do último mês com dados consolidados, não a
partir de hoje. Como a série termina em {obs}, o tempo real de preparo é menor
que {antecedencia}.
""",
}

EN = {
    "alertas.titulo": "This month's alerts",
    "alertas.erro_modelo": "The {modelo} model was not fitted for this combination.",
    "alertas.legenda_topo": "Forecast for **{alvo}**, made with data up to {obs}. {corte}.",
    "alertas.m_avaliados": "Municipalities assessed",
    "alertas.m_previsto": "Outbreak forecast",
    "alertas.m_previsto_ajuda": "Municipalities in the High or Critical levels, that "
                                "is, with a score of {corte} or more: {frase}.",
    "alertas.m_sem_surto": "Of those, not in outbreak now",
    "alertas.m_sem_surto_ajuda": "These are the ones that still leave time to act, "
                                 "and the hardest to get right.",
    "alertas.m_ja_em_surto": "Already in outbreak",
    "alertas.legenda_cartoes": "High and Critical are the municipalities with an "
                               "outbreak forecast. The score ranges change with the "
                               "disease, the definition, the lead time and the model; "
                               "the About page explains where they come from. Open a "
                               "municipality to see what usually makes sense at its "
                               "level.",
    "alertas.filtro_sem_surto": "Only municipalities not in outbreak right now",
    "alertas.filtro_sem_surto_ajuda": "Hides those already in outbreak. The alerts "
                                      "left are the ones that still leave time to act.",
    "alertas.faixa_minima": "Show from level",
    "alertas.faixa_minima_ajuda": "High and Critical are the municipalities with an "
                                  "outbreak forecast. Moderate also shows those getting "
                                  "close to the cut.",
    "alertas.quantos": "How many to show",
    "alertas.vazio": "No municipality at the {faixa} level or above. In low "
                     "transmission months this is expected; pick a lower level to see "
                     "who is closest to the cut.",
    "alertas.col_municipio": "Municipality",
    "alertas.col_codigo": "IBGE code",
    "alertas.col_populacao": "Population",
    "alertas.col_situacao": "Status in the observed month",
    "alertas.col_faixa": "Level",
    "alertas.col_escore": "Score",
    "alertas.listados": "{n} municipalities listed. Click a row to see why the "
                        "municipality was flagged.",
    "alertas.como_ler": "How to read these numbers",
    "alertas.como_ler_texto": """
The score goes from 0 to 1 and ranks municipalities by the attention they deserve
this month. **It is not the probability that an outbreak will happen.** A score of
0.60 does not mean a 60% chance: it means the municipality is ahead of almost all
the others in the queue.

The score at which the model forecasts an outbreak changes from one combination to
another. In this one, it is **{corte}**. Each model spreads its scores differently,
and in the tree models the scores shrink as the forecast reaches further ahead;
that is why the cut is computed for each combination, and the levels follow the
cut. The About page explains the calculation.

The status column comes from the label observed in {obs}, and it is the
distinction this work measures. Forecasting that an outbreak continues is easy,
because the month's case count already says almost everything. Forecasting that
an outbreak starts is what changes what a health department can do, and it is
where the model does much worse.

The lead time counts from the last month with consolidated data, not from today.
Since the series ends in {obs}, the real preparation time is shorter than
{antecedencia}.
""",
}
