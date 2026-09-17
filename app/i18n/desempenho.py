"""Textos da tela de desempenho medido (`screens/desempenho.py`)."""

PT = {
    "des.titulo": "Desempenho medido",
    "des.legenda_topo": "Todos os números vêm dos anos de teste de 2022, 2023 e 2024. "
                        "Cada ano foi previsto por modelos treinados só com os anos "
                        "anteriores, como aconteceria na prática.",
    "des.sem_colunas": "Os números desta tela saem da Seção 7 do `03_train.ipynb` "
                       "(`limiares_operacao.parquet`). Rode essa seção para gerá-los.",
    "des.sem_padroes": "As combinações padrão não estão no arquivo de cortes.",
    "des.padroes_titulo": "As combinações que o aplicativo abre por padrão",
    "des.previsoes_com": "Previsões feitas com {antecedencia} de antecedência.",

    "des.metrica.precisao": "Precisão",
    "des.metrica.cobertura": "Cobertura",
    "des.metrica.auroc": "AUROC",
    "des.metrica.auprc": "AUPRC",
    "des.sorteio": "sorteio daria {v}",
    "des.n_alertas": "{n} alertas",
    "des.n_surtos": "{n} surtos",
    "des.modelo": "Modelo: {modelo}",
    "des.rodape_cartao": "Surto previsto a partir do escore {corte}. {n} meses com surto "
                         "nos três anos, somando os municípios.",

    "des.significado": "O que cada número quer dizer",
    "des.na_dengue": "Na dengue",
    "des.aqui": "Aqui",
    "des.precisao_pergunta": "quando o modelo avisa, ele acerta?",
    "des.precisao_texto": "Dos municípios com surto previsto, quantos de fato tiveram "
                          "surto. Precisão baixa quer dizer muitos alarmes falsos. "
                          "{onde}, {n} alertas se confirmaram.",
    "des.cobertura_pergunta": "dos surtos que vieram, quantos foram avisados?",
    "des.cobertura_texto": "Dos surtos que aconteceram, quantos o modelo tinha apontado "
                           "com antecedência. Cobertura baixa quer dizer surto chegando "
                           "sem aviso. Também é chamada de sensibilidade ou recall. "
                           "{onde}, o modelo avisou {n} surtos.",
    "des.auroc_pergunta": "o modelo põe quem vai ter surto na frente?",
    "des.auroc_texto": "Sorteie um município que teve surto e um que não teve. A AUROC é "
                       "a chance de o modelo ter dado escore maior ao primeiro. 0,50 é o "
                       "mesmo que tirar no cara ou coroa, e 1 é acertar sempre. Acima de "
                       "0,80 costuma ser considerado bom. {onde}, {v}: em {n} de cada 100 "
                       "pares, o município com surto estava na frente.",
    "des.auprc_pergunta": "e no topo da fila, onde ficam os alertas?",
    "des.auprc_texto": "É a precisão média conforme se desce pela fila, do escore mais "
                       "alto para o mais baixo. Ela depende de quão comum é o surto, por "
                       "isso vem sempre com o valor de um sorteio ao lado, que é a "
                       "própria taxa de surto. Um número que parece baixo pode ser muito "
                       "melhor que o sorteio.",
    "des.opostos": "**Precisão e cobertura puxam em sentidos opostos.** Baixar o escore "
                   "a partir do qual o modelo prevê surto faz ele avisar mais: a "
                   "cobertura sobe e a precisão cai. Subir faz o contrário. O corte de "
                   "cada combinação é o que equilibra os dois, e a aba Sobre explica "
                   "como ele é escolhido.",
    "des.exemplo_auprc": "**Um exemplo de AUPRC.** Na {doenca}, {v} parece pouco. Mas o "
                         "surto é raro, e um sorteio daria {sorteio}: o modelo marca "
                         "cerca de {vezes} vezes mais.",
    "des.zika_poucos": "A zika teve só {n} meses com surto nos três anos de teste, "
                       "somando todos os municípios. Com tão poucos casos, a precisão e "
                       "a cobertura dela mudam bastante com um ou dois surtos a mais ou "
                       "a menos. A AUROC é mais estável.",
    "des.como_medido": "Como estes números foram medidos",
    "des.como_medido_texto": "Cada ano de teste foi previsto por modelos treinados só com "
                             "os anos anteriores a ele. **AUROC e AUPRC** são a média dos "
                             "três anos. **Precisão e cobertura** somam os três anos, e "
                             "em cada ano o corte foi escolhido olhando só os outros "
                             "dois. Assim o modelo não é avaliado com a resposta na mão. "
                             "É uma medida mais exigente do que usar o corte das outras "
                             "telas, que foi escolhido com esses mesmos três anos, e por "
                             "isso os dois números podem ficar um pouco abaixo do que "
                             "esse corte daria.",

    "des.horizonte_titulo": "Quanto o sinal sobrevive à antecedência",
    "des.horizonte_intro": "Quanto mais longe a previsão, menos o modelo sabe. Os "
                           "gráficos mostram os quatro números de cada doença de 1 a 6 "
                           "meses de antecedência, com as mesmas cores de cima. A linha "
                           "tracejada marca a antecedência escolhida no topo da página.",
    "des.eixo_antecedencia": "Antecedência (meses)",
    "des.dica_metrica": "Métrica",
    "des.dica_antecedencia": "Antecedência",
    "des.dica_valor": "Valor",
    "des.horizonte_resumo": "De {de} para {para}: precisão de {p1} para {p2}, cobertura "
                            "de {c1} para {c2} e AUROC de {a1} para {a2}.",
    "des.ordem_resiste": "**A ordem da fila resiste bem.** A AUROC cai devagar nas três "
                         "doenças: mesmo seis meses antes, o modelo ainda põe, na maioria "
                         "das vezes, quem vai ter surto na frente de quem não vai. Seis "
                         "meses ainda é tempo de comprar insumo e escalar equipe.",
    "des.dengue_precisao": "**Na dengue, quem paga a distância é a precisão.** Mais "
                           "longe, o modelo fica menos seguro sobre todos os municípios "
                           "ao mesmo tempo e os escores descem. O corte é escolhido de "
                           "novo para cada antecedência e desce junto, de {c1} em {h1} "
                           "para {c2} em {h2}. Isso segura a cobertura ({r1} para {r2}), "
                           "mas o modelo passa a avisar mais municípios que não terão "
                           "surto, e a precisão cai de {p1} para {p2}.",
}

EN = {
    "des.titulo": "Measured performance",
    "des.legenda_topo": "Every number comes from the 2022, 2023 and 2024 test years. Each "
                        "year was forecast by models trained only on the years before "
                        "it, as would happen in practice.",
    "des.sem_colunas": "The numbers on this page come from Section 7 of "
                       "`03_train.ipynb` (`limiares_operacao.parquet`). Run that section "
                       "to generate them.",
    "des.sem_padroes": "The default combinations are not in the thresholds file.",
    "des.padroes_titulo": "The combinations the app opens with",
    "des.previsoes_com": "Forecasts made {antecedencia} ahead.",

    "des.metrica.precisao": "Precision",
    "des.metrica.cobertura": "Recall",
    "des.metrica.auroc": "AUROC",
    "des.metrica.auprc": "AUPRC",
    "des.sorteio": "chance would give {v}",
    "des.n_alertas": "{n} alerts",
    "des.n_surtos": "{n} outbreaks",
    "des.modelo": "Model: {modelo}",
    "des.rodape_cartao": "Outbreak forecast from a score of {corte}. {n} outbreak months "
                         "over the three years, across all municipalities.",

    "des.significado": "What each number means",
    "des.na_dengue": "For dengue",
    "des.aqui": "Here",
    "des.precisao_pergunta": "when the model raises an alert, is it right?",
    "des.precisao_texto": "Of the municipalities with an outbreak forecast, how many "
                          "actually had one. Low precision means many false alarms. "
                          "{onde}, {n} alerts were confirmed.",
    "des.cobertura_pergunta": "of the outbreaks that came, how many were flagged?",
    "des.cobertura_texto": "Of the outbreaks that happened, how many the model had "
                           "flagged in advance. Low recall means outbreaks arriving "
                           "without warning. Also called sensitivity. {onde}, the model "
                           "flagged {n} outbreaks.",
    "des.auroc_pergunta": "does the model put the future outbreaks first?",
    "des.auroc_texto": "Pick at random one municipality that had an outbreak and one "
                       "that did not. The AUROC is the chance that the model gave the "
                       "first one a higher score. 0.50 is a coin toss, and 1 is always "
                       "right. Above 0.80 is usually considered good. {onde}, {v}: in "
                       "{n} out of every 100 pairs, the municipality with the outbreak "
                       "came first.",
    "des.auprc_pergunta": "and at the top of the queue, where the alerts are?",
    "des.auprc_texto": "It is the average precision as you move down the queue, from the "
                       "highest score to the lowest. It depends on how common outbreaks "
                       "are, so it always comes with the value chance would give next "
                       "to it, which is the outbreak rate itself. A number that looks "
                       "low can be much better than chance.",
    "des.opostos": "**Precision and recall pull in opposite directions.** Lowering the "
                   "score at which the model forecasts an outbreak makes it alert more: "
                   "recall goes up and precision goes down. Raising it does the "
                   "opposite. Each combination's cut is what balances the two, and the "
                   "About page explains how it is chosen.",
    "des.exemplo_auprc": "**An AUPRC example.** For {doenca}, {v} looks low. But "
                         "outbreaks are rare, and chance would give {sorteio}: the model "
                         "scores about {vezes} times more.",
    "des.zika_poucos": "Zika had only {n} outbreak months over the three test years, "
                       "across all municipalities. With so few cases, its precision and "
                       "recall change a lot with one or two outbreaks more or less. The "
                       "AUROC is more stable.",
    "des.como_medido": "How these numbers were measured",
    "des.como_medido_texto": "Each test year was forecast by models trained only on the "
                             "years before it. **AUROC and AUPRC** are the average of "
                             "the three years. **Precision and recall** add up the three "
                             "years, and in each year the cut was chosen looking only at "
                             "the other two. That way the model is not evaluated with "
                             "the answer in hand. It is a stricter measure than using "
                             "the cut from the other pages, which was chosen with those "
                             "same three years, so these two numbers may come out a "
                             "little below what that cut would give.",

    "des.horizonte_titulo": "How much signal survives the lead time",
    "des.horizonte_intro": "The further ahead the forecast, the less the model knows. "
                           "The charts show each disease's four numbers from 1 to 6 "
                           "months of lead time, in the same colours as above. The "
                           "dashed line marks the lead time chosen at the top of the "
                           "page.",
    "des.eixo_antecedencia": "Lead time (months)",
    "des.dica_metrica": "Metric",
    "des.dica_antecedencia": "Lead time",
    "des.dica_valor": "Value",
    "des.horizonte_resumo": "From {de} to {para}: precision from {p1} to {p2}, recall "
                            "from {c1} to {c2} and AUROC from {a1} to {a2}.",
    "des.ordem_resiste": "**The ranking holds up well.** The AUROC falls slowly for all "
                         "three diseases: even six months ahead, the model still puts, "
                         "most of the time, the municipalities that will have an "
                         "outbreak ahead of those that will not. Six months is still "
                         "time to buy supplies and scale up staff.",
    "des.dengue_precisao": "**For dengue, precision pays for the distance.** Further "
                           "ahead, the model is less sure about every municipality at "
                           "once and the scores drop. The cut is chosen again for each "
                           "lead time and drops with them, from {c1} at {h1} to {c2} at "
                           "{h2}. That holds recall steady ({r1} to {r2}), but the model "
                           "starts alerting on more municipalities that will not have an "
                           "outbreak, and precision falls from {p1} to {p2}.",
}
