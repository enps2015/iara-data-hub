import importlib.util
import unittest
from pathlib import Path

import pandas as pd

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "sih_pilot_2023_01.py"
SPEC = importlib.util.spec_from_file_location("sih_pilot", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class SihPilotTests(unittest.TestCase):
    def setUp(self):
        self.frame = pd.DataFrame([
            {
                "MUNIC_RES": "150140", "MUNIC_MOV": "150140",
                "DT_INTER": "20230115", "DT_SAIDA": "20230120",
                "DIAG_PRINC": "A00.0", "N_AIH": "123",
                "IDENT": "1", "ANO_CMPT": "2023", "MES_CMPT": "01",
            },
            {
                "MUNIC_RES": "150080", "MUNIC_MOV": "150140",
                "DT_INTER": "202301", "DT_SAIDA": "202302",
                "DIAG_PRINC": "A09", "N_AIH": "124",
                "IDENT": "5", "ANO_CMPT": "2023", "MES_CMPT": "01",
            },
            {
                "MUNIC_RES": "150140", "MUNIC_MOV": "150140",
                "DT_INTER": "20230115", "DT_SAIDA": "20230120",
                "DIAG_PRINC": "A10", "N_AIH": "125",
                "IDENT": "1", "ANO_CMPT": "2023", "MES_CMPT": "01",
            },
            {
                "MUNIC_RES": "999999", "MUNIC_MOV": "150140",
                "DT_INTER": "20230115", "DT_SAIDA": "20230120",
                "DIAG_PRINC": "A01", "N_AIH": "126",
                "IDENT": "1", "ANO_CMPT": "2023", "MES_CMPT": "01",
            },
        ])

    def test_filters_resident_rmb_and_principal_cid_a00_a09(self):
        result = MODULE.filter_rmb_records(self.frame, "RDPA2301.dbc")
        self.assertEqual(len(result), 2)
        self.assertEqual(set(result["municipio"]), {"Belém", "Ananindeua"})
        self.assertTrue(result["uf_processamento"].eq("PA").all())

    def test_parses_both_supported_dt_inter_shapes(self):
        result = MODULE.filter_rmb_records(self.frame, "RDPA2301.dbc")
        self.assertTrue(result["ano_dt_inter"].astype("Int64").eq(2023).all())
        self.assertTrue(result["dt_inter_valida"].all())

    def test_recognizes_part_split_dbc_filename(self):
        result = MODULE.filter_rmb_records(self.frame, "RDPA2301_2.dbc")
        self.assertEqual(len(result), 2)
        self.assertTrue(result["uf_processamento"].eq("PA").all())

    def test_preserves_ident_without_excluding_any_type(self):
        result = MODULE.filter_rmb_records(self.frame, "RDPA2301.dbc")
        self.assertEqual(set(result["IDENT"].astype(str)), {"1", "5"})

    def test_aggregate_total_matches_selected_rows(self):
        result = MODULE.filter_rmb_records(self.frame, "RDPA2301.dbc")
        summary = MODULE.summarize_records(result)
        self.assertEqual(int(summary["registros_aih"].sum()), len(result))

    def test_repetition_report_contains_counts_not_aihs(self):
        result = MODULE.filter_rmb_records(self.frame, "RDPA2301.dbc")
        repeated = pd.concat([result, result.iloc[[0]]], ignore_index=True)
        report = MODULE.summarize_possible_repetitions(repeated)
        self.assertEqual(int(report["registros_em_chaves_repetidas"].sum()), 2)
        self.assertNotIn("N_AIH", report.columns)


if __name__ == "__main__":
    unittest.main()
