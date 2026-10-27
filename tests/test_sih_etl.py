import sys
import unittest
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.build_iara_municipios_rmb import select_sih_admissions


class SelectSihAdmissionsTests(unittest.TestCase):
    def test_selects_only_principal_diagnoses_A00_to_A09(self):
        frame = pd.DataFrame({
            "MUNIC_RES": [150080, 150080, 150140, 150140, 150150, 150150],
            "DT_INTER": ["20230105", "20230212", "20230303", "20230421", "20230506", "20230617"],
            "DIAG_PRINC": ["A00", "a05.1", "A09", "A10", "B99", "A04.0"],
            "N_AIH": ["AIH-1", "AIH-2", "AIH-3", "AIH-4", "AIH-5", "AIH-6"],
        })
        seen = set()

        selected = select_sih_admissions(frame, "fixture.csv", seen)

        self.assertEqual(len(selected), 4)
        self.assertEqual(set(selected["DIAG_PRINC"].str.strip().str.upper()), {"A00", "A05.1", "A09", "A04.0"})
        self.assertEqual(set(selected["ano"]), {2023})
        self.assertEqual(set(selected["MUNIC_RES"]), {150080, 150140, 150150})
        self.assertEqual(len(seen), 4)

    def test_fails_when_a_target_admission_has_invalid_date(self):
        frame = pd.DataFrame({
            "MUNIC_RES": [150080],
            "DT_INTER": ["2023-01-05"],
            "DIAG_PRINC": ["A00"],
        })
        with self.assertRaisesRegex(ValueError, "DT_INTER"):
            select_sih_admissions(frame, "invalid-date.csv")

    def test_fails_when_a_target_admission_has_invalid_residence_code(self):
        frame = pd.DataFrame({
            "MUNIC_RES": ["not-a-code"],
            "DT_INTER": ["20230105"],
            "DIAG_PRINC": ["A00"],
        })
        with self.assertRaisesRegex(ValueError, "MUNIC_RES"):
            select_sih_admissions(frame, "invalid-residence.csv")

    def test_fails_when_required_columns_are_missing(self):
        frame = pd.DataFrame({
            "MUNIC_RES": [150080],
            "DIAG_PRINC": ["A00"],
        })
        with self.assertRaisesRegex(ValueError, "DT_INTER"):
            select_sih_admissions(frame, "missing-column.csv")

    def test_fails_when_an_admission_id_overlaps_source_files(self):
        frame = pd.DataFrame({
            "MUNIC_RES": [150080],
            "DT_INTER": ["20230105"],
            "DIAG_PRINC": ["A00"],
            "N_AIH": ["AIH-DUP"],
        })
        seen = {"AIH-DUP"}
        with self.assertRaisesRegex(ValueError, "duplicadas"):
            select_sih_admissions(frame, "overlap.csv", seen)


if __name__ == "__main__":
    unittest.main()
