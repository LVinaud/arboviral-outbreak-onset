"""Testes de fumaça do aplicativo e da tradução.

Rodar da raiz do repositório:
    python -m unittest discover tests

1. Os textos em português e em inglês têm as mesmas chaves e os mesmos campos
   variáveis (um "{mes}" que falta numa das línguas quebra a tela só nela).
2. Toda chave usada no código existe, inclusive as montadas a partir de
   códigos (doença, definição, modelo, faixa...).
3. Cada tela abre nos dois idiomas sem exceção, o idioma acompanha a troca de
   tela e a troca de idioma não perde a doença e a antecedência escolhidas.

Os testes 3 precisam dos artefatos do `03_train` em `data/train/` e são
pulados quando eles não existem.
"""
import re
import sys
import unittest
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
APP = RAIZ / "app"
sys.path.insert(0, str(APP))

import i18n  # noqa: E402
from lib import comparacao, dados  # noqa: E402

TELAS = ["alertas", "estado", "municipio", "desempenho", "sobre"]
TEM_ARTEFATOS = (RAIZ / "data" / "train" / "predictions_producao").exists()


class Dicionarios(unittest.TestCase):
    def test_mesmas_chaves(self):
        pt, en = set(i18n.TEXTOS["pt"]), set(i18n.TEXTOS["en"])
        self.assertEqual(sorted(pt - en), [], "chaves só em português")
        self.assertEqual(sorted(en - pt), [], "chaves só em inglês")

    def test_mesmos_campos(self):
        diferentes = {
            chave: (i18n.campos_de(texto), i18n.campos_de(i18n.TEXTOS["en"][chave]))
            for chave, texto in i18n.TEXTOS["pt"].items()
            if i18n.campos_de(texto) != i18n.campos_de(i18n.TEXTOS["en"][chave])
        }
        self.assertEqual(diferentes, {})

    def test_sem_texto_vazio(self):
        vazios = [(lingua, chave) for lingua, textos in i18n.TEXTOS.items()
                  for chave, texto in textos.items()
                  if not texto.strip() and not chave.startswith("comp.unidade.")]
        self.assertEqual(vazios, [])


class ChavesUsadas(unittest.TestCase):
    def test_chaves_literais_existem(self):
        padrao = re.compile(r"""\bt\(\s*["']([a-z_]+\.[a-zA-Z0-9_.]+)["']""")
        faltando = []
        for arquivo in APP.rglob("*.py"):
            if "i18n" in arquivo.parts:
                continue
            for chave in padrao.findall(arquivo.read_text(encoding="utf-8")):
                if chave not in i18n.TEXTOS["pt"]:
                    faltando.append(f"{arquivo.relative_to(RAIZ)}: {chave}")
        self.assertEqual(faltando, [])

    def test_chaves_montadas_existem(self):
        chaves = []
        chaves += [f"doenca.{d}" for d in dados.DOENCAS]
        chaves += [f"doenca_minuscula.{d}" for d in dados.DOENCAS]
        chaves += [f"definicao.{d}" for d in dados.DEFINICOES]
        chaves += [f"modelo.{m}" for m in dados.MODELOS]
        chaves += [f"faixa.{f}" for f in dados.NOMES_FAIXA]
        chaves += [f"acao.{f}" for f in dados.NOMES_FAIXA]
        chaves += [f"acao_curta.{f}" for f in dados.NOMES_FAIXA]
        chaves += [f"situacao.{s}" for s in (dados.EM_SURTO, dados.SEM_SURTO, dados.SEM_DADO)]
        chaves += [f"comp.porte.{i}" for i in range(len(comparacao.FAIXAS_PORTE) - 1)]
        for ind in comparacao.INDICADORES:
            chaves += [f"comp.ind.{ind.coluna}", f"comp.unidade.{ind.coluna}",
                       f"comp.fonte.{ind.coluna}", f"comp.tema.{ind.tema}"]
        chaves += [f"mun.origem.{o}" for o in ("alertas", "mapa", "top15", "vizinhos", "outra")]
        chaves += [f"des.metrica.{m}" for m in ("precisao", "cobertura", "auroc", "auprc")]
        chaves += [f"estado.porte_{i}" for i in range(4)]
        chaves += [f"estado.contar_{c}" for c in ("municipios", "populacao")]
        chaves += [f"mapa_hist.faixa_{i}" for i in range(5)]
        faltando = [c for c in chaves if c not in i18n.TEXTOS["pt"]]
        self.assertEqual(faltando, [])

    @unittest.skipUnless((RAIZ / "data" / "train" / "features.parquet").exists(),
                         "sem data/train/features.parquet")
    def test_todas_as_variaveis_tem_nome(self):
        import pandas as pd
        from lib.rotulos import rotular

        colunas = [c for c in pd.read_parquet(RAIZ / "data" / "train" / "features.parquet")
                   .columns if c not in ("cod_ibge", "ano", "mes")]
        sem_nome = [c for c in colunas if rotular(c) == c]
        self.assertEqual(sem_nome, [])


@unittest.skipUnless(TEM_ARTEFATOS, "sem os artefatos do 03_train em data/train/")
class Telas(unittest.TestCase):
    def _abrir(self, tela: str, lingua: str):
        from streamlit.testing.v1 import AppTest

        at = AppTest.from_file(str(APP / "app.py"), default_timeout=300)
        at.query_params["lang"] = lingua     # como um link com ?lang=en
        at.run()
        if tela != "alertas":
            at.switch_page(f"screens/{tela}.py")
            at.run()
        return at

    def _conferir(self, at, tela: str, lingua: str):
        self.assertEqual([e.value for e in at.exception], [], f"{tela} em {lingua}")
        titulo = {"alertas": "alertas.titulo", "estado": "estado.titulo",
                  "municipio": "mun.titulo", "desempenho": "des.titulo",
                  "sobre": "sobre.titulo"}[tela]
        self.assertEqual(at.title[0].value, i18n.TEXTOS[lingua][titulo])
        self.assertEqual(at.query_params["lang"], [lingua])

    def test_telas_em_portugues(self):
        for tela in TELAS:
            with self.subTest(tela=tela):
                self._conferir(self._abrir(tela, "pt"), tela, "pt")

    def test_telas_em_ingles(self):
        for tela in TELAS:
            with self.subTest(tela=tela):
                self._conferir(self._abrir(tela, "en"), tela, "en")

    def test_escolhas_sobrevivem_a_troca_de_idioma(self):
        at = self._abrir("alertas", "pt")
        at.selectbox(key="w_cfg_doenca").set_value("chikungunya").run()
        at.selectbox(key="w_cfg_h").set_value(3).run()
        at.session_state["lang"] = "en"     # como um clique em "English"
        at.run()
        self._conferir(at, "alertas", "en")
        self.assertEqual(at.selectbox(key="w_cfg_doenca").value, "chikungunya")
        self.assertEqual(at.selectbox(key="w_cfg_h").value, 3)

    def test_idioma_acompanha_a_troca_de_tela(self):
        at = self._abrir("alertas", "en")
        at.switch_page("screens/municipio.py")
        at.run()
        self._conferir(at, "municipio", "en")

    def test_desempenho_abre_em_um_mes(self):
        at = self._abrir("alertas", "pt")
        self.assertEqual(at.selectbox(key="w_cfg_h").value, 6)
        at.switch_page("screens/desempenho.py")
        at.run()
        self.assertEqual(at.selectbox(key="w_desempenho_h").value, 1)


if __name__ == "__main__":
    unittest.main()
