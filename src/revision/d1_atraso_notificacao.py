"""D1. Quanto tempo uma notificação de dengue leva para ser encerrada (Seção 2 do artigo).

Lê os arquivos brutos do SINAN de dengue de 2022 e 2023 (data/raw/<coleta>/sinan),
todas as notificações de residentes ou notificadas em SP (SG_UF = 35, o mesmo
filtro do 02_master), sem filtrar pela classificação. Para cada ano:
  n               notificações
  pct_60d, 90d    fração encerrada (DT_ENCERRA) em até 60 e 90 dias da notificação
  mediana_dias    mediana do intervalo entre notificação e encerramento
  pct_classif     fração com classificação final (CLASSI_FIN preenchido)
É o que justifica cortar a série no último mês com 60 dias para consolidar.

Precisa dos arquivos brutos, que não estão no repositório (estão no depósito do
Zenodo citado no README). A saída fica versionada em data/master/, ao lado da
tabela que o 02 monta a partir do mesmo bruto.
"""
import tempfile
from pathlib import Path

import dbfread
import numpy as np
import pandas as pd
from pyreaddbc import dbc2dbf

ROOT = Path(__file__).resolve().parents[2]
RAW = sorted(p for p in (ROOT / "data" / "raw").iterdir() if p.is_dir())[-1]
OUT = ROOT / "data" / "master" / "notification_delay.csv"


def ler(path):
    with tempfile.NamedTemporaryFile(suffix=".dbf", delete=False) as tmp:
        dbf = tmp.name
    dbc2dbf(str(path), dbf)
    linhas = []
    for rec in dbfread.DBF(dbf, encoding="latin1", load=False):
        if str(rec.get("SG_UF", "")).strip() != "35":
            continue
        linhas.append((rec.get("DT_NOTIFIC"), rec.get("DT_ENCERRA"), rec.get("CLASSI_FIN")))
    Path(dbf).unlink(missing_ok=True)
    return pd.DataFrame(linhas, columns=["notific", "encerra", "classi"])


res = []
for ano in (2022, 2023):
    d = ler(RAW / "sinan" / f"DENGBR{str(ano)[-2:]}.dbc")
    notif = pd.to_datetime(d["notific"], errors="coerce")
    enc = pd.to_datetime(d["encerra"], errors="coerce")
    dias = (enc - notif).dt.days
    classi = pd.to_numeric(d["classi"], errors="coerce")
    res.append({"year": ano, "collection": RAW.name, "n_notifications": len(d),
                "pct_closed_60d": float((dias <= 60).mean()),
                "pct_closed_90d": float((dias <= 90).mean()),
                "median_days_to_close": float(np.nanmedian(dias)),
                "pct_with_final_classification": float(classi.notna().mean())})
    print(res[-1], flush=True)

pd.DataFrame(res).to_csv(OUT, index=False)
print("gravado em", OUT.relative_to(ROOT))
