# -*- coding: utf-8 -*-
"""Unit tests for Task F1819: Documentation Correction for F1816/F1818 Records."""

import hashlib
import json
import os
import re
import unittest

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

FROZEN_UEL_SHA256 = "CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6"
FROZEN_FRAMEWORK_SHA256 = "4276A5DC1AF22A6A117102D8C24492789E8AA4EBFD4AF079C58EE86DBEEC7C8B"

F1818_RECEIPT_SHA256 = "E272152DB6462E14212FECF230DB9E8335D1BC33E327A5FD05D67E93B2A7627C"
F1818_TEST_FILE_SHA256 = "EC4FBB9440A1FD59C0DD754C412402D49485D212A0CB2DF12490512C74E1A9B2"


def _sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest().upper()


class TestF1819DocumentationCorrection(unittest.TestCase):
    """Verifies all Task F1819 documentation corrections and governance invariants."""

    def test_01_frozen_uel_and_framework(self):
        """Production UEL and shared framework must remain bitwise invariant."""
        uel_path = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "f42_mixed_uel.for")
        self.assertTrue(os.path.isfile(uel_path), "UEL file missing")
        self.assertEqual(_sha256(uel_path), FROZEN_UEL_SHA256)

        fw_path = os.path.join(REPO_ROOT, "scripts", "remeshing", "reusable_2d_adaptive_framework.py")
        self.assertTrue(os.path.isfile(fw_path), "Framework file missing")
        self.assertEqual(_sha256(fw_path), FROZEN_FRAMEWORK_SHA256)

    def test_02_f1816_report_section_4_1_synthesis_table(self):
        """F1816 report Section 4.1 table must have corrected header and WITHDRAWN (UNTESTED)."""
        report_path = os.path.join(REPO_ROOT, "docs", "validation", "F1816_MULTISTEP_REFINEMENT_NARROWING_REPORT.md")
        self.assertTrue(os.path.isfile(report_path), "F1816 report missing")

        with open(report_path, "r", encoding="utf-8") as f:
            content = f.read()

        # Header check
        self.assertIn("Step 1: Tight UNIFORM_ERROR (Min/Max Untested)", content)
        self.assertNotIn("Step 1: Min/Max Sizing", content)

        # Adoption decision row check
        self.assertIn("| Adoption Decision | **ADOPTED** | **WITHDRAWN (UNTESTED)** | **REJECTED** | **REJECTED** | **F1812 Stood** |", content)

    def test_03_f1818_report_section_2_1_remeshing_rule_snippet(self):
        """F1818 report Section 2.1 must quote the verbatim RemeshingRule constructor."""
        report_path = os.path.join(REPO_ROOT, "docs", "validation", "F1818_CORRECTION_AND_REASSESSMENT_REPORT.md")
        self.assertTrue(os.path.isfile(report_path), "F1818 report missing")

        with open(report_path, "r", encoding="utf-8") as f:
            content = f.read()

        # Must contain verbatim framework constructor keywords
        self.assertIn("m.RemeshingRule(", content)
        self.assertIn("stepName=step_target", content)
        self.assertIn("region=inst.sets['ALL_ELEM']", content)
        self.assertIn("sizingMethod=UNIFORM_ERROR", content)
        self.assertIn("errorTarget=config.error_target", content)
        self.assertIn("minElementSize=config.min_h", content)
        self.assertIn("maxElementSize=config.max_h", content)

        # Must NOT contain erroneous parameter names
        self.assertNotIn("endStep=step_name", content)
        self.assertNotIn("endFrame=frame_idx", content)
        self.assertNotIn("minSize=config.min_element_size_mm", content)
        self.assertNotIn("maxSize=config.max_element_size_mm", content)

    def test_04_f1818_report_section_7_artifact_table(self):
        """F1818 report Section 7 table must list verified receipt and test suite checksums."""
        report_path = os.path.join(REPO_ROOT, "docs", "validation", "F1818_CORRECTION_AND_REASSESSMENT_REPORT.md")
        with open(report_path, "r", encoding="utf-8") as f:
            content = f.read()

        # Receipt row
        self.assertIn(F1818_RECEIPT_SHA256, content)
        self.assertIn("5,339", content)

        # Test suite row
        self.assertIn(F1818_TEST_FILE_SHA256, content)
        self.assertIn("9,078", content)

        # No computed upon generation placeholders in section 7
        sec7_idx = content.find("## 7. Artifact & Publication Figure Manifest")
        sec8_idx = content.find("## 8. Governance, Invariants & Conclusion")
        self.assertGreater(sec7_idx, 0)
        self.assertGreater(sec8_idx, sec7_idx)
        sec7_text = content[sec7_idx:sec8_idx]
        self.assertNotIn("*computed upon generation*", sec7_text)

    def test_05_f1819_receipt_and_report_exist(self):
        """F1819 receipt and report must exist and have valid structure."""
        receipt_path = os.path.join(
            REPO_ROOT,
            "models",
            "pandey_kumar_mode1",
            "263_f1816_multistep_narrowing",
            "PK_F1819_DOCUMENTATION_CORRECTION_RECEIPT.json",
        )
        self.assertTrue(os.path.isfile(receipt_path), "F1819 receipt missing")

        with open(receipt_path, "r", encoding="utf-8") as f:
            receipt = json.load(f)

        self.assertEqual(receipt["task_id"], "F1819-DOCUMENTATION-CORRECTION")
        self.assertEqual(receipt["protocol"], "INDEPENDENT_STRUCTURED_REVIEW_V1")
        self.assertEqual(receipt["correlation_id"], "HND-F1819-DOCUMENTATION-CORRECTION-001")
        self.assertEqual(receipt["predecessor_correlation_id"], "HND-F1818-CORRECTION-REASSESSMENT-001")
        self.assertEqual(receipt["governing_objectives"]["cumulative_pbs_submissions"], 35)
        self.assertEqual(receipt["governing_objectives"]["new_pbs_submissions"], 0)
        self.assertEqual(receipt["governing_objectives"]["master_goal_status"], "OPEN")

        report_path = os.path.join(REPO_ROOT, "docs", "validation", "F1819_DOCUMENTATION_CORRECTION_REPORT.md")
        self.assertTrue(os.path.isfile(report_path), "F1819 report missing")

    def test_06_bridge_research_policy_includes_documentation_correction(self):
        """Bridge research policy must include documentation_correction in allowed_operations."""
        policy_path = os.path.join(REPO_ROOT, ".agents", "scripts", "bridge_research_policy.json")
        with open(policy_path, "r", encoding="utf-8-sig") as f:
            policy = json.load(f)
        self.assertIn("documentation_correction", policy["allowed_operations"])

    def test_07_governance_invariants(self):
        """Governance invariants must be preserved: 0 new PBS, 35 cumulative, master goal OPEN."""
        task_path = os.path.join(REPO_ROOT, "project_coordination", "ACTIVE_TASK.json")
        if os.path.isfile(task_path):
            with open(task_path, "r", encoding="utf-8") as f:
                task = json.load(f)
            self.assertEqual(task.get("master_goal_status"), "OPEN")
            self.assertEqual(task.get("cumulative_pbs_submissions"), 35)


if __name__ == "__main__":
    unittest.main()
