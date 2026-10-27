#!/usr/bin/env python3
"""Reconcile annual municipal population and derived rates for the IARA CSV.

Source treatment:
- 2017–2021: annual estimates published by FAPESPA/IBGE.
- 2022: current IBGE Censo Demográfico 2022 values.
- 2023: repeats 2022 census values because FAPESPA notes that IBGE did not
  calculate municipal estimates for 2023. These are carried-forward references,
  not independent estimates for 2023.
- 2024: IBGE estimates reported by FAPESPA.
- 2025: IBGE estimate table POP2025_20260828.pdf, reference date 1 July 2025.

Only population and its derived admission rate are updated. Admission counts,
sanitation indicators, climate indicators, and their missing cells are untouched.
"""
import csv
from pathlib import Path

CSV_PATH = Path(__file__).resolve().parents[1] / "data" / "iara" / "iara_municipios_rmb.csv"

# FAPESPA/IBGE annual estimates for 2017–2021.
# https://www.fapespa.pa.gov.br/sistemas/anuario2021/tabelas/demografia/tab-1.1-populacao-total-e-estimativas-populacionais-2017-a-2021.htm
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
    # Current IBGE Cidades e Estados pages, Censo Demográfico 2022.
    2022: {
        "Ananindeua (PA)": 478778, "Belém (PA)": 1303403,
        "Benevides (PA)": 63567, "Castanhal (PA)": 192256,
        "Marituba (PA)": 111785, "Santa Bárbara do Pará (PA)": 21087,
        "Santa Izabel do Pará (PA)": 73019,
    },
    # FAPESPA notes 2022 values were repeated for 2023 because IBGE did not
    # calculate municipal estimates for that year.
    # https://www.fapespa.pa.gov.br/sistemas/anuario2024/tabelas/demografia/tab-1.1-populacao-total-estimativas-populacionais-e-censo-deografico-2020-a-2024.htm
    2023: {
        "Ananindeua (PA)": 478778, "Belém (PA)": 1303403,
        "Benevides (PA)": 63567, "Castanhal (PA)": 192256,
        "Marituba (PA)": 111785, "Santa Bárbara do Pará (PA)": 21087,
        "Santa Izabel do Pará (PA)": 73019,
    },
    # FAPESPA/IBGE estimates, reference date 1 July 2024.
    # https://www.fapespa.pa.gov.br/sistemas/anuario2024/tabelas/demografia/tab-1.1-populacao-total-estimativas-populacionais-e-censo-deografico-2020-a-2024.htm
    2024: {
        "Ananindeua (PA)": 507838, "Belém (PA)": 1398531,
        "Benevides (PA)": 68191, "Castanhal (PA)": 207603,
        "Marituba (PA)": 118998, "Santa Bárbara do Pará (PA)": 22288,
        "Santa Izabel do Pará (PA)": 78317,
    },
    # IBGE POP2025_20260828.pdf, reference date 1 July 2025.
    # https://ftp.ibge.gov.br/Estimativas_de_Populacao/Estimativas_2025/POP2025_20260828.pdf
    2025: {
        "Ananindeua (PA)": 509227, "Belém (PA)": 1397315,
        "Benevides (PA)": 68962, "Castanhal (PA)": 209126,
        "Marituba (PA)": 119437, "Santa Bárbara do Pará (PA)": 22530,
        "Santa Izabel do Pará (PA)": 79195,
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

    keys = [(row["municipio"], int(row["ano"])) for row in rows]
    if len(keys) != len(set(keys)):
        raise ValueError("CSV tem chaves município/ano duplicadas.")

    expected_keys = {
        (municipality, year)
        for year, population_map in POPULATION_BY_YEAR.items()
        for municipality in population_map
    }
    if not expected_keys.issubset(set(keys)):
        raise ValueError(f"Registros município/ano ausentes: {sorted(expected_keys - set(keys))}")

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

    with CSV_PATH.open("w", encoding="utf-8", newline="") as destination:
        writer = csv.DictWriter(destination, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)

    print(f"Atualizados {updated} registros de população/taxa de 2017–2025.")
    print("Nota: população de 2023 repete os valores de 2022, conforme nota da FAPESPA.")
    print("Contagens de internações, saneamento, clima e ausências permanecem intocados.")


if __name__ == "__main__":
    main()
