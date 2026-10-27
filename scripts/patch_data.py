#!/usr/bin/env python3
"""Reconcile annual population estimates from the cited FAPESPA/IBGE table.

This script intentionally updates only 2017–2021, the years covered by the
source below. It does not fill missing population values in later years with
one fixed number. Values for 2022–2025 remain untouched pending source review.
"""
import csv
from pathlib import Path

SOURCE_URL = (
    "https://www.fapespa.pa.gov.br/sistemas/anuario2021/tabelas/demografia/"
    "tab-1.1-populacao-total-e-estimativas-populacionais-2017-a-2021.htm"
)
CSV_PATH = Path(__file__).resolve().parents[1] / "data" / "iara" / "iara_municipios_rmb.csv"

POPULATION_BY_YEAR = {
    2017: {
        "Ananindeua (PA)": 516057, "Belém (PA)": 1452275,
        "Benevides (PA)": 60990, "Castanhal (PA)": 195253,
        "Marituba (PA)": 127858, "Santa Bárbara do Pará (PA)": 20492,
        "Santa Izabel do Pará (PA)": 68836,
    },
    2018: {
        "Ananindeua (PA)": 525566, "Belém (PA)": 1485732,
        "Benevides (PA)": 61689, "Castanhal (PA)": 198294,
        "Marituba (PA)": 129321, "Santa Bárbara do Pará (PA)": 20704,
        "Santa Izabel do Pará (PA)": 69746,
    },
    2019: {
        "Ananindeua (PA)": 530598, "Belém (PA)": 1492745,
        "Benevides (PA)": 62737, "Castanhal (PA)": 200793,
        "Marituba (PA)": 131521, "Santa Bárbara do Pará (PA)": 21079,
        "Santa Izabel do Pará (PA)": 70801,
    },
    2020: {
        "Ananindeua (PA)": 535547, "Belém (PA)": 1499641,
        "Benevides (PA)": 63768, "Castanhal (PA)": 203251,
        "Marituba (PA)": 133685, "Santa Bárbara do Pará (PA)": 21449,
        "Santa Izabel do Pará (PA)": 71837,
    },
    2021: {
        "Ananindeua (PA)": 540410, "Belém (PA)": 1506420,
        "Benevides (PA)": 64780, "Castanhal (PA)": 205667,
        "Marituba (PA)": 135812, "Santa Bárbara do Pará (PA)": 21811,
        "Santa Izabel do Pará (PA)": 72856,
    },
}


def main() -> None:
    with CSV_PATH.open("r", encoding="utf-8", newline="") as source:
        reader = csv.DictReader(source)
        if not reader.fieldnames:
            raise ValueError(f"CSV sem cabeçalho: {CSV_PATH}")
        rows = list(reader)
        fieldnames = list(reader.fieldnames)

    required = {
        "municipio", "ano", "populacao",
        "internacoes_hidricas_total", "taxa_internacoes_hidricas_10k",
    }
    if not required.issubset(fieldnames):
        raise ValueError(f"Colunas ausentes no CSV: {sorted(required - set(fieldnames))}")

    updated = 0
    for year, population_map in POPULATION_BY_YEAR.items():
        for municipality, population in population_map.items():
            matches = [
                row for row in rows
                if row["municipio"] == municipality and int(row["ano"]) == year
            ]
            if len(matches) != 1:
                raise ValueError(
                    f"Esperado um registro para {municipality}/{year}; encontrados {len(matches)}"
                )

            row = matches[0]
            count = float(row["internacoes_hidricas_total"])
            if count < 0:
                raise ValueError(f"Contagem de internações negativa em {municipality}/{year}")
            row["populacao"] = str(population)
            row["taxa_internacoes_hidricas_10k"] = repr((count / population) * 10000)
            updated += 1

    # Years outside the cited source window are not touched by this script.
    with CSV_PATH.open("w", encoding="utf-8", newline="") as destination:
        writer = csv.DictWriter(destination, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)

    print(f"Atualizados {updated} registros de população/taxa de 2017–2021.")
    print(f"Fonte: {SOURCE_URL}")
    print("Os dados de 2022–2025 foram preservados sem alteração.")


if __name__ == "__main__":
    main()

