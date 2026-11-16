"""
Unit test for Task F1822: MINIMUM_MAXIMUM Control Verification and F1821 Record Correction.
Target Correlation ID: HND-F1822-MINMAX-CONTROL-VERIFICATION-001
"""

import hashlib
import json
import os
import re
import unittest

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))


def sha256_file(filepath):
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest().upper()


def compute_mesh_body_sha(filepath):
    """Compute SHA-256 of mesh body ignoring comment lines starting with **."""
    h = hashlib.sha256()
    with open(filepath, "r", encoding="utf-8", errors="replace") as f:
        for line in f:
            if line.startswith("**"):
                continue
            h.update(line.strip().encode("utf-8"))
            h.update(b"\n")
    return h.hexdigest().upper()


class TestF1822ControlVerification(unittest.TestCase):
    def test_control_mesh_properties(self):
        mesh_path = os.path.join(
            REPO_ROOT,
            "models",
            "pandey_kumar_mode1",
            "266_f1822_uniform_error_control",
            "PK_F1822_CASE1_UE3_CONTROL_PHYS.inp",
        )
        self.assertTrue(os.path.exists(mesh_path), f"Mesh not found: {mesh_path}")

        # Check file size
        file_size = os.path.getsize(mesh_path)
        self.assertEqual(file_size, 4480026)

        # Check body SHA
        body_sha = compute_mesh_body_sha(mesh_path)
        expected_body_sha = (
            "D36603D89FF9D953395A176D8C327F097FE69E92469FA73F6CC3193426B6E768"
        )
        self.assertEqual(
            body_sha,
            expected_body_sha,
            f"Body SHA mismatch: got {body_sha}, expected {expected_body_sha}",
        )

        # Count elements from INP
        elem_count = 0
        quad_count = 0
        tri_count = 0
        in_elements = False
        elem_type = None

        with open(mesh_path, "r", encoding="utf-8", errors="replace") as f:
            for line in f:
                line_s = line.strip()
                if re.match(r"^\*ELEMENT\s*,", line_s, re.IGNORECASE):
                    in_elements = True
                    m = re.search(r"TYPE=([A-Za-z0-9]+)", line_s, re.IGNORECASE)
                    elem_type = m.group(1).upper() if m else None
                    continue
                elif line_s.startswith("*") and in_elements:
                    in_elements = False
                    continue

                if in_elements and line_s:
                    parts = [p.strip() for p in line_s.split(",") if p.strip()]
                    if len(parts) >= 4:
                        elem_count += 1
                        if len(parts) == 5:
                            quad_count += 1
                        elif len(parts) == 4:
                            tri_count += 1

        self.assertEqual(elem_count, 62611)
        self.assertEqual(quad_count, 60966)
        self.assertEqual(tri_count, 1645)
        quad_fraction = 100.0 * quad_count / elem_count
        self.assertAlmostEqual(quad_fraction, 97.37, places=1)

    def test_control_rpy_journal(self):
        journal_path = os.path.join(
            REPO_ROOT,
            "models",
            "pandey_kumar_mode1",
            "266_f1822_uniform_error_control",
            "case_1_ue3_control_abaqus.rpy",
        )
        self.assertTrue(os.path.exists(journal_path))
        self.assertGreater(os.path.getsize(journal_path), 0)

        with open(journal_path, "r", encoding="utf-8", errors="replace") as f:
            content = f.read()

        self.assertIn("sizingMethod=UNIFORM_ERROR", content)
        self.assertIn("errorTarget=3.0%", content)
        self.assertIn("run_f1822_control_verification.py", content)

    def test_control_config(self):
        config_path = os.path.join(
            REPO_ROOT,
            "configs",
            "remeshing",
            "f1822_case1_uniform_error_3pct.json",
        )
        self.assertTrue(os.path.exists(config_path))
        file_sha = sha256_file(config_path)
        expected_sha = "09AAC074DE9E62075E0AF891DD9A20E7F91199946F53D926D0053D95E4C04D77"
        self.assertEqual(file_sha, expected_sha)

        with open(config_path, "r", encoding="utf-8") as f:
            cfg = json.load(f)

        self.assertEqual(cfg["remeshing_rule"]["sizing_method"], "UNIFORM_ERROR")
        self.assertEqual(cfg["remeshing_rule"]["error_target"], 3.0)

    def test_control_receipt_and_comparison(self):
        receipt_path = os.path.join(
            REPO_ROOT,
            "models",
            "pandey_kumar_mode1",
            "266_f1822_uniform_error_control",
            "PK_F1822_CONTROL_VERIFICATION_RECEIPT.json",
        )
        self.assertTrue(os.path.exists(receipt_path))

        with open(receipt_path, "r", encoding="utf-8") as f:
            rcpt = json.load(f)

        self.assertEqual(rcpt["task_id"], "F1822-MINIMUM-MAXIMUM-CONTROL-VERIFICATION")
        self.assertEqual(
            rcpt["correlation_id"], "HND-F1822-MINMAX-CONTROL-VERIFICATION-001"
        )
        self.assertEqual(rcpt["results"]["total_elements"], 62611)
        self.assertEqual(
            rcpt["results"]["physical_mesh_body_sha256"],
            "D36603D89FF9D953395A176D8C327F097FE69E92469FA73F6CC3193426B6E768",
        )

        cmp_data = rcpt["comparison_against_minmax"]
        self.assertFalse(cmp_data["shas_match"])
        self.assertEqual(cmp_data["element_delta"], 599)
        self.assertEqual(cmp_data["uniform_error_3pct"]["total_elements"], 62611)
        self.assertEqual(cmp_data["minimum_maximum_bias7"]["total_elements"], 63210)

    def test_f1821_receipt_has_correlation_id(self):
        f1821_rcpt_path = os.path.join(
            REPO_ROOT,
            "models",
            "pandey_kumar_mode1",
            "265_f1821_genuine_minmax",
            "PK_F1821_GENUINE_MINMAX_RECEIPT.json",
        )
        self.assertTrue(os.path.exists(f1821_rcpt_path))

        with open(f1821_rcpt_path, "r", encoding="utf-8") as f:
            rcpt = json.load(f)

        self.assertIn("correlation_id", rcpt)
        self.assertEqual(
            rcpt["correlation_id"], "HND-F1821-GENUINE-MINMAX-EXECUTION-001"
        )

    def test_f1821_report_table_corrected(self):
        f1821_rep_path = os.path.join(
            REPO_ROOT,
            "docs",
            "validation",
            "F1821_GENUINE_MINMAX_EXECUTION_REPORT.md",
        )
        self.assertTrue(os.path.exists(f1821_rep_path))

        with open(f1821_rep_path, "r", encoding="utf-8") as f:
            content = f.read()

        # Check that table lists 14,838 bytes and 1A30A82E...
        self.assertIn("14,838", content)
        self.assertIn(
            "1A30A82EECAFED41FCB4226DE5473C26FB86DC1EF7BACDC6F424E65CE3C6FF56", content
        )

    def test_governance_invariants(self):
        # Bitwise frozen UEL
        uel_path = os.path.join(
            REPO_ROOT, "models", "pandey_kumar_mode1", "f42_mixed_uel.for"
        )
        uel_sha = sha256_file(uel_path)
        expected_uel_sha = (
            "CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6"
        )
        self.assertEqual(
            uel_sha,
            expected_uel_sha,
            "Production UEL has mutated from bitwise frozen state!",
        )

        # Framework SHA
        fw_path = os.path.join(
            REPO_ROOT, "scripts", "remeshing", "reusable_2d_adaptive_framework.py"
        )
        fw_sha = sha256_file(fw_path)
        expected_fw_sha = (
            "0578156E5551173307892B8881E4BA772F099187BCF332672F39AC825023E80D"
        )
        self.assertEqual(
            fw_sha, expected_fw_sha, "Shared framework SHA has mutated unexpectedly!"
        )


if __name__ == "__main__":
    unittest.main()
