"""Textos da tela Sobre (`screens/sobre.py`)."""

PT = {
    "sobre.titulo": "Sobre",
    "sobre.texto": """
### O que esta plataforma faz

Ordena os 645 municípios do estado de São Paulo, a cada mês, pelo risco de
surto de dengue, zika e chikungunya, de um a seis meses à frente. Para cada
alerta, mostra as variáveis que empurraram o risco para cima e para baixo.

Os modelos aprendem de dezesseis fontes públicas brasileiras: notificações
(SINAN), internações (SIH-SUS), rede de saúde (CNES/SIM), nascidos vivos
(SINASC), clima (NASA POWER), população e PIB (IBGE), área territorial,
deslocamento pendular, habitação, cobertura do solo (MapBiomas), saneamento
(SINISA), atenção primária (e-Gestor), capacidade municipal (MUNIC),
indicadores fiscais e de desenvolvimento, e cobertura vacinal de febre amarela.

### O que ela não faz

**O escore não é a probabilidade de um surto acontecer.** É uma posição na
fila de atenção. Uma probabilidade convida a uma aposta; um escore convida a
uma comparação, que é o uso correto.

**O horizonte é nominal.** Ele conta a partir do último mês com dados
consolidados, e não a partir de hoje. Uma notificação leva tempo para ser
classificada como confirmada ou descartada, então a série termina no último mês
que teve sessenta dias para consolidar. O tempo real de preparo é menor que o
horizonte escolhido.

**Não há uma única definição de surto.** A plataforma oferece quatro, e elas
discordam entre si. Duas são absolutas, comparáveis entre municípios; duas são
relativas à história de cada município. A concordância entre as duas famílias,
medida por kappa de Cohen, fica entre 0,49 e 0,60. Escolher uma definição é
uma decisão, não um detalhe técnico, e por isso ela está na tela e não
escondida no código.

### Por que algumas combinações não aparecem

Os modelos foram treinados para quatro doenças, quatro definições de surto e
seis horizontes. A plataforma só mostra o que passou em dois critérios.

**1. Foi possível verificar se o modelo acerta.** Para isso, precisa ter havido
surto em pelo menos um dos anos usados para teste (2022, 2023 e 2024). Por esse
critério ficaram de fora a **febre amarela**, em todas as definições, e a
**zika** com as definições de mais de 100 e de mais de 300 casos por 100 mil
habitantes: nesses casos não houve nenhum surto nos anos de teste, e não há
como saber se um escore alto significa alguma coisa.

**2. O modelo ajuda de fato.** Nos anos de teste, o modelo precisa ter
separado bem os municípios que tiveram surto dos que não tiveram: AUROC de pelo
menos 0,70, que é o limite usual para considerar essa separação aceitável.
Abaixo disso, a ordem dos municípios fica pouco melhor que um sorteio, e os
alertas custariam à secretaria mais em alarmes falsos do que ajudariam.

Por esse critério saem:

- a **dengue** com o canal endêmico e com a definição por desvios da média, de
  4 a 6 meses à frente (nessas combinações, o melhor modelo ficou entre
  0,64 e 0,68);
- a **chikungunya** com as definições de mais de 100 casos por 100 mil
  habitantes (de 3 a 6 meses) e de mais de 300 (5 e 6 meses);
- em algumas combinações que continuam, **modelos específicos**, na maioria a
  regressão logística. Eles simplesmente não aparecem no seletor.

O critério vale para cada modelo em cada combinação. O modelo padrão de cada
doença passa em todos os horizontes.

A febre amarela continua entrando nos modelos das outras doenças, pela
cobertura vacinal e pelo histórico de casos, mas não tem alerta próprio.

### Modelo e definição de cada doença

Cada doença abre com o modelo e a definição que tiveram melhor resultado nos
anos de teste, com atenção especial aos horizontes de 4 a 6 meses:

- **Dengue:** XGBoost, com surto definido como mais de 100 casos por 100 mil
  habitantes. O XGBoost foi o melhor em todos os horizontes.
- **Zika:** Random Forest, com o canal endêmico. Com horizonte de 6 meses,
  o Random Forest separou melhor os municípios que tiveram surto (AUROC 0,957,
  contra 0,868 do XGBoost).
- **Chikungunya:** Random Forest, com o canal endêmico.

Na zika e na chikungunya, o canal endêmico é a escolha natural porque são
doenças mais raras: as definições por número de casos por habitante quase
nunca indicam surto. Você pode trocar o modelo e a definição a qualquer momento
nos seletores de cada tela.

### Como o escore e as faixas são calculados

**De onde vem o escore.** Para cada município, o modelo olha 125 informações
do mês mais recente (casos recentes das quatro doenças, clima, época do ano,
saneamento, cobertura de saúde, população, entre outras) e devolve um número
entre 0 e 1. Quanto maior o número, mais o município se parece com os que, no
passado, tiveram surto com aquele horizonte. O modelo que gera a previsão
atual aprendeu com todos os meses de 2015 até o último mês consolidado.

**Como cada modelo chega ao número.**

- **Regressão logística.** Dá um peso a cada informação, soma tudo e passa a
  soma por uma curva que a transforma num valor entre 0 e 1. É o modelo mais
  simples, e o único em que cada informação empurra o risco sempre na mesma
  direção.
- **Random Forest.** Reúne 200 árvores de decisão, cada uma treinada com uma
  parte diferente dos dados. Cada árvore faz uma sequência de perguntas, como
  "o município teve mais de tantos casos no mês passado?" ou "a temperatura
  passou de tal valor?", até chegar a uma resposta. O escore é a média das
  respostas das 200 árvores.
- **XGBoost e LightGBM.** Também usam árvores, 300 em cada um, mas construídas
  uma depois da outra: cada árvore nova tenta corrigir os erros que as
  anteriores ainda cometiam. O escore é a soma das contribuições de todas as
  árvores, convertida para um valor entre 0 e 1.

**Por que cada modelo tem o seu próprio corte.** Os quatro modelos colocam os
municípios numa ordem parecida, mas espalham os escores de formas muito
diferentes. O escore a partir do qual cada um prevê surto fica, em geral, perto
de 0,10 no LightGBM, 0,20 no XGBoost, 0,43 no Random Forest e 0,80 na regressão
logística. Um escore de 0,30 é alto para o XGBoost e baixo para a regressão
logística. Por isso o escore só tem significado quando comparado com o corte do
próprio modelo.

O corte também muda com o horizonte. Nos três modelos de árvores, quanto
mais distante a previsão, menos seguro o modelo fica e mais baixos ficam os
escores de todos os municípios: o corte típico do Random Forest cai de 0,60 com
um mês para 0,30 com seis meses. Com um corte fixo em 0,50, o Random Forest
avisaria sobre 28% dos surtos seis meses à frente; com o corte
próprio, avisa sobre 57% (valores medianos entre as combinações). Na regressão
logística é o contrário: o corte fica acima de 0,50, e um 0,50 fixo daria
alarmes falsos demais. O corte não serve para avisar mais ou menos, e sim para
equilibrar as duas coisas em cada caso.

**Como o corte é escolhido.** Usamos os anos de 2022, 2023 e 2024, cada um
previsto por uma versão do modelo que não o viu durante o treino. Em cada ano,
testamos cortes de 0,05 a 0,95 e ficamos com o que melhor equilibra duas
coisas: avisar sobre o maior número possível de surtos que de fato
aconteceram, e dar o menor número possível de alarmes falsos. O corte final é o
valor do meio entre os três anos, para que um ano fora do comum, como a grande
epidemia de 2024, não decida sozinho. Isso é feito separadamente para cada
combinação de doença, definição de surto, horizonte e modelo, num total de
240 cortes.

Uma ressalva: o corte é medido com essas versões de teste, e o modelo que gera
a previsão atual foi treinado com todos os anos. Supomos que ele distribui os
escores da mesma forma.

**Como as faixas saem do corte.**

- **Alto** começa no corte. É a partir daqui que o modelo prevê surto.
- **Crítico** começa no meio do caminho entre o corte e 1.
- **Moderado** começa na metade do corte. O modelo ainda não prevê surto, mas o
  município está se aproximando.
- **Baixo** é tudo o que fica abaixo disso.

Por exemplo, com corte 0,40: Crítico a partir de 0,70, Alto a partir de 0,40,
Moderado a partir de 0,20.

**Por que o escore não é uma probabilidade.** A proporção de municípios em
surto muda muito de um ano para outro. Com a definição de mais de 100 casos por
100 mil habitantes, ela foi de 20,3% em 2022, 16,7% em 2023 e 39,0% em 2024.
Um ajuste que convertesse o escore em "chance de surto", aprendido num ano
comum, erraria num ano de epidemia, e não há como saber com antecedência como
será o ano seguinte. Na versão anterior deste projeto, esse ajuste foi testado
e piorou os resultados. O que se mantém de um ano para outro é a ordem dos
municípios, e é essa ordem que o escore expressa.

### Reprodutibilidade

Todo o pipeline são quatro notebooks que rodam de cima para baixo: coleta,
montagem da tabela e dos rótulos, features e treino, resultados. O notebook de
resultados reexecuta o código de features do notebook de treino em vez de
repeti-lo, e se recusa a produzir qualquer figura se o modelo reajustado não
reproduzir as métricas gravadas em disco com quatro casas decimais.
""",
    "sobre.cortes_titulo": "Os cortes de cada combinação",
    "sobre.cortes_intro": "Escore a partir do qual cada modelo prevê surto, para cada "
                          "horizonte. As faixas saem desses números pela regra acima.",
    "sobre.cortes_legenda": "— indica modelo que não passou no critério de qualidade e "
                            "não aparece no aplicativo nessa combinação.",
    "sobre.autoria_titulo": "Autoria",
    "sobre.autoria_intro": "Projeto de Iniciação Científica desenvolvido no Instituto de "
                           "Ciências Matemáticas e de Computação da USP (ICMC-USP), em São "
                           "Carlos, com bolsa do Programa Unificado de Bolsas (PUB) da USP, "
                           "por um aluno de graduação.",
    "sobre.autoria_aluno": "Aluno",
    "sobre.autoria_orientador": "Orientador",
    "sobre.autoria_colaboracao": "Colaboração",
}

EN = {
    "sobre.titulo": "About",
    "sobre.texto": """
### What this platform does

Every month, it ranks the 645 municipalities of the state of São Paulo by the
risk of a dengue, Zika or chikungunya outbreak, one to six months ahead. For each
alert, it shows the variables that pushed the risk up and down.

The models learn from sixteen Brazilian public data sources: case notifications
(SINAN), hospitalisations (SIH-SUS), health network (CNES/SIM), live births
(SINASC), weather (NASA POWER), population and GDP (IBGE), land area, commuting,
housing, land cover (MapBiomas), sanitation (SINISA), primary care (e-Gestor),
municipal capacity (MUNIC), fiscal and development indicators, and yellow fever
vaccination coverage.

### What it does not do

**The score is not the probability that an outbreak will happen.** It is a place
in the attention queue. A probability invites a bet; a score invites a
comparison, which is the right use.

**The horizon is nominal.** It counts from the last month with consolidated
data, not from today. A notification takes time to be classified as confirmed or
discarded, so the series ends at the last month that has had sixty days to
consolidate. The real preparation time is shorter than the chosen horizon.

**There is no single outbreak definition.** The platform offers four, and they
disagree with each other. Two are absolute, comparable across municipalities; two
are relative to each municipality's own history. Agreement between the two
families, measured by Cohen's kappa, is between 0.49 and 0.60. Choosing a
definition is a decision, not a technical detail, which is why it is on the
screen and not hidden in the code.

### Why some combinations do not appear

The models were trained for four diseases, four outbreak definitions and six
horizons. The platform only shows what passed two criteria.

**1. It was possible to check whether the model is right.** That requires at
least one outbreak in the test years (2022, 2023 and 2024). This criterion leaves
out **yellow fever**, under every definition, and **Zika** under the more than
100 and more than 300 cases per 100,000 residents definitions: there was no
outbreak in the test years, so there is no way to know whether a high score
means anything.

**2. The model actually helps.** In the test years, the model must have
separated well the municipalities that had an outbreak from those that did not:
an AUROC of at least 0.70, the usual threshold for acceptable discrimination.
Below that, the ranking is barely better than chance, and the alerts would cost a
health department more in false alarms than they would help.

This criterion removes:

- **dengue** under the historical range and standard score definitions, at 4 to
  6 months ahead (in these combinations, the best model scored between
  0.64 and 0.68);
- **chikungunya** under the more than 100 cases per 100,000 residents definition
  (3 to 6 months) and the more than 300 definition (5 and 6 months);
- in some combinations that remain, **specific models**, mostly logistic
  regression. They simply do not appear in the selector.

The criterion applies to each model in each combination. Each disease's default
model passes at every horizon.

Yellow fever still feeds into the models of the other diseases, through
vaccination coverage and case history, but it has no alert of its own.

### Model and definition for each disease

Each disease opens with the model and definition that did best in the test
years, with special attention to horizons of 4 to 6 months:

- **Dengue:** XGBoost, with an outbreak defined as more than 100 cases per
  100,000 residents. XGBoost was the best at every horizon.
- **Zika:** Random Forest, with the endemic channel. Six months ahead,
  Random Forest best separated the municipalities that had an outbreak (AUROC
  0.957, against 0.868 for XGBoost).
- **Chikungunya:** Random Forest, with the endemic channel.

For Zika and chikungunya, the endemic channel is the natural choice because they
are rarer diseases: the definitions based on cases per resident almost never
flag an outbreak. You can change the model and the definition at any time in the
selectors on each page.

### How the score and the levels are computed

**Where the score comes from.** For each municipality, the model looks at 125
pieces of information from the latest month (recent cases of the four diseases,
weather, time of year, sanitation, health coverage, population, among others)
and returns a number between 0 and 1. The higher the number, the more the
municipality resembles those that, in the past, had an outbreak at that
horizon. The model behind the current forecast learned from every month from 2015
to the last consolidated month.

**How each model arrives at the number.**

- **Logistic regression.** Gives each piece of information a weight, adds
  everything up and passes the sum through a curve that turns it into a value
  between 0 and 1. It is the simplest model, and the only one in which each piece
  of information always pushes the risk in the same direction.
- **Random Forest.** Brings together 200 decision trees, each trained on a
  different part of the data. Each tree asks a sequence of questions, such as
  "did the municipality have more than so many cases last month?" or "did the
  temperature go above a certain value?", until it reaches an answer. The score
  is the average of the 200 trees' answers.
- **XGBoost and LightGBM.** Also use trees, 300 in each, but built one after the
  other: each new tree tries to correct the errors the previous ones were still
  making. The score is the sum of all the trees' contributions, converted to a
  value between 0 and 1.

**Why each model has its own cut.** The four models put municipalities in a
similar order, but spread the scores in very different ways. The score at which
each one forecasts an outbreak is usually around 0.10 for LightGBM, 0.20 for
XGBoost, 0.43 for Random Forest and 0.80 for logistic regression. A score of 0.30
is high for XGBoost and low for logistic regression. That is why a score only
means something compared with its own model's cut.

The cut also changes with the horizon. In the three tree models, the further
ahead the forecast, the less sure the model is and the lower every
municipality's score gets: Random Forest's typical cut falls from 0.60 at one
month to 0.30 at six months. With a fixed cut of 0.50, Random Forest would flag
28% of outbreaks six months ahead; with its own cut, it flags 57% (median values
across combinations). Logistic regression is the opposite: its cut sits above
0.50, and a fixed 0.50 would give too many false alarms. The cut is not there to
alert more or less, but to balance the two in each case.

**How the cut is chosen.** We use 2022, 2023 and 2024, each forecast by a version
of the model that did not see it during training. In each year, we try cuts from
0.05 to 0.95 and keep the one that best balances two things: flagging as many of
the outbreaks that actually happened as possible, and raising as few false
alarms as possible. The final cut is the middle value across the three years, so
that an unusual year, like the large 2024 epidemic, does not decide on its own.
This is done separately for each combination of disease, outbreak definition,
horizon and model, 240 cuts in total.

One caveat: the cut is measured with these test versions, and the model behind
the current forecast was trained on all years. We assume it spreads the scores
the same way.

**How the levels come from the cut.**

- **High** starts at the cut. From here on the model forecasts an outbreak.
- **Critical** starts halfway between the cut and 1.
- **Moderate** starts at half the cut. The model does not forecast an outbreak
  yet, but the municipality is getting closer.
- **Low** is everything below that.

For example, with a cut of 0.40: Critical from 0.70, High from 0.40, Moderate
from 0.20.

**Why the score is not a probability.** The share of municipalities in outbreak
changes a lot from one year to the next. Under the more than 100 cases per
100,000 residents definition, it was 20.3% in 2022, 16.7% in 2023 and 39.0% in
2024. An adjustment that turned the score into a "chance of outbreak", learned in
an ordinary year, would be wrong in an epidemic year, and there is no way to know
in advance what the next year will be like. In the previous version of this
project, that adjustment was tested and made results worse. What holds from one
year to the next is the ranking of municipalities, and that ranking is what the
score expresses.

### Reproducibility

The whole pipeline is four notebooks that run top to bottom: collection, building
the table and the labels, features and training, results. The results notebook
re-runs the training notebook's feature code instead of repeating it, and refuses
to produce any figure if the refitted model does not reproduce the metrics saved
on disk to four decimal places.
""",
    "sobre.cortes_titulo": "The cuts for each combination",
    "sobre.cortes_intro": "Score at which each model forecasts an outbreak, for each "
                          "horizon. The levels come from these numbers by the rule "
                          "above.",
    "sobre.cortes_legenda": "— marks a model that did not pass the quality criterion and "
                            "does not appear in the app for that combination.",
    "sobre.autoria_titulo": "Authorship",
    "sobre.autoria_intro": "Undergraduate research project developed at the Institute of "
                           "Mathematical and Computer Sciences of the University of São "
                           "Paulo (ICMC-USP), in São Carlos, funded by USP's Unified "
                           "Scholarship Programme (PUB).",
    "sobre.autoria_aluno": "Student",
    "sobre.autoria_orientador": "Advisor",
    "sobre.autoria_colaboracao": "Collaborators",
}
