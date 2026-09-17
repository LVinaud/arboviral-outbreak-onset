"""Nomes legíveis para as 125 variáveis do modelo.

Uma explicação que diz `mmam2612_moradia_risco` não explica nada a quem decide
onde mandar a equipe de campo. Este módulo traduz o código da coluna para uma
frase no idioma da tela, compondo a raiz com o sufixo temporal. As palavras
ficam em `i18n/variaveis.py`.

As raízes são 66; os sufixos (`_lag1`, `_roll3`, `_trend3`) são regra, não
exceção, então são compostos por código em vez de enumerados. Assim uma
variável nova ganha rótulo sozinha se a raiz dela estiver lá.
"""
import re

from i18n import TEXTOS, maiuscula, t

_DOENCA = {"dengue": "dengue", "zika": "zika", "chikungunya": "chikungunya",
           "fa": "fa", "febre_amarela": "fa"}

_PADRAO_DOENCA = re.compile(
    r"^(dengue|zika|chikungunya|fa|febre_amarela)_"
    r"(casos|incid|internacoes_sih|latencia_mediana|latencia_p90)$")


def _existe(chave: str) -> bool:
    return chave in TEXTOS["pt"]


def rotular(coluna: str) -> str:
    """Nome legível de uma coluna de feature.

    Devolve o próprio código quando a raiz é desconhecida, para uma variável
    nova aparecer como está em vez de sumir da tela.
    """
    m = re.match(r"^(.*?)_(lag\d+|roll\d+|trend\d+|max|min)$", coluna)
    raiz, sufixo = (m.group(1), m.group(2)) if m else (coluna, None)

    if _existe(f"var.{raiz}"):
        base = t(f"var.{raiz}")
    else:
        d = _PADRAO_DOENCA.match(raiz)
        if d:
            doenca = t(f"doenca_minuscula.{_DOENCA[d.group(1)]}")
            base = maiuscula(t(f"var_medida.{d.group(2)}", d=doenca))
        else:
            base = raiz

    if sufixo:
        complemento = t(f"var_sufixo.{sufixo}") if _existe(f"var_sufixo.{sufixo}") else sufixo
        return t("var.composicao", base=base, sufixo=complemento)
    return base


def cobertura(colunas) -> tuple[int, list[str]]:
    """Quantas colunas têm rótulo de verdade, e quais não têm.

    Serve de rede: se alguém acrescentar variáveis ao `03_train` e esquecer de
    documentá-las em `i18n/variaveis.py`, a tela mostra o código cru e este
    contador denuncia.
    """
    sem = [c for c in colunas if rotular(c) == c]
    return len(colunas) - len(sem), sem
