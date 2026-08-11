import hashlib
import importlib.util
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location("h2_endpoint", ROOT / "scripts/validation/validate_h2_endpoint_extension_preflight.py")
MOD = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MOD)


class TestH2EndpointExtension(unittest.TestCase):
    def test_scientific_bytes_are_identical(self):
        old = ROOT / "models/generated/mode_ii/reference_convergence/M2REF_H2_FRACFIX"
        new = ROOT / "models/generated/mode_ii/reference_convergence/M2REF_H2_FRACFIX_ENDPOINT"
        self.assertEqual(MOD.sha(old / "M2REF_H2_FRACFIX.inp"), MOD.sha(new / "M2REF_H2_FRACFIX_ENDPOINT.inp"))
        self.assertEqual(MOD.sha(old / "f42_mixed_uel.for"), MOD.sha(new / "f42_mixed_uel.for"))

    def test_preflight_passes_package_and_blocks_submission(self):
        import sys
        previous = sys.argv
        try:
            sys.argv = ["preflight"]
            self.assertEqual(MOD.main(), 2)
        finally:
            sys.argv = previous


if __name__ == "__main__":
    unittest.main()
