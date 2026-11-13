"""Columns kept from the files that hold one record per person.

The DATASUS microdata (SINAN, SIH-SUS, SIM, SINASC, CNES beds) and the Ministry
of Health's list of yellow fever cases carry one record per notification,
admission, death or birth. The pipeline needs only a few columns of each: a
diagnosis or classification, the municipality, the dates that place a record in
a month, and whether the person died or was admitted. 01_data_collection keeps
those and drops every other column as soon as each file arrives, so the raw
collection, which is archived publicly, carries no dates of birth, sex, race,
free text or identifiers. Every record is kept.

DATASUS ships its files as .dbc, its own compressed DBF, and there is no writer
for that format. The reduced file is therefore the plain DBF with only the kept
columns, gzip-compressed: RDSP2401.dbc becomes RDSP2401.dbf.gz. The columns are
cut out byte by byte, so every value left is exactly the one DATASUS published.
02_master and src/revision/d1_atraso_notificacao.py read both forms through
abrir_dbf().
"""
import gzip
import os
import struct
import tempfile
from contextlib import contextmanager
from pathlib import Path

import numpy as np

# SINAN: 02_master counts cases, deaths and admissions and measures the delay from
# symptoms to notification; d1_atraso_notificacao measures the time to close.
_SINAN = ("SG_UF", "ID_MN_RESI", "DT_NOTIFIC", "DT_SIN_PRI", "CLASSI_FIN",
          "EVOLUCAO", "HOSPITALIZ", "DT_ENCERRA")
COLUNAS_USADAS = {
    "DENG": _SINAN,
    "ZIKA": _SINAN,
    "CHIK": _SINAN,
    # SIH-SUS: arbovirus admissions by municipality of residence (month in the name)
    "RDSP": ("DIAG_PRINC", "MUNIC_RES", "MORTE"),
    # CNES beds: SUS beds by municipality (month in the name)
    "LTSP": ("CODUFMUN", "QT_SUS"),
    # SIM: maternal deaths by municipality of residence (year in the name)
    "DOSP": ("CAUSABAS", "CODMUNRES"),
    # SINASC: live births by municipality of residence (year in the name)
    "DNSP": ("CODMUNRES",),
}
# The zika files have no hospitalization field; 02_master treats it as absent.
OPCIONAIS = {"HOSPITALIZ"}
# Yellow fever cases (one CSV): 02_master counts cases and deaths by municipality
# of probable infection and month of symptom onset.
COLUNAS_FEBRE_AMARELA = ("ID", "UF_LPI", "COD_MUN_LPI", "ANO_IS", "MES_IS", "OBITO")
SUFIXO_REDUZIDO = ".dbf.gz"


def colunas_usadas(nome: str) -> tuple:
    """Columns kept from a DATASUS file, by its name (empty if it is not one)."""
    return COLUNAS_USADAS.get(Path(nome).name[:4].upper(), ())


def reduzir_dbf(origem, destino_gz, manter, opcionais=OPCIONAIS) -> list:
    """Write a gzip-compressed copy of a dBase III file with only the columns in
    `manter`, every record and every kept byte as it was. Returns the kept names."""
    manter = {c.upper() for c in manter}
    with open(origem, "rb") as f:
        cabecalho = f.read(32)
        if cabecalho[0] != 0x03:
            raise ValueError(f"expected a dBase III file (0x03), got 0x{cabecalho[0]:02x}")
        n_registros = struct.unpack("<I", cabecalho[4:8])[0]
        tam_cabecalho, tam_registro = struct.unpack("<HH", cabecalho[8:12])
        resto_cabecalho = f.read(tam_cabecalho - 32)

        campos, i = [], 0
        while resto_cabecalho[i] != 0x0D:
            campos.append(resto_cabecalho[i:i + 32])
            i += 32
        if 32 + i + 1 != tam_cabecalho:
            raise ValueError("unexpected bytes between the field list and the records")

        mascara = np.zeros(tam_registro, dtype=bool)
        mascara[0] = True                                  # the deletion flag
        descritores, nomes, pos = [], [], 1
        for d in campos:
            nome, largura = d[:11].split(b"\0")[0].decode("latin-1").upper(), d[16]
            if d[12:16] != b"\0\0\0\0":
                raise ValueError(f"{nome}: field displacement set, the cut would break it")
            if nome in manter:
                mascara[pos:pos + largura] = True
                descritores.append(d)
                nomes.append(nome)
            pos += largura
        if pos != tam_registro:
            raise ValueError("field widths do not add up to the record length")
        faltam = manter - set(nomes) - set(opcionais)
        if faltam:
            raise ValueError(f"columns not found: {sorted(faltam)}")

        novo = bytearray(cabecalho)
        novo[8:10] = struct.pack("<H", 32 + 32 * len(descritores) + 1)
        novo[10:12] = struct.pack("<H", int(mascara.sum()))
        # mtime=0 and no file name in the gzip header: the same input always gives
        # the same bytes, so the archive checksums are reproducible.
        with open(destino_gz, "wb") as bruto, gzip.GzipFile(
                filename="", mode="wb", fileobj=bruto, compresslevel=9, mtime=0) as gz:
            gz.write(bytes(novo) + b"".join(descritores) + b"\x0d")
            bloco = max(1, (64 << 20) // tam_registro)       # about 64 MB at a time
            lidos = 0
            while lidos < n_registros:
                k = min(bloco, n_registros - lidos)
                dados = f.read(k * tam_registro)
                if len(dados) != k * tam_registro:
                    raise ValueError("the file is shorter than its header says")
                registros = np.frombuffer(dados, dtype=np.uint8).reshape(k, tam_registro)
                gz.write(registros[:, mascara].tobytes())
                lidos += k
            fim = f.read()
            if fim not in (b"", b"\x1a"):
                raise ValueError(f"unexpected {len(fim)} bytes after the last record")
            gz.write(fim)
    return nomes


def caminho_reduzido(caminho_dbc) -> Path:
    """RDSP2401.dbc -> RDSP2401.dbf.gz, in the same folder."""
    caminho_dbc = Path(caminho_dbc)
    return caminho_dbc.with_name(caminho_dbc.stem + SUFIXO_REDUZIDO)


def reduzir_dbc(caminho_dbc) -> Path:
    """Write the .dbf.gz with only the columns used and delete the .dbc."""
    from pyreaddbc import dbc2dbf

    caminho_dbc = Path(caminho_dbc)
    manter = colunas_usadas(caminho_dbc.name)
    if not manter:
        raise ValueError(f"{caminho_dbc.name}: no column list for this file")
    destino = caminho_reduzido(caminho_dbc)
    parcial = destino.with_name(destino.name + ".partial")
    with tempfile.TemporaryDirectory() as tmp:
        dbf = Path(tmp) / "x.dbf"
        dbc2dbf(str(caminho_dbc), str(dbf))
        reduzir_dbf(dbf, parcial, manter)
    os.replace(parcial, destino)
    caminho_dbc.unlink()
    return destino


def reduzir_csv_febre_amarela(caminho) -> None:
    """Keep only COLUNAS_FEBRE_AMARELA in the yellow fever case list, in place.
    Every row is kept, and each kept value is the same bytes as in the download."""
    caminho = Path(caminho)
    dados = caminho.read_bytes()
    fim_linha = b"\r\n" if b"\r\n" in dados else b"\n"
    linhas = dados.split(fim_linha)
    termina_com_quebra = linhas[-1] == b""
    if termina_com_quebra:
        linhas = linhas[:-1]
    if b'"' in dados:
        raise ValueError(f"{caminho.name}: quoted fields, a split on ';' would be wrong")
    cabecalho = linhas[0].split(b";")
    nomes = [c.decode("latin-1").strip() for c in cabecalho]
    faltam = set(COLUNAS_FEBRE_AMARELA) - set(nomes)
    if faltam:
        raise ValueError(f"{caminho.name}: columns not found: {sorted(faltam)}")
    indices = [nomes.index(c) for c in COLUNAS_FEBRE_AMARELA]
    saida = []
    for n, linha in enumerate(linhas, start=1):
        campos = linha.split(b";")
        if len(campos) != len(cabecalho):
            raise ValueError(f"{caminho.name}, line {n}: {len(campos)} fields, "
                             f"the header has {len(cabecalho)}")
        saida.append(b";".join(campos[i] for i in indices))
    parcial = caminho.with_name(caminho.name + ".partial")
    parcial.write_bytes(fim_linha.join(saida) + (fim_linha if termina_com_quebra else b""))
    os.replace(parcial, caminho)


def arquivos_dbf(pasta, prefixo) -> list:
    """The .dbc or reduced .dbf.gz files of one source, whichever is on disk."""
    achados = {}
    for p in Path(pasta).iterdir():
        nome = p.name.upper()
        if not nome.startswith(prefixo.upper()):
            continue
        if nome.endswith(".DBC"):
            chave = p.name[:-4].upper()
        elif nome.endswith(SUFIXO_REDUZIDO.upper()):
            chave = p.name[:-len(SUFIXO_REDUZIDO)].upper()
        else:
            continue
        if chave in achados:
            raise RuntimeError(f"{chave} is on disk both as .dbc and as {SUFIXO_REDUZIDO}")
        achados[chave] = p
    return [achados[k] for k in sorted(achados)]


@contextmanager
def abrir_dbf(caminho):
    """Yield the path of a plain .dbf for a .dbc, a .dbf.gz or a .dbf."""
    caminho = Path(caminho)
    nome = caminho.name.lower()
    if nome.endswith(".dbf"):
        yield caminho
        return
    with tempfile.TemporaryDirectory() as tmp:
        dbf = Path(tmp) / "x.dbf"
        if nome.endswith(".dbc"):
            from pyreaddbc import dbc2dbf
            dbc2dbf(str(caminho), str(dbf))
        elif nome.endswith(SUFIXO_REDUZIDO):
            with gzip.open(caminho, "rb") as entrada, open(dbf, "wb") as saida:
                while bloco := entrada.read(1 << 24):
                    saida.write(bloco)
        else:
            raise ValueError(f"{caminho.name}: not a .dbc, .dbf.gz or .dbf")
        yield dbf
