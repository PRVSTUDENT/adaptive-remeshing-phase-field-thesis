"""
Unit regression test suite for Mode-I reproduction package, manifest, and terminal ingestion guards.
"""
import unittest
import json
import hashlib
import re
from pathlib import Path

REPO_ROOT = Path(r"D:\Master thesis\Adaptive remeshing")
AUTHORITATIVE_FORTRAN_HASH = "CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6"
SUPERVISOR_MEETING_DATE = "Thursday, 08 October 2026, 10:00 CEST"


class TestMode1ReproductionPackageAndManifest(unittest.TestCase):
    """Test suite validating Mode-I reproduction package integrity, manifest, and governance rules."""

    def test_01_authoritative_fortran_source_hash_integrity(self):
        """Verify exact cryptographic SHA-256 hash of authoritative energy-instrumented f42_mixed_uel.for."""
        fortran_paths = [
            REPO_ROOT / "models" / "pandey_kumar_mode1" / "reproduction_package_gate6b_energy" / "f42_mixed_uel.for",
            REPO_ROOT / "models" / "pandey_kumar_mode1" / "25_stage14_adaptive_candidate_14k" / "f42_mixed_uel.for",
            REPO_ROOT / "models" / "pandey_kumar_mode1" / "34_stage14_step2_adaptive_candidate_et2_6k" / "f42_mixed_uel.for",
            REPO_ROOT / "models" / "pandey_kumar_mode1" / "35_stage14_step2_adaptive_candidate_et3_5k" / "f42_mixed_uel.for",
            REPO_ROOT / "models" / "pandey_kumar_mode1" / "36_stage14_step2_adaptive_candidate_et5_4k" / "f42_mixed_uel.for",
            REPO_ROOT / "models" / "pandey_kumar_mode1" / "30_stage14_adaptive_candidate_spatial_fine" / "f42_mixed_uel.for",
        ]
        for p in fortran_paths:
            self.assertTrue(p.exists(), f"Fortran source missing: {p}")
            content = p.read_bytes()
            h = hashlib.sha256(content).hexdigest().upper()
            self.assertEqual(
                h,
                AUTHORITATIVE_FORTRAN_HASH,
                f"Fortran SHA-256 mismatch in {p}! Expected {AUTHORITATIVE_FORTRAN_HASH}, got {h}"
            )

    def test_02_manifest_schema_and_artifact_integrity(self):
        """Validate MODE1_REPRODUCTION_MANIFEST.json schema, fields, and 100% artifact hash matches."""
        manifest_path = REPO_ROOT / "models" / "pandey_kumar_mode1" / "MODE1_REPRODUCTION_MANIFEST.json"
        self.assertTrue(manifest_path.exists(), "Manifest missing!")

        with open(manifest_path, "r", encoding="utf-8") as f:
            manifest = json.load(f)

        # Validate required root keys
        required_keys = [
            "manifest_version",
            "generated_timestamp",
            "active_scientific_phase",
            "next_supervisor_meeting",
            "authoritative_fortran_source_hash",
            "governing_parallel_verdict",
            "mpi_disqualification_status",
            "scientific_narrative_structure",
            "reproduction_artifacts"
        ]
        for key in required_keys:
            self.assertIn(key, manifest, f"Missing key in manifest: {key}")

        self.assertEqual(manifest["authoritative_fortran_source_hash"], AUTHORITATIVE_FORTRAN_HASH)
        self.assertEqual(manifest["mpi_disqualification_status"], "TRUE_MULTIRANK_MPI_NOT_QUALIFIED")
        self.assertEqual(
            manifest["governing_parallel_verdict"],
            "8THREAD_SHARED_MEMORY_EXECUTION_EMPIRICALLY_QUALIFIED_FOR_THE_TESTED_MODE1_FORMULATION_AND_CONTROLS"
        )

        # Validate each artifact
        artifacts = manifest["reproduction_artifacts"]
        self.assertGreaterEqual(len(artifacts), 30, f"Expected at least 30 artifacts, got {len(artifacts)}")

        for art in artifacts:
            for field in ["relative_path", "scientific_role", "sha256", "originating_task_job", "category_type", "required_environment", "expected_outputs"]:
                self.assertIn(field, art, f"Artifact missing field '{field}': {art}")

            rel_path = art["relative_path"]
            full_path = REPO_ROOT / rel_path
            self.assertTrue(full_path.exists(), f"Artifact file does not exist: {rel_path}")

            actual_hash = hashlib.sha256(full_path.read_bytes()).hexdigest().upper()
            self.assertEqual(
                actual_hash,
                art["sha256"],
                f"Hash mismatch for artifact {rel_path}! Expected {art['sha256']}, got {actual_hash}"
            )

    def test_03_guard_against_odb_dependency_in_reproduction_package(self):
        """Guard against requiring large binary ODB files for basic reproduction and evaluation."""
        manifest_path = REPO_ROOT / "models" / "pandey_kumar_mode1" / "MODE1_REPRODUCTION_MANIFEST.json"
        with open(manifest_path, "r", encoding="utf-8") as f:
            manifest = json.load(f)

        for art in manifest["reproduction_artifacts"]:
            rel = art["relative_path"].lower()
            self.assertFalse(
                rel.endswith(".odb") or rel.endswith(".res") or rel.endswith(".sim") or rel.endswith(".pac"),
                f"Prohibited heavy solver binary in reproduction manifest: {rel}"
            )

    def test_04_guard_against_multirank_mpi_for_original_uel(self):
        """Verify that commands.txt, templates, and methods documents disqualify multi-rank MPI."""
        commands_path = REPO_ROOT / "models" / "pandey_kumar_mode1" / "commands.txt"
        commands_text = commands_path.read_text(encoding="utf-8", errors="ignore")
        self.assertIn("TRUE_MULTIRANK_MPI_NOT_QUALIFIED", commands_text)
        self.assertIn("STRICTLY DISQUALIFIED", commands_text)
        self.assertIn("CB_STATE_TRANS", commands_text)

        pbs_template = REPO_ROOT / "scripts" / "hpc" / "templates" / "submit_mode1_8thread_scratch_template.pbs"
        pbs_text = pbs_template.read_text(encoding="utf-8", errors="ignore")
        self.assertTrue("exit 89" in pbs_text.lower(), "Must contain Exit 89 MPI/multi-node rejection guard")
        self.assertIn("nodes=1:ppn=8", pbs_text)

    def test_05_guard_against_forward_filling_in_evaluators(self):
        """Verify that terminal evaluators enforce NOT_REACHED and zero forward-filling."""
        eval_script = REPO_ROOT / "scripts" / "evaluation" / "evaluate_stage14_step2_errortarget_fracture_batch.py"
        eval_text = eval_script.read_text(encoding="utf-8", errors="ignore")
        self.assertIn("NOT_REACHED", eval_text)
        self.assertIn("ZERO FORWARD-FILLING", eval_text.upper())

    def test_06_guard_against_wext_mislabeling_as_fracture_or_internal_energy(self):
        """Guard against labeling external work W_ext as internal strain energy or fracture energy."""
        map_doc = REPO_ROOT / "models" / "pandey_kumar_mode1" / "reproduction_package_gate6b_energy" / "MODE1_ENERGY_EQUATION_CODE_OUTPUT_MAP.md"
        map_text = map_doc.read_text(encoding="utf-8", errors="ignore")
        self.assertTrue("W_{\\text{ext}}" in map_text or "W_ext" in map_text, "Must explicitly document external work W_ext")
        self.assertTrue("\\Delta_{\\text{book}}" in map_text or "Delta_book" in map_text, "Must explicitly document bookkeeping residual Delta_book")

        commands_path = REPO_ROOT / "models" / "pandey_kumar_mode1" / "commands.txt"
        commands_text = commands_path.read_text(encoding="utf-8", errors="ignore")
        self.assertIn("Delta_book = W_ext - (E_elas + E_frac)", commands_text)

    def test_07_guard_against_physical_element_terminology(self):
        """Verify that reproduction package files do NOT contain the forbidden phrase 'physical element'."""
        checked_files = [
            REPO_ROOT / "models" / "pandey_kumar_mode1" / "MODE1_REPRODUCTION_MANIFEST.json",
            REPO_ROOT / "models" / "pandey_kumar_mode1" / "commands.txt",
            REPO_ROOT / "docs" / "methods" / "TERMINAL_INGESTION_CHECKLIST.md",
            REPO_ROOT / "docs" / "methods" / "MODE1_GATE6B_CLOSURE_DECISION_MATRIX_AND_CONSISTENCY_AUDIT.md",
            REPO_ROOT / "docs" / "methods" / "MODE1_SHARED_MEMORY_8THREAD_PARITY_AND_SCALING_AUDIT.md"
        ]
        forbidden_regex = re.compile(r'\bphysical\s+elements?\b', re.IGNORECASE)
        for f in checked_files:
            if f.exists():
                text = f.read_text(encoding="utf-8", errors="ignore")
                matches = forbidden_regex.findall(text)
                self.assertEqual(
                    len(matches),
                    0,
                    f"Forbidden phrase 'physical element' found {len(matches)} times in {f.name}: {matches}"
                )

    def test_08_scientific_narrative_ordering_discipline(self):
        """Verify that manifest and checklist enforce logical scientific structure."""
        manifest_path = REPO_ROOT / "models" / "pandey_kumar_mode1" / "MODE1_REPRODUCTION_MANIFEST.json"
        with open(manifest_path, "r", encoding="utf-8") as f:
            manifest = json.load(f)

        structure = manifest.get("scientific_narrative_structure", "")
        self.assertEqual(structure, "problem -> expected_solution -> fixed_reference -> adaptive_method -> comparison -> discrepancies")

    def test_09_next_supervisor_meeting_date_consistency(self):
        """Verify that active documents consistently cite Thursday, 08 October 2026, 10:00 CEST."""
        active_docs = [
            REPO_ROOT / "models" / "pandey_kumar_mode1" / "MODE1_REPRODUCTION_MANIFEST.json",
            REPO_ROOT / "models" / "pandey_kumar_mode1" / "commands.txt",
            REPO_ROOT / "docs" / "methods" / "TERMINAL_INGESTION_CHECKLIST.md",
            REPO_ROOT / "project_coordination" / "CURRENT_STATE.md",
            REPO_ROOT / "docs" / "supervisor_reports" / "08-10-2026" / "MODE1_GATE6B_PROVEN_VS_PENDING_SUMMARY.md"
        ]
        for f in active_docs:
            self.assertTrue(f.exists(), f"Active doc missing: {f}")
            text = f.read_text(encoding="utf-8", errors="ignore")
            self.assertTrue(
                "08 October 2026" in text or "08-10-2026" in text or "08-October-2026" in text,
                f"Missing 08-October-2026 meeting date in {f.name}"
            )


if __name__ == '__main__':
    unittest.main(verbosity=2)
