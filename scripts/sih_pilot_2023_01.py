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


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    cache = output / ".pysus_cache"
    cache.mkdir(exist_ok=True)
    os.environ["PYSUS_CACHEPATH"] = str(cache)

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(message)s",
    )
    log = logging.getLogger("iara.sih.pilot")

    try:
        import pysus
    except ImportError:
        log.exception("PySUS não está instalado.")
        return 2

    inventory: list[dict[str, Any]] = []
    coverage: list[dict[str, Any]] = []
    selected_frames: list[pd.DataFrame] = []
    errors: list[dict[str, str]] = []

    log.info("Piloto SIH-RD %04d-%02d; consulta de origem para %d UFs.", YEAR, MONTH, len(UFS))
    for uf in UFS:
        row = {
            "uf": uf, "arquivos_listados": 0, "arquivos_baixados": 0,
            "status": "pendente", "erro": "",
        }
        try:
            remote_bag = pysus.ftp.sih(
                state=uf, year=YEAR, month=MONTH,
                source="origin", download=False,
            )
            remote_files = [
                item for item in remote_bag.files
                if str(getattr(item, "name", "")).lower().endswith(".dbc")
            ]
            row["arquivos_listados"] = len(remote_files)
            if not remote_files:
                row["status"] = "nenhum_arquivo_listado"
                coverage.append(row)
                log.warning("%s: nenhum DBC listado.", uf)
                continue

            for item in remote_files:
                inventory.append({
                    "uf_consultada": uf,
                    "nome": getattr(item, "name", ""),
                    "caminho_remoto": getattr(item, "path", ""),
                    "tamanho_remoto_bytes": getattr(item, "size", None),
                    "modificado_remoto": str(getattr(item, "modify", "")),
                    "status_download": "pendente",
                    "sha256_local": "",
                    "tamanho_local_bytes": "",
                    "erro": "",
                })

            local_bag = remote_bag.download()
            local_by_name = {
                Path(str(getattr(item, "path", ""))).name: item
                for item in local_bag.files
            }

            for item in remote_files:
                name = str(getattr(item, "name", ""))
                local = local_by_name.get(name)
                inv = next(
                    (x for x in reversed(inventory)
                     if x["uf_consultada"] == uf and x["nome"] == name),
                    None,
                )
                if local is None:
                    message = "Arquivo listado não apareceu após download."
                    errors.append({"uf": uf, "arquivo": name, "erro": message})
                    if inv:
                        inv["erro"] = message
                    continue

                path = Path(local.path)
                if not path.is_file():
                    message = f"Arquivo local não encontrado: {path}"
                    errors.append({"uf": uf, "arquivo": name, "erro": message})
                    if inv:
                        inv["erro"] = message
                    continue

                if inv:
                    inv.update({
                        "status_download": "baixado",
                        "sha256_local": sha256_file(path),
                        "tamanho_local_bytes": path.stat().st_size,
                    })

                try:
                    frame = asyncio.run(local.load())
                    if not isinstance(frame, pd.DataFrame):
                        frame = pd.DataFrame(frame)
                    selected = filter_rmb_records(frame, name)
                    selected_frames.append(selected)
                    log.info("%s: %d linhas; %d registros RMB/A00-A09.",
                             name, len(frame), len(selected))
                except Exception as exc:
                    message = f"{type(exc).__name__}: {exc}"
                    errors.append({"uf": uf, "arquivo": name, "erro": message})
                    if inv:
                        inv["erro"] = message
                    log.exception("Falha ao ler %s.", name)

            row["arquivos_baixados"] = sum(
                1 for x in inventory
                if x["uf_consultada"] == uf and x["status_download"] == "baixado"
            )
            row["status"] = (
                "download_concluido"
                if row["arquivos_baixados"] == row["arquivos_listados"]
                else "download_parcial"
            )
        except Exception as exc:
            row["status"] = "erro_consulta"
            row["erro"] = f"{type(exc).__name__}: {exc}"
            errors.append({"uf": uf, "arquivo": "", "erro": row["erro"]})
            log.exception("Erro na consulta/download de %s.", uf)
        coverage.append(row)

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

    listed_ufs = {r["uf"] for r in coverage if r["arquivos_listados"] > 0}
    missing_ufs = sorted(set(UFS) - listed_ufs)
    metadata = {
        "projeto": "IARA Data Hub",
        "sistema": "SIH-RD",
        "fonte": "DATASUS FTP, source=origin",
        "pysus_version": importlib.metadata.version("pysus"),
        "python_version": os.sys.version.split()[0],
        "competencia_processamento": f"{YEAR}-{MONTH:02d}",
        "ufs_solicitadas": UFS,
        "ufs_com_arquivos": sorted(listed_ufs),
        "ufs_sem_arquivo_listado": missing_ufs,
        "total_dbc_listados": len(inventory),
        "total_dbc_baixados": int((inventory_df.get("status_download", pd.Series(dtype=str)) == "baixado").sum()),
        "registros_rmb_a00_a09": int(len(records)),
        "aih_repetidas_registradas_em_chaves": int(repetitions.get("registros_em_chaves_repetidas", pd.Series(dtype=int)).sum()),
        "total_erros": len(errors),
        "completo": not errors and not missing_ufs,
        "nota": (
            "Piloto de uma competência de processamento. Não representa o ano civil "
            "de DT_INTER. Nenhuma linha individual nem N_AIH foi exportada nos relatórios."
        ),
        "executado_em_utc": datetime.now(timezone.utc).isoformat(),
    }
    (output / "metadados_execucao.json").write_text(
        json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    shutil.rmtree(cache, ignore_errors=True)
    log.info("Finalizado: DBCs=%d; selecionados=%d; erros=%d; UFs sem arquivo=%d.",
             len(inventory), len(records), len(errors), len(missing_ufs))
    return 0 if metadata["completo"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
