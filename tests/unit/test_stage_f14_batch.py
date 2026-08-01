import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

class StageF14Tests(unittest.TestCase):
    def test_runtime_source_contract(self):
        text = (ROOT / "models/generated/mode_ii/f14_runtime_load_smoke/M2RTLOAD1.for").read_text()
        self.assertNotIn("GET_ENVIRONMENT_VARIABLE", text.upper())
        self.assertNotIn("for_getenv_err", text)
        self.assertIn("CALL GETOUTDIR(F14OUT,F14LO)", text)
        self.assertIn("CALL GETJOBNAME(F14JOB,F14LJ)", text)
        self.assertNotIn("WRITE(99", text.upper())
        self.assertNotIn("PNEWDT=", text.upper())
        self.assertIn("JELEM.EQ.1.AND.INPT.EQ.1", text)

    def test_runtime_deck_mapping(self):
        text = (ROOT / "models/generated/mode_ii/f14_runtime_load_smoke/M2RTLOAD1.inp").read_text()
        self.assertIn("*Step, name=RUNTIME_LOAD_SMOKE", text)
        self.assertNotIn("UNLOAD_RELOAD", text)
        self.assertIn("69, 27, 28, 35, 34", text)

    def test_region_lane_is_nonexecuting(self):
        text = (ROOT / "scripts/remeshing/qualify_stage_f14_adaptive_region.py").read_text()
        self.assertNotIn(".adaptiveRemesh(", text)
        self.assertNotIn(".submit(", text)
        self.assertIn('"ale_adaptive_mesh_used": False', text)
        self.assertIn("RemeshingRule", text)

    def test_manifests_are_valid(self):
        for rel in ("models/generated/mode_ii/f14_runtime_load_smoke/PACKAGE_MANIFEST.json",
                    "models/generated/mode_ii/f14_native_miseseri_adaptive_region/PACKAGE_MANIFEST.json"):
            json.loads((ROOT / rel).read_text())

if __name__ == "__main__":
    unittest.main()
