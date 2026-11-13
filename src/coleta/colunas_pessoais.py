"""Personal columns removed from the DATASUS files right after download.

The project never uses them, and the raw collection is archived publicly, so
01_data_collection drops them as soon as each file arrives:

  SIH-SUS (RDSP*): CEP (patient's postal code), CPF_AUT and GESTOR_CPF (CPFs)
  CNES/LT (LTSP*): CPF_CNPJ (owner's CPF or CNPJ)
  SINASC  (DNSP*): DTNASCMAE (mother's date of birth)

DATASUS ships these files as .dbc, its own compressed DBF, and there is no
writer for that format. The cleaned file is therefore the plain DBF, minus
those columns, gzip-compressed: RDSP2401.dbc becomes RDSP2401.dbf.gz. The
columns are cut out byte by byte, so every value left in the file is exactly
the one DATASUS published. 02_master reads both forms through abrir_dbf().
"""
import gzip
import os
import struct
import tempfile
from contextlib import contextmanager
from pathlib import Path

import numpy as np

COLUNAS_PESSOAIS = {
    "RDSP": ("CEP", "CPF_AUT", "GESTOR_CPF"),
    "LTSP": ("CPF_CNPJ",),
    "DNSP": ("DTNASCMAE",),
}
SUFIXO_LIMPO = ".dbf.gz"


def colunas_a_remover(nome: str) -> tuple:
    """Columns to drop from a DATASUS file, by its name (empty if none)."""
    return COLUNAS_PESSOAIS.get(Path(nome).name[:4].upper(), ())


def remover_colunas_dbf(dbf: bytes, colunas) -> bytes:
    """Remove columns from a dBase III file, keeping every other byte as it was."""
    colunas = {c.upper() for c in colunas}
    if dbf[0] != 0x03:
        raise ValueError(f"expected a dBase III file (0x03), got 0x{dbf[0]:02x}")
    n_registros = struct.unpack("<I", dbf[4:8])[0]
    tam_cabecalho = struct.unpack("<H", dbf[8:10])[0]
    tam_registro = struct.unpack("<H", dbf[10:12])[0]

    campos, i = [], 32
    while dbf[i] != 0x0D:
        campos.append(dbf[i:i + 32])
        i += 32
    if i + 1 != tam_cabecalho:
        raise ValueError("unexpected bytes between the field list and the records")
    fim = tam_cabecalho + n_registros * tam_registro
    resto = dbf[fim:]
    if resto not in (b"", b"\x1a"):
        raise ValueError(f"unexpected {len(resto)} bytes after the last record")

    manter = np.ones(tam_registro, dtype=bool)        # byte 0 is the deletion flag
    descritores, pos, removidas = [], 1, set()
    for d in campos:
        nome, largura = d[:11].split(b"\0")[0].decode("latin-1").upper(), d[16]
        if nome in colunas:
            manter[pos:pos + largura] = False
            removidas.add(nome)
        else:
            descritores.append(d)
        pos += largura
    if pos != tam_registro:
        raise ValueError("field widths do not add up to the record length")
    if removidas != colunas:
        raise ValueError(f"columns not found: {sorted(colunas - removidas)}")

    registros = np.frombuffer(dbf, dtype=np.uint8, count=n_registros * tam_registro,
                              offset=tam_cabecalho).reshape(n_registros, tam_registro)
    novo_cabecalho = bytearray(dbf[:32])
    novo_cabecalho[8:10] = struct.pack("<H", 32 + 32 * len(descritores) + 1)
    novo_cabecalho[10:12] = struct.pack("<H", int(manter.sum()))
    return (bytes(novo_cabecalho) + b"".join(descritores) + b"\x0d"
            + registros[:, manter].tobytes() + resto)


def caminho_limpo(caminho_dbc) -> Path:
    """RDSP2401.dbc -> RDSP2401.dbf.gz, in the same folder."""
    caminho_dbc = Path(caminho_dbc)
    return caminho_dbc.with_name(caminho_dbc.stem + SUFIXO_LIMPO)


def limpar_dbc(caminho_dbc) -> Path:
    """Write the .dbf.gz without the personal columns and delete the .dbc."""
    from pyreaddbc import dbc2dbf

    caminho_dbc = Path(caminho_dbc)
    colunas = colunas_a_remover(caminho_dbc.name)
    if not colunas:
        raise ValueError(f"{caminho_dbc.name}: no personal columns listed for this file")
    with tempfile.TemporaryDirectory() as tmp:
        dbf = Path(tmp) / "x.dbf"
        dbc2dbf(str(caminho_dbc), str(dbf))
        limpo = remover_colunas_dbf(dbf.read_bytes(), colunas)
    destino = caminho_limpo(caminho_dbc)
    parcial = destino.with_name(destino.name + ".partial")
    # mtime=0 and no file name in the gzip header: the same input always gives
    # the same bytes, so the archive checksums are reproducible.
    parcial.write_bytes(gzip.compress(limpo, compresslevel=9, mtime=0))
    os.replace(parcial, destino)
    caminho_dbc.unlink()
    return destino


def arquivos_dbf(pasta, prefixo) -> list:
    """The .dbc or cleaned .dbf.gz files of one source, whichever is on disk."""
    achados = {}
    for p in Path(pasta).iterdir():
        nome = p.name.upper()
        if not nome.startswith(prefixo.upper()):
            continue
        if nome.endswith(".DBC"):
            chave = p.name[:-4].upper()
        elif nome.endswith(SUFIXO_LIMPO.upper()):
            chave = p.name[:-len(SUFIXO_LIMPO)].upper()
        else:
            continue
        if chave in achados:
            raise RuntimeError(f"{chave} is on disk both as .dbc and as {SUFIXO_LIMPO}")
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
        elif nome.endswith(SUFIXO_LIMPO):
            with gzip.open(caminho, "rb") as entrada, open(dbf, "wb") as saida:
                while bloco := entrada.read(1 << 24):
                    saida.write(bloco)
        else:
            raise ValueError(f"{caminho.name}: not a .dbc, .dbf.gz or .dbf")
        yield dbf
