"""Nomes legíveis das variáveis do modelo, para a explicação SHAP.

A composição (raiz + sufixo temporal) está em `lib/rotulos.py`; aqui ficam só
as palavras. `var.<raiz>` é o nome da variável, `var_sufixo.<sufixo>` o
complemento temporal e `var_medida.<medida>` as medidas por doença, com `{d}`
no lugar do nome da doença.
"""

PT = {
    "var.composicao": "{base}, {sufixo}",
    # --- clima (NASA POWER) ---
    "var.t2m": "Temperatura média",
    "var.prectotcorr": "Chuva acumulada",
    "var.rh2m": "Umidade relativa do ar",
    "var.ws10m": "Velocidade do vento",
    "var.ps": "Pressão atmosférica",
    # --- calendário ---
    "var.mes_sin": "Posição no calendário (seno do mês)",
    "var.mes_cos": "Posição no calendário (cosseno do mês)",
    # --- território e ambiente ---
    "var.pct_agricultura": "Área de agricultura e pastagem",
    "var.pct_agua": "Área coberta por água",
    "var.pct_floresta": "Área de floresta",
    "var.pct_nao_vegetado": "Área sem vegetação (urbana, solo exposto)",
    "var.pct_natural_nao_florestal": "Área natural não florestal",
    "var.area_km2": "Área do município",
    "var.densidade_hab_km2": "Densidade populacional",
    # --- população e economia ---
    "var.pop_residente": "População residente",
    "var.pib_per_capita": "PIB por habitante",
    "var.gini_2010": "Desigualdade de renda (Gini, 2010)",
    "var.idhm_2010": "Índice de desenvolvimento humano (2010)",
    "var.num_favelas": "Número de favelas",
    "var.pop_favelas": "População em favelas",
    "var.pendulares_saem_trabalho": "Moradores que trabalham em outro município",
    "var.capag_A": "Capacidade de pagamento nota A",
    "var.capag_B": "Capacidade de pagamento nota B",
    "var.capag_C": "Capacidade de pagamento nota C",
    "var.capag_D": "Capacidade de pagamento nota D",
    # --- saneamento (SINISA) ---
    "var.iag0001_atend_agua_pct": "Domicílios com água tratada",
    "var.ies0001_atend_esgoto_pct": "Domicílios com coleta de esgoto",
    "var.ies0007_esgoto_tratado_pct": "Esgoto que recebe tratamento",
    "var.iap0001_vias_pavimentadas_pct": "Vias pavimentadas",
    # --- atenção primária (e-Gestor) ---
    "var.esf_cobertura_pct": "Cobertura da Estratégia Saúde da Família",
    "var.esf_qt_equipes": "Equipes de saúde da família",
    "var.esf_pop_referencia": "População coberta pela saúde da família",
    "var.esf_metodologia_AB": "Cobertura calculada pela metodologia da atenção básica",
    "var.esf_metodologia_APS": "Cobertura calculada pela metodologia da atenção primária",
    "var.rmm_por_100k_nv": "Mortalidade materna por 100 mil nascidos vivos",
    "var.cob_vac_fa_pct": "Cobertura vacinal de febre amarela",
    # --- capacidade municipal (MUNIC) ---
    "var.msau28_pacs": "Tem programa de agentes comunitários de saúde",
    "var.msau541_vig_sanitaria": "Tem vigilância sanitária",
    "var.msau542_vig_epidemiologica": "Tem vigilância epidemiológica",
    "var.msau543_controle_endemias": "Tem serviço de controle de endemias",
    "var.mgrd01_seca": "Registro de seca nos últimos anos",
    "var.mgrd06_alagamento": "Registro de alagamento",
    "var.mgrd07_erosao": "Registro de erosão",
    "var.mgrd08_enchente_gradual": "Registro de enchente gradual",
    "var.mgrd11_enxurrada": "Registro de enxurrada",
    "var.mgrd14_deslizamento": "Registro de deslizamento",
    "var.mgrd201_mapeamento_risco": "Tem mapeamento de áreas de risco",
    "var.mmam2612_moradia_risco": "Domicílios em área de risco",
    # --- sufixos temporais ---
    "var_sufixo.lag1": "no mês anterior",
    "var_sufixo.lag2": "há 2 meses",
    "var_sufixo.lag3": "há 3 meses",
    "var_sufixo.lag6": "há 6 meses",
    "var_sufixo.lag12": "há 12 meses (mesmo mês do ano passado)",
    "var_sufixo.roll3": "média dos 3 meses anteriores",
    "var_sufixo.roll6": "média dos 6 meses anteriores",
    "var_sufixo.trend3": "tendência dos últimos 3 meses",
    "var_sufixo.max": "máximo",
    "var_sufixo.min": "mínimo",
    # --- medidas por doença ---
    "var_medida.casos": "Casos de {d}",
    "var_medida.incid": "Incidência de {d} por 100 mil habitantes",
    "var_medida.internacoes_sih": "Internações por {d}",
    "var_medida.latencia_mediana": "Atraso mediano na notificação de {d}",
    "var_medida.latencia_p90": "Atraso na notificação de {d} (percentil 90)",
}

EN = {
    "var.composicao": "{base}, {sufixo}",
    # --- climate (NASA POWER) ---
    "var.t2m": "Mean temperature",
    "var.prectotcorr": "Total rainfall",
    "var.rh2m": "Relative humidity",
    "var.ws10m": "Wind speed",
    "var.ps": "Atmospheric pressure",
    # --- calendar ---
    "var.mes_sin": "Time of year (sine of the month)",
    "var.mes_cos": "Time of year (cosine of the month)",
    # --- territory and environment ---
    "var.pct_agricultura": "Farmland and pasture area",
    "var.pct_agua": "Area covered by water",
    "var.pct_floresta": "Forest area",
    "var.pct_nao_vegetado": "Non-vegetated area (urban, bare soil)",
    "var.pct_natural_nao_florestal": "Natural non-forest area",
    "var.area_km2": "Municipality area",
    "var.densidade_hab_km2": "Population density",
    # --- population and economy ---
    "var.pop_residente": "Resident population",
    "var.pib_per_capita": "GDP per capita",
    "var.gini_2010": "Income inequality (Gini, 2010)",
    "var.idhm_2010": "Human development index (2010)",
    "var.num_favelas": "Number of favelas",
    "var.pop_favelas": "Population living in favelas",
    "var.pendulares_saem_trabalho": "Residents who work in another municipality",
    "var.capag_A": "Fiscal capacity rating A",
    "var.capag_B": "Fiscal capacity rating B",
    "var.capag_C": "Fiscal capacity rating C",
    "var.capag_D": "Fiscal capacity rating D",
    # --- sanitation (SINISA) ---
    "var.iag0001_atend_agua_pct": "Households with treated water",
    "var.ies0001_atend_esgoto_pct": "Households with sewage collection",
    "var.ies0007_esgoto_tratado_pct": "Sewage that is treated",
    "var.iap0001_vias_pavimentadas_pct": "Paved roads",
    # --- primary care (e-Gestor) ---
    "var.esf_cobertura_pct": "Family Health Strategy coverage",
    "var.esf_qt_equipes": "Family health teams",
    "var.esf_pop_referencia": "Population covered by family health teams",
    "var.esf_metodologia_AB": "Coverage computed with the basic care method",
    "var.esf_metodologia_APS": "Coverage computed with the primary care method",
    "var.rmm_por_100k_nv": "Maternal mortality per 100,000 live births",
    "var.cob_vac_fa_pct": "Yellow fever vaccination coverage",
    # --- municipal capacity (MUNIC) ---
    "var.msau28_pacs": "Has a community health agents programme",
    "var.msau541_vig_sanitaria": "Has health inspection services",
    "var.msau542_vig_epidemiologica": "Has epidemiological surveillance",
    "var.msau543_controle_endemias": "Has an endemic disease control service",
    "var.mgrd01_seca": "Drought recorded in recent years",
    "var.mgrd06_alagamento": "Flooding recorded",
    "var.mgrd07_erosao": "Erosion recorded",
    "var.mgrd08_enchente_gradual": "Gradual river flooding recorded",
    "var.mgrd11_enxurrada": "Flash flood recorded",
    "var.mgrd14_deslizamento": "Landslide recorded",
    "var.mgrd201_mapeamento_risco": "Has mapped risk areas",
    "var.mmam2612_moradia_risco": "Households in risk areas",
    # --- time suffixes ---
    "var_sufixo.lag1": "previous month",
    "var_sufixo.lag2": "2 months earlier",
    "var_sufixo.lag3": "3 months earlier",
    "var_sufixo.lag6": "6 months earlier",
    "var_sufixo.lag12": "12 months earlier (same month last year)",
    "var_sufixo.roll3": "average of the previous 3 months",
    "var_sufixo.roll6": "average of the previous 6 months",
    "var_sufixo.trend3": "trend over the last 3 months",
    "var_sufixo.max": "maximum",
    "var_sufixo.min": "minimum",
    # --- per-disease measures ---
    "var_medida.casos": "{d} cases",
    "var_medida.incid": "{d} incidence per 100,000 residents",
    "var_medida.internacoes_sih": "{d} hospitalisations",
    "var_medida.latencia_mediana": "Median notification delay for {d}",
    "var_medida.latencia_p90": "Notification delay for {d} (90th percentile)",
}
