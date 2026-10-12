"""
Unit Test Suite for Mode-I Method C Gate C1 Telemetry Extractor
Task F1424: Method C Gate C1 Post-Processing & Telemetry Extraction Qualification
Protocol Version: 2
"""

import sys
from pathlib import Path
import tempfile
import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.postprocessing.extract_mode1_c1_results import (
    parse_sta_file,
    parse_dat_file,
    parse_energy_csv,
)

EVIDENCE_1412158_DIR = REPO_ROOT / "models" / "pandey_kumar_mode1" / "39_method_c_transfer_gate_c1" / "evidence_1412158"
STA_PATH = EVIDENCE_1412158_DIR / "M1_RECIP_2906_CONTINUATION.sta"


class TestMode1C1Extractor:
    def test_01_parse_sta_file_real_evidence(self):
        """Verify that parse_sta_file correctly parses the 5,010 increments from Job 1412158 evidence."""
        assert STA_PATH.exists(), f"Evidence .sta file not found at {STA_PATH}"
        summary = parse_sta_file(STA_PATH)

        assert summary["status"] == "PARSED"
        assert summary["total_increments"] == 5010
        assert summary["step1_increments"] == 10
        assert summary["step2_increments"] == 5000
        assert summary["cutbacks"] == 0
        assert summary["severe_discontinuities"] == 0
        assert summary["final_step"] == 2
        assert summary["final_time"] == 2.0

    def test_02_parse_dat_file_synthetic(self, tmp_path):
        """Verify that parse_dat_file extracts RP reaction forces and displacements across steps."""
        dat_content = """
                    S T E P       1     C A L C U L A T I O N

   INCREMENT     1 SUMMARY
       NODE FOOT-   U2          RF2
            NOTE
     999999       5.0000E-04  6.5309E-02

   INCREMENT    10 SUMMARY
       NODE FOOT-   U2          RF2
            NOTE
     999999       5.0000E-03  6.5309E-01

                    S T E P       2     C A L C U L A T I O N

   INCREMENT     1 SUMMARY
       NODE FOOT-   U2          RF2
            NOTE
     999999       5.0010E-03  6.5312E-01
"""
        dat_file = tmp_path / "test.dat"
        dat_file.write_text(dat_content, encoding="utf-8")

        records = parse_dat_file(dat_file)
        assert len(records) == 3

        assert records[0]["step"] == 1
        assert pytest.approx(records[0]["u2_mm"], 1e-6) == 5.0e-4
        assert pytest.approx(records[0]["rf2_kn"], 1e-6) == 0.065309

        assert records[1]["step"] == 1
        assert pytest.approx(records[1]["u2_mm"], 1e-6) == 0.0050
        assert pytest.approx(records[1]["rf2_kn"], 1e-6) == 0.65309

        assert records[2]["step"] == 2
        assert pytest.approx(records[2]["u2_mm"], 1e-6) == 0.005001
        assert pytest.approx(records[2]["rf2_kn"], 1e-6) == 0.65312

    def test_03_parse_energy_csv_synthetic(self, tmp_path):
        """Verify that parse_energy_csv correctly parses UEL energy components."""
        csv_content = """step,increment,total_time,step_time,e_elastic,e_fracture,e_total
1,1,0.1,0.1,1.0e-3,7.5e-6,1.0075e-3
1,10,1.0,1.0,1.6e-3,7.5e-6,1.6075e-3
2,5000,2.0,1.0,1.0e-5,3.0e-3,3.0100e-3
"""
        csv_file = tmp_path / "energy.csv"
        csv_file.write_text(csv_content, encoding="utf-8")

        records = parse_energy_csv(csv_file)
        assert len(records) == 3
        assert records[0]["step"] == 1
        assert records[0]["increment"] == 1
        assert pytest.approx(records[1]["e_elastic_knmm"], 1e-6) == 1.6e-3
        assert pytest.approx(records[1]["e_fracture_knmm"], 1e-6) == 7.5e-6
        assert pytest.approx(records[2]["e_fracture_knmm"], 1e-6) == 3.0e-3

    def test_04_missing_file_handling(self, tmp_path):
        """Verify that missing files are handled safely without crashing."""
        missing = tmp_path / "nonexistent.sta"
        res = parse_sta_file(missing)
        assert res["status"] == "MISSING"

        dat_res = parse_dat_file(tmp_path / "nonexistent.dat")
        assert dat_res == []

        csv_res = parse_energy_csv(tmp_path / "nonexistent.csv")
        assert csv_res == []
