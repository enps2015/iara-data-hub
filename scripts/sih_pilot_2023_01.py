#!/usr/bin/env python3
"""Piloto SIH-RD: competência 2023-01, todas as UFs, residentes da RMB.

O processamento ocorre em memória no runner. Os artefatos exportados são
agregados e metadados; não exportam linhas individuais nem N_AIH.
"""
from __future__ import annotations

import argparse
import asyncio
import hashlib
import importlib.metadata
import json
import logging
import os
import re
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd

YEAR, MONTH = 2023, 1
UFS = [
    "AC", "AL", "AP", "AM", "BA", "CE", "DF", "ES", "GO", "MA",
    "MT", "MS", "MG", "PA", "PB", "PR", "PE", "PI", "RJ", "RN",
    "RS", "RO", "RR", "SC", "SP", "SE", "TO",
]
MUNICIPIOS = {
    "150080": ("1500800", "Ananindeua"),
    "150140": ("1501402", "Belém"),
    "150150": ("1501501", "Benevides"),
    "150240": ("1502400", "Castanhal"),
    "150442": ("1504422", "Marituba"),
    "150635": ("1506351", "Santa Bárbara do Pará"),
    "150650": ("1506500", "Santa Izabel do Pará"),
}
REQUIRED = {"MUNIC_RES", "DT_INTER", "DIAG_PRINC"}
AUDIT_COLUMNS = [
    "MUNIC_RES", "MUNIC_MOV", "DT_INTER", "DT_SAIDA", "DIAG_PRINC",
    "N_AIH", "IDENT", "ANO_CMPT", "MES_CMPT",
]


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as file:
        for chunk in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def parse_dt_inter(values: pd.Series) -> pd.Series:
    raw = values.astype("string").str.strip()
    result = pd.Series(pd.NaT, index=raw.index, dtype="datetime64[ns]")
    day = raw.str.fullmatch(r"\d{8}", na=False)
    month = raw.str.fullmatch(r"\d{6}", na=False)
    if day.any():
        result.loc[day] = pd.to_datetime(raw.loc[day], format="%Y%m%d", errors="coerce")
    if month.any():
        result.loc[month] = pd.to_datetime(raw.loc[month], format="%Y%m", errors="coerce")
    return result


def filter_rmb_records(frame: pd.DataFrame, filename: str) -> pd.DataFrame:
    data = frame.copy()
    data.columns = [str(column).strip().upper() for column in data.columns]
    missing = sorted(REQUIRED - set(data.columns))
    if missing:
        raise ValueError(f"{filename}: colunas obrigatórias ausentes: {missing}")

    residence = data["MUNIC_RES"].astype("string").str.strip().str.replace(r"\.0$", "", regex=True)
    diagnosis = data["DIAG_PRINC"].astype("string").str.strip().str.upper()
    mask = residence.isin(MUNICIPIOS) & diagnosis.str.match(r"^A0[0-9]", na=False)
    selected = data.loc[mask].copy()
    selected["MUNIC_RES"] = residence.loc[mask]
    selected["cod_ibge"] = selected["MUNIC_RES"].map({k: v[0] for k, v in MUNICIPIOS.items()})
    selected["municipio"] = selected["MUNIC_RES"].map({k: v[1] for k, v in MUNICIPIOS.items()})
    match = re.match(r"^RD([A-Z]{2})\d{4}(?:_\d+)?\.DBC$", Path(filename).name.upper())
    selected["uf_processamento"] = match.group(1) if match else pd.NA
    selected["arquivo_origem"] = Path(filename).name

    for column in AUDIT_COLUMNS:
        if column not in selected.columns:
            selected[column] = pd.NA

    selected["DT_INTER"] = selected["DT_INTER"].astype("string").str.strip()
    parsed = parse_dt_inter(selected["DT_INTER"])
    selected["ano_dt_inter"] = parsed.dt.year.astype("Int64")
    selected["dt_inter_valida"] = parsed.notna()
    return selected


def summarize_records(records: pd.DataFrame) -> pd.DataFrame:
    dimensions = [
        "MUNIC_RES", "municipio", "cod_ibge", "uf_processamento",
        "ANO_CMPT", "MES_CMPT", "ano_dt_inter", "IDENT",
    ]
    if records.empty:
        return pd.DataFrame(columns=dimensions + ["registros_aih"])
    return (
        records.groupby(dimensions, dropna=False)
        .size()
        .reset_index(name="registros_aih")
        .sort_values(["MUNIC_RES", "uf_processamento", "ano_dt_inter"], na_position="last")
    )


def summarize_possible_repetitions(records: pd.DataFrame) -> pd.DataFrame:
    columns = ["municipio", "cod_ibge", "uf_processamento", "IDENT",
               "registros_em_chaves_repetidas", "aih_distintas_repetidas"]
    if records.empty or "N_AIH" not in records:
        return pd.DataFrame(columns=columns)

    ids = records["N_AIH"].astype("string").str.strip().str.replace(r"\.0$", "", regex=True)
    valid = ids.notna() & ids.ne("") & ids.str.lower().ne("nan")
    base = records.loc[valid].copy()
    base["_n_aih"] = ids.loc[valid]
    for col in ("ANO_CMPT", "MES_CMPT"):
        if col not in base:
            base[col] = pd.NA
    key = ["_n_aih", "ANO_CMPT", "MES_CMPT"]
    repeated = base.loc[base.duplicated(key, keep=False)]
    if repeated.empty:
        return pd.DataFrame(columns=columns)
    return (
        repeated.groupby(["municipio", "cod_ibge", "uf_processamento", "IDENT"], dropna=False)
        .agg(
            registros_em_chaves_repetidas=("_n_aih", "size"),
            aih_distintas_repetidas=("_n_aih", "nunique"),
        )
        .reset_index()
    )


def write_csv(frame: pd.DataFrame, path: Path) -> None:
    frame.to_csv(path, index=False, encoding="utf-8-sig", na_rep="")


async def run_extraction(output: Path, log: logging.Logger) -> dict[str, Any]:
    """Retrieve exact monthly SIH-RD filenames without listing the full FTP archive."""
    from ftplib import error_perm
    from pysus.api.ftp.client import FTP
    from pysus.api.extensions import DBC

    cache = output / ".pysus_cache"
    cache.mkdir(exist_ok=True)
    os.environ["PYSUS_CACHEPATH"] = str(cache)

    inventory: list[dict[str, Any]] = []
    coverage: list[dict[str, Any]] = []
    selected_frames: list[pd.DataFrame] = []
    errors: list[dict[str, str]] = []

    ftp = FTP(timeout=45)
    try:
        await ftp.connect()
        ftp_directory = "/dissemin/publicos/SIHSUS/200801_/Dados"
        ftp.ftp.cwd(ftp_directory)
        log.info(
            "FTP DATASUS conectado. Recuperação direta de nomes mensais em %s.",
            ftp_directory,
        )

        def retrieve_exact(name: str) -> Path | None:
            """Retrieve a known filename. A 550 response means it is not present."""
            local_path = cache / name
            try:
                with local_path.open("wb") as output_file:
                    ftp.ftp.retrbinary(
                        f"RETR {name}",
                        output_file.write,
                        blocksize=1024 * 1024,
                    )
            except error_perm as exc:
                local_path.unlink(missing_ok=True)
                if str(exc).lstrip().startswith("550"):
                    return None
                raise

            if not local_path.is_file() or local_path.stat().st_size == 0:
                local_path.unlink(missing_ok=True)
                raise ValueError(f"Download vazio ou inexistente: {name}")
            return local_path

        for uf in UFS:
            stem = f"RD{uf}{str(YEAR)[-2:]}{MONTH:02d}"
            row = {
                "uf": uf,
                "arquivos_listados": 0,
                "arquivos_baixados": 0,
                "status": "pendente",
                "erro": "",
            }

            # Normal file first. DATASUS splits oversized files as _1, _2, ...
            # If the unsplit name is absent, probe the numbered parts.
            found: list[tuple[str, Path]] = []
            base_name = f"{stem}.dbc"
            try:
                base_path = retrieve_exact(base_name)
                if base_path is not None:
                    found.append((base_name, base_path))
                else:
                    for part in range(1, 11):
                        part_name = f"{stem}_{part}.dbc"
                        part_path = retrieve_exact(part_name)
                        if part_path is not None:
                            found.append((part_name, part_path))
            except Exception as exc:
                message = f"{type(exc).__name__}: {exc}"
                row["erro"] = message
                errors.append({"uf": uf, "arquivo": base_name, "erro": message})
                log.exception("Falha ao recuperar arquivos SIH da UF %s.", uf)

            row["arquivos_listados"] = len(found)
            for name, local_path in found:
                entry = {
                    "uf_consultada": uf,
                    "nome": name,
                    "caminho_remoto": f"{ftp_directory}/{name}",
                    "tamanho_remoto_bytes": "",
                    "modificado_remoto": "",
                    "grupo": "RD",
                    "status_download": "baixado",
                    "sha256_local": sha256_file(local_path),
                    "tamanho_local_bytes": local_path.stat().st_size,
                    "erro": "",
                }
                inventory.append(entry)
                row["arquivos_baixados"] += 1

                try:
                    dbc = DBC(path=local_path)
                    frame = await dbc.load()
                    if not isinstance(frame, pd.DataFrame):
                        frame = pd.DataFrame(frame)
                    selected = filter_rmb_records(frame, name)
                    selected_frames.append(selected)
                    log.info(
                        "%s: %d linhas brutas; %d registros RMB/A00-A09.",
                        name, len(frame), len(selected)
                    )
                except Exception as exc:
                    message = f"{type(exc).__name__}: {exc}"
                    entry["erro"] = message
                    errors.append({"uf": uf, "arquivo": name, "erro": message})
                    log.exception("Falha ao interpretar %s.", name)

            if row["erro"]:
                row["status"] = "erro_recuperacao"
            elif not found:
                row["status"] = "nenhum_arquivo_mensal_encontrado"
                log.warning("%s: nenhum arquivo mensal encontrado para %04d-%02d.", uf, YEAR, MONTH)
            else:
                row["status"] = "download_concluido"
                log.info("%s: %d arquivo(s) recuperado(s).", uf, len(found))
            coverage.append(row)

    finally:
        await ftp.close()

    records = (
        pd.concat(selected_frames, ignore_index=True, sort=False)
        if selected_frames else pd.DataFrame()
    )
    inventory_df = pd.DataFrame(inventory)
    coverage_df = pd.DataFrame(coverage)
    error_df = pd.DataFrame(errors, columns=["uf", "arquivo", "erro"])
    summary = summarize_records(records)
    repetitions = summarize_possible_repetitions(records)

    write_csv(inventory_df, output / "inventario_dbc.csv")
    write_csv(coverage_df, output / "cobertura_arquivos_por_uf.csv")
    write_csv(summary, output / "resumo_por_municipio_uf_ident.csv")
    write_csv(repetitions, output / "repeticoes_n_aih_resumo.csv")
    write_csv(error_df, output / "erros_execucao.csv")

    found_ufs = sorted({
        row["uf"] for row in coverage if row["arquivos_listados"] > 0
    })
    missing_ufs = sorted(set(UFS) - set(found_ufs))
    metadata = {
        "projeto": "IARA Data Hub",
        "sistema": "SIH-RD",
        "fonte": "FTP DATASUS oficial (ftp.datasus.gov.br)",
        "pysus_version": importlib.metadata.version("pysus"),
        "python_version": os.sys.version.split()[0],
        "diretorio_ftp": ftp_directory,
        "competencia_processamento": f"{YEAR}-{MONTH:02d}",
        "ufs_solicitadas": UFS,
        "ufs_com_arquivos": found_ufs,
        "ufs_sem_arquivo_mensal_encontrado": missing_ufs,
        "total_dbc_rd_listados_e_baixados": int(len(inventory)),
        "total_dbc_interpretados": int(
            sum(1 for entry in inventory if not entry["erro"])
        ),
        "registros_rmb_a00_a09": int(len(records)),
        "aih_repetidas_registradas_em_chaves": int(
            repetitions.get("registros_em_chaves_repetidas", pd.Series(dtype=int)).sum()
        ),
        "total_erros": len(errors),
        "completo": not errors and not missing_ufs,
        "nota": (
            "Arquivos consultados por nome exato via RETR no diretório oficial "
            "SIH-RD (2008 em diante), sem varredura do diretório inteiro. "
            "Competência de processamento não equivale ao ano civil de DT_INTER. "
            "Nenhuma linha individual nem N_AIH foi exportada nos relatórios."
        ),
        "executado_em_utc": datetime.now(timezone.utc).isoformat(),
    }
    (output / "metadados_execucao.json").write_text(
        json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    shutil.rmtree(cache, ignore_errors=True)
    log.info(
        "Finalizado: DBCs=%d; selecionados=%d; erros=%d; UFs sem arquivo=%d.",
        len(inventory), len(records), len(errors), len(missing_ufs)
    )
    return metadata

def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=True)

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(message)s",
    )
    log = logging.getLogger("iara.sih.pilot")

    try:
        metadata = asyncio.run(run_extraction(output, log))
    except Exception:
        log.exception("Falha fatal ao executar o piloto SIH via FTP.")
        return 2

    return 0 if metadata["completo"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
