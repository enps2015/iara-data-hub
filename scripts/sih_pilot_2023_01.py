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
    match = re.match(r"^RD([A-Z]{2})\d{4}\.DBC$", Path(filename).name.upper())
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
    """Discover and download the Jan/2023 RD files through PySUS's FTP API."""
    cache = output / ".pysus_cache"
    cache.mkdir(exist_ok=True)
    os.environ["PYSUS_CACHEPATH"] = str(cache)

    from pysus.api.ftp.client import FTP
    from pysus.api.ftp.databases import SIH
    from pysus.api.ftp.models import Directory
    from pysus.api.models import BaseRemoteFile, BaseRemoteGroup

    inventory: list[dict[str, Any]] = []
    coverage: list[dict[str, Any]] = []
    selected_frames: list[pd.DataFrame] = []
    errors: list[dict[str, str]] = []

    ftp = FTP(timeout=45)
    try:
        await ftp.connect()
        # The IARA series starts in 2017. Restrict discovery to the modern
        # SIH directory (2008 onward), avoiding the legacy 1992–2007 archive.
        sih = SIH(
            client=ftp,
            paths=[Directory("/dissemin/publicos/SIHSUS/200801_/Dados")],
        )
        log.info("Iniciando listagem PySUS do diretório SIH 200801_/Dados.")
        # PySUS parses the official DBC filename metadata (group, UF, year, month).
        content = await sih.content
        log.info("Listagem PySUS concluída: %d entradas no diretório moderno.", len(content))
        remote_files: list[BaseRemoteFile] = []
        for item in content:
            if isinstance(item, BaseRemoteFile):
                remote_files.append(item)
            elif isinstance(item, BaseRemoteGroup):
                remote_files.extend(await item.files)

        log.info("FTP DATASUS: %d entradas SIH recebidas via PySUS.", len(content))
        log.info(
            "FTP DATASUS: %d arquivos remotos; amostra: %s",
            len(remote_files),
            [file.name for file in remote_files[:15]],
        )

        monthly_files = [
            file for file in remote_files
            if getattr(file, "year", None) == YEAR
            and getattr(file, "month", None) == MONTH
            and str(getattr(getattr(file, "group", None), "name", "")).upper() == "RD"
            and str(getattr(file, "state", "")).upper() in UFS
        ]

        by_uf: dict[str, list[BaseRemoteFile]] = {uf: [] for uf in UFS}
        for remote in monthly_files:
            by_uf[str(remote.state).upper()].append(remote)

        log.info(
            "FTP DATASUS: %d DBCs RD identificados para %04d-%02d.",
            len(monthly_files), YEAR, MONTH
        )

        for uf in UFS:
            files = sorted(by_uf[uf], key=lambda item: item.name)
            row = {
                "uf": uf,
                "arquivos_listados": len(files),
                "arquivos_baixados": 0,
                "status": "nenhum_arquivo_listado" if not files else "pendente",
                "erro": "",
            }
            if not files:
                coverage.append(row)
                log.warning("%s: nenhum DBC RD para %04d-%02d no catálogo FTP.", uf, YEAR, MONTH)
                continue

            for remote in files:
                inv = {
                    "uf_consultada": uf,
                    "nome": remote.name,
                    "caminho_remoto": str(remote.path),
                    "tamanho_remoto_bytes": getattr(remote, "size", ""),
                    "modificado_remoto": str(getattr(remote, "modify", "")),
                    "grupo": "RD",
                    "status_download": "pendente",
                    "sha256_local": "",
                    "tamanho_local_bytes": "",
                    "erro": "",
                }
                inventory.append(inv)
                try:
                    local = await remote.download()
                    local_path = Path(local.path)
                    if not local_path.is_file():
                        raise FileNotFoundError(f"Arquivo local não encontrado: {local_path}")

                    inv.update({
                        "status_download": "baixado",
                        "sha256_local": sha256_file(local_path),
                        "tamanho_local_bytes": local_path.stat().st_size,
                    })
                    frame = await local.load()
                    if not isinstance(frame, pd.DataFrame):
                        frame = pd.DataFrame(frame)

                    selected = filter_rmb_records(frame, remote.name)
                    selected_frames.append(selected)
                    row["arquivos_baixados"] += 1
                    log.info(
                        "%s: %d linhas brutas; %d registros RMB/A00-A09.",
                        remote.name, len(frame), len(selected)
                    )
                except Exception as exc:
                    message = f"{type(exc).__name__}: {exc}"
                    inv["erro"] = message
                    errors.append({"uf": uf, "arquivo": remote.name, "erro": message})
                    log.exception("Falha ao baixar/processar %s.", remote.name)

            row["status"] = (
                "download_concluido"
                if row["arquivos_baixados"] == row["arquivos_listados"]
                else "download_parcial"
            )
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

    listed_ufs = {
        row["uf"] for row in coverage if row["arquivos_listados"] > 0
    }
    missing_ufs = sorted(set(UFS) - listed_ufs)
    metadata = {
        "projeto": "IARA Data Hub",
        "sistema": "SIH-RD",
        "fonte": "FTP DATASUS oficial via PySUS",
        "pysus_version": importlib.metadata.version("pysus"),
        "python_version": os.sys.version.split()[0],
        "competencia_processamento": f"{YEAR}-{MONTH:02d}",
        "ufs_solicitadas": UFS,
        "ufs_com_arquivos": sorted(listed_ufs),
        "ufs_sem_dbc_listado": missing_ufs,
        "total_entradas_dataset_sih": len(content),
        "total_arquivos_remotos": len(remote_files),
        "total_dbc_rd_listados": len(monthly_files),
        "total_dbc_baixados": int(
            (inventory_df.get("status_download", pd.Series(dtype=str)) == "baixado").sum()
        ),
        "registros_rmb_a00_a09": int(len(records)),
        "aih_repetidas_registradas_em_chaves": int(
            repetitions.get("registros_em_chaves_repetidas", pd.Series(dtype=int)).sum()
        ),
        "total_erros": len(errors),
        "completo": not errors and not missing_ufs,
        "nota": (
            "Descoberta de arquivos feita pela API FTP documentada do PySUS; "
            "competência de processamento não equivale ao ano civil de DT_INTER. "
            "Nenhuma linha individual nem N_AIH foi exportada nos relatórios."
        ),
        "executado_em_utc": datetime.now(timezone.utc).isoformat(),
    }
    (output / "metadados_execucao.json").write_text(
        json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    shutil.rmtree(cache, ignore_errors=True)
    log.info(
        "Finalizado: arquivos RD=%d; selecionados=%d; erros=%d; UFs sem arquivo=%d.",
        len(monthly_files), len(records), len(errors), len(missing_ufs)
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
