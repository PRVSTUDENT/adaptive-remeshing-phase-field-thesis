import importlib.util
import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[2]


def load(name, relative):
    spec = importlib.util.spec_from_file_location(name, ROOT / relative)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


remesh = load("f5_remesh", "scripts/remeshing/create_mode_ii_native_miseseri_remesh.py")
integrity = load("f5_integrity", "scripts/validation/validate_mode_ii_refined_deck_integrity.py")


class TestF5Readiness(unittest.TestCase):
    def setUp(self):
        self.config_path = ROOT / "configs/stage_f/mode_ii_miseseri_native_remesh.yaml"

    def test_config_parses_and_baseline_is_exact(self):
        config = remesh.load_config(str(self.config_path))
        self.assertEqual(config["publication_faithful_baseline"]["errorTarget"], 1.0)
        self.assertEqual(config["publication_faithful_baseline"]["refinementFactor"], 10)

    def test_dry_run_never_executes(self):
        result = remesh.audit(remesh.load_config(str(self.config_path)))
        self.assertFalse(result["native_remesh_executed"])
        self.assertEqual(result["solver_execution_count"], 0)

    def test_source_odb_hash_is_pinned(self):
        config = remesh.load_config(str(self.config_path))
        self.assertEqual(config["source"]["odb_sha256"],
                         "bfcdbec08669774a9f80939d67c9c86ffe7df707e760450b08b1f6073fc588ac")

    def test_smoke_manifest_hashes_are_exact(self):
        manifest = json.loads((ROOT / "models/generated/mode_ii/h2_u020_compiler_datacheck_smoke/PACKAGE_MANIFEST.json").read_text())
        self.assertEqual(manifest["deck"]["sha256"],
                         "fdcd6ee1b1d6cbfb88d59a3edfb7f1c6b35cecde736a427f6b3030b0443b10bf")
        self.assertEqual(manifest["fortran"]["sha256"],
                         "49c9054ab5faec9e069e0a9149af5058e6f1e11ab164c2a0e318f60282309b37")

    def test_no_automatic_full_job_submission(self):
        script = (ROOT / "scripts/hpc/stage_f/07_mode_ii_h2_compiler_datacheck_smoke.pbs").read_text()
        self.assertIn("datacheck interactive", script)
        self.assertNotIn("qsub ", script)
        self.assertNotIn("analysis", script.lower().split("abaqus job=", 1)[-1])

    def test_compiler_classifications_present(self):
        script = (ROOT / "scripts/hpc/stage_f/07_mode_ii_h2_compiler_datacheck_smoke.pbs").read_text()
        for name in ("compiler_environment_missing", "compiler_detected",
                     "compilation_failed", "link_failed", "datacheck_failed", "datacheck_pass"):
            self.assertIn(name, script)

    def test_integrity_detects_duplicate_nodes(self):
        deck = "*Node\n1,0,0\n1,1,0\n*Element, type=CPE4, elset=All_elem\n1,1,1,1,1\n"
        self.assertFalse(integrity.validate_text(deck)["checks"]["no_duplicate_node_labels"])

    def test_integrity_accepts_required_static_markers(self):
        deck = """*Node
1,0,0
2,1,0
3,1,1
4,0,1
*Element, type=CPE4, elset=All_elem
1,1,2,3,4
*Element, type=U1, elset=umatelem
2,1,2,3,4
*UEL Property, elset=umatelem
1.
*Solid Section, elset=All_elem, material=m
*Boundary
1,1,2
*Equation
2
1,1,1.,2,1,-1.
*Output, field
*Node Output
U
"""
        checks = integrity.validate_text(deck)["checks"]
        for key in ("required_all_elem", "required_umatelem", "sections_present",
                    "boundary_conditions_present", "rp_equations_present",
                    "plane_strain_elements_present", "uel_elements_present",
                    "uel_properties_present", "output_requests_present"):
            self.assertTrue(checks[key], key)


if __name__ == "__main__":
    unittest.main()
