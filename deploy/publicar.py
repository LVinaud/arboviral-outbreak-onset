"""Publica os dados do aplicativo no repositório de dados do Hugging Face.

O aplicativo hospedado sai do código, mas os modelos e tabelas que o 03_train
grava em data/train/ não são versionados no Git: o app os baixa deste
repositório de dados público, arquivo por arquivo, na primeira vez que precisa
(ver app/lib/dados.py).

Uso, da raiz do repositório, depois de `hf auth login` com um token de escrita:

    python deploy/publicar.py

Cria o repositório se ele ainda não existir e envia o estado atual de data/.
Rodar de novo atualiza: é o mesmo comando depois de cada rodada mensal do
pipeline. Previsões e modelos que não valem mais são apagados no mesmo envio.

Dos modelos, só sobem os que o aplicativo oferece (coluna `oferecer` do
limiares_operacao.parquet): 169 de 240, perto de 1 GB.

Opção:
    --repo USUARIO/NOME   repositório de destino (padrão: o que o app lê,
                          dados.HF_REPO_PADRAO)
"""
import argparse
import sys
from pathlib import Path

import pandas as pd
from huggingface_hub import HfApi

RAIZ = Path(__file__).resolve().parents[1]
DADOS = RAIZ / "data"
sys.path.insert(0, str(RAIZ / "app"))

from lib.dados import HF_REPO_PADRAO  # noqa: E402

# Arquivos que o app lê, com o caminho relativo a data/ (ver app/lib/dados.py).
ARQUIVOS_FIXOS = [
    "train/features.parquet",
    "train/limiares_operacao.parquet",
    "master/municipio_mes.parquet",
    "master/labels.parquet",
    "lookup/municipios_sp_estacoes_inmet.xlsx",
]

CARTAO = """---
pretty_name: Alerta de arboviroses, dados do aplicativo
tags:
- epidemiology
- dengue
- brazil
---

# Dados do aplicativo de alerta de arboviroses

Arquivos lidos pelo aplicativo de previsão de surtos de dengue, zika e
chikungunya nos municípios de São Paulo. São gerados pelo pipeline do projeto
(notebooks 01 a 03) a partir de fontes públicas brasileiras, e atualizados a
cada rodada mensal.

- `train/predictions_producao/`: previsões dos meses ainda sem desfecho
- `train/models_producao/`: modelos de produção oferecidos pelo aplicativo
- `train/features.parquet`: matriz de 125 preditores usada na explicação SHAP
- `train/limiares_operacao.parquet`: cortes, métricas e combinações oferecidas
- `master/`: tabela município-mês e rótulos de surto
- `lookup/`: coordenadas dos municípios
"""


def modelos_oferecidos() -> list[str]:
    lim = pd.read_parquet(DADOS / "train/limiares_operacao.parquet")
    lim = lim[lim["oferecer"]] if "oferecer" in lim.columns else lim
    caminhos = [f"train/models_producao/{r.disease}_{r.definition}_h{r.h}_{r.model}.joblib"
                for r in lim.itertuples()]
    faltando = [c for c in caminhos if not (DADOS / c).exists()]
    if faltando:
        sys.exit(f"{len(faltando)} modelos oferecidos não estão em data/, por exemplo "
                 f"{faltando[0]}. Rode a Seção 6 do 03_train.")
    return caminhos


def main() -> None:
    args = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    args.add_argument("--repo", default=HF_REPO_PADRAO)
    repo = args.parse_args().repo

    faltando = [a for a in ARQUIVOS_FIXOS if not (DADOS / a).exists()]
    if faltando:
        sys.exit(f"Faltam arquivos em data/: {faltando}. Rode o pipeline antes.")
    modelos = modelos_oferecidos()

    api = HfApi()
    try:
        conta = api.whoami()["name"]
    except Exception:  # noqa: BLE001
        sys.exit("Sem login no Hugging Face. Rode `hf auth login` com um token de escrita.")
    print(f"Logado como {conta}.")

    api.create_repo(repo, repo_type="dataset", exist_ok=True)
    api.upload_file(path_or_fileobj=CARTAO.encode(), path_in_repo="README.md",
                    repo_id=repo, repo_type="dataset", commit_message="Descrição dos dados")

    print(f"Enviando tabelas para {repo}...")
    api.upload_folder(
        repo_id=repo, repo_type="dataset", folder_path=DADOS,
        allow_patterns=ARQUIVOS_FIXOS + ["train/predictions_producao/*.parquet"],
        delete_patterns=["train/predictions_producao/*"],
        commit_message="Atualiza tabelas e previsões",
    )
    print(f"Enviando {len(modelos)} modelos para {repo} (perto de 1 GB)...")
    api.upload_folder(
        repo_id=repo, repo_type="dataset", folder_path=DADOS,
        allow_patterns=modelos, delete_patterns=["train/models_producao/*"],
        commit_message=f"Atualiza os {len(modelos)} modelos oferecidos",
    )
    print(f"\nPronto: https://huggingface.co/datasets/{repo}\n"
          "Reinicie o app no painel do host para ele ler os dados novos.")


if __name__ == "__main__":
    main()
