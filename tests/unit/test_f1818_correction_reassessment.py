# -*- coding: utf-8 -*-
"""
tests/unit/test_f1818_correction_reassessment.py
================================================
Task F1818: Correction and Reassessment of F1816 Narrowing Conclusions.
Validates:
  1. Frozen UEL (CE8D5EDC...) and framework invariance (4276A5DC...)
  2. Step 2 summary JSON contains corrected Case 3 secondary corridor gate values (Var 2b 94.88% PASS, Var 2a 92.27% PASS) and zero Windows drive prefixes
  3. Direct recomputation of Case 3 secondary corridor gates from committed meshes confirms PASS (>= 90%)
  4. F1816 report honest provenance documentation (UNIFORM_ERROR errorTarget=3.0, MINIMUM_MAXIMUM untested)
  5. F1817 report run script hashes match committed file values
  6. Regenerated width comparison figures exist and match verified hashes
  7. F1818 receipt and report integrity
  8. Governance invariants (cumulative 35, 0 new PBS, MASTER_GOAL_STATUS = OPEN)
"""
import os
import sys
import json
import math
import hashlib
import unittest

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)
if os.path.join(REPO_ROOT, "scripts", "remeshing") not in sys.path:
    sys.path.insert(0, os.path.join(REPO_ROOT, "scripts", "remeshing"))

from reusable_2d_adaptive_framework import MeshQualityAuditEngine, py_sum

FROZEN_UEL_SHA = "CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6"
FROZEN_FRAMEWORK_SHA = "4276A5DC1AF22A6A117102D8C24492789E8AA4EBFD4AF079C58EE86DBEEC7C8B"

UEL_PATH = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "f42_mixed_uel.for")
FRAMEWORK_PATH = os.path.join(REPO_ROOT, "scripts", "remeshing", "reusable_2d_adaptive_framework.py")

BASE_NARROWING_DIR = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "263_f1816_multistep_narrowing")
STEP1_SUMMARY = os.path.join(BASE_NARROWING_DIR, "step1_minmax", "step1_minmax_summary.json")
STEP2_SUMMARY = os.path.join(BASE_NARROWING_DIR, "step2_envelope", "step2_envelope_summary.json")
RECEIPT_F1816 = os.path.join(BASE_NARROWING_DIR, "PK_F1816_MULTISTEP_NARROWING_RECEIPT.json")
RECEIPT_F1818 = os.path.join(BASE_NARROWING_DIR, "PK_F1818_CORRECTION_REASSESSMENT_RECEIPT.json")

REPORT_F1816 = os.path.join(REPO_ROOT, "docs", "validation", "F1816_MULTISTEP_REFINEMENT_NARROWING_REPORT.md")
REPORT_F1817 = os.path.join(REPO_ROOT, "docs", "validation", "F1817_EVIDENCE_COMPLETION_REPORT.md")
REPORT_F1818 = os.path.join(REPO_ROOT, "docs", "validation", "F1818_CORRECTION_AND_REASSESSMENT_REPORT.md")

FIG_PNG = os.path.join(REPO_ROOT, "results", "figures", "fig_f1816_refinement_width_comparison.png")
FIG_PDF = os.path.join(REPO_ROOT, "results", "figures", "fig_f1816_refinement_width_comparison.pdf")


def sha256_file(filepath):
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while True:
            chunk = f.read(65536)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest().upper()


class TestF1818CorrectionReassessment(unittest.TestCase):

    def test_01_frozen_uel_and_framework(self):
        self.assertTrue(os.path.exists(UEL_PATH), "UEL file must exist")
        self.assertEqual(sha256_file(UEL_PATH), FROZEN_UEL_SHA, "Production UEL must be bitwise frozen")
        self.assertTrue(os.path.exists(FRAMEWORK_PATH), "Framework file must exist")
        self.assertEqual(sha256_file(FRAMEWORK_PATH), FROZEN_FRAMEWORK_SHA,
                         "Shared framework must remain bitwise invariant at 4276A5DC...")

    def test_02_step2_summary_case3_secondary_gates(self):
        self.assertTrue(os.path.exists(STEP2_SUMMARY), "Step 2 summary must exist")
        with open(STEP2_SUMMARY, "r", encoding="utf-8") as f:
            raw = f.read()
            d2 = json.loads(raw)
        self.assertNotIn("D:\\", raw, "Step 2 summary must contain zero Windows absolute drive prefixes")
        
        # Var 2b Case 3 gate
        g2b = d2["variant_2b_reduced"]["case_3"]["scientific_gate"]
        self.assertTrue(g2b["pass"], "Variant 2b Case 3 must be PASS")
        self.assertAlmostEqual(g2b["val"], 94.88, places=1, msg="Variant 2b Case 3 coverage must be ~94.88%")
        
        # Var 2a Case 3 gate
        g2a = d2["variant_2a_overlapping"]["case_3"]["scientific_gate"]
        self.assertTrue(g2a["pass"], "Variant 2a Case 3 must be PASS")
        self.assertAlmostEqual(g2a["val"], 92.27, places=1, msg="Variant 2a Case 3 coverage must be ~92.27%")

    def test_03_mesh_independent_gate_recomputation(self):
        l0 = 0.285
        mesh_paths = {
            "v2b": os.path.join(BASE_NARROWING_DIR, "step2_envelope", "variant_2b_reduced", "PK_F1816_V2B_CASE_3_PHYS.inp"),
            "v2a": os.path.join(BASE_NARROWING_DIR, "step2_envelope", "variant_2a_overlapping", "PK_F1816_V2A_CASE_3_PHYS.inp")
        }
        
        for key, p in mesh_paths.items():
            self.assertTrue(os.path.exists(p), "Mesh file must exist: %s" % p)
            nodes, quads, tris = MeshQualityAuditEngine.parse_physical_inp(p)
            all_elems = list(quads.items()) + list(tris.items())
            sec_elems = []
            for eid, conn in all_elems:
                pts = [nodes[nid] for nid in conn]
                cx = py_sum(pt[0] for pt in pts) / len(pts)
                cy = py_sum(pt[1] for pt in pts) / len(pts)
                if 36.5 <= cx <= 65.0 and 45.0 <= cy <= 65.0:
                    n = len(pts)
                    area = 0.5 * abs(py_sum(pts[i][0] * pts[(i+1)%n][1] - pts[(i+1)%n][0] * pts[i][1] for i in range(n)))
                    sec_elems.append(math.sqrt(area))
            
            n_tot = len(sec_elems)
            n_fine = py_sum(1 for h in sec_elems if h <= l0 + 1e-9)
            cov = float(n_fine) / n_tot * 100.0
            
            self.assertGreaterEqual(cov, 90.0, "%s secondary corridor coverage must pass >= 90%%: got %.2f%%" % (key, cov))
            if key == "v2b":
                self.assertEqual(n_tot, 12964)
                self.assertEqual(n_fine, 12300)
            elif key == "v2a":
                self.assertEqual(n_tot, 11440)
                self.assertEqual(n_fine, 10556)

    def test_04_f1816_report_correction_content(self):
        self.assertTrue(os.path.exists(REPORT_F1816), "F1816 report must exist")
        with open(REPORT_F1816, "r", encoding="utf-8") as f:
            content = f.read()
        self.assertIn("sizingMethod=UNIFORM_ERROR", content)
        self.assertIn("errorTarget=3.0%", content)
        self.assertIn("MINIMUM_MAXIMUM sizing was never actually exercised", content)
        self.assertIn("94.88%", content)
        self.assertIn("92.27%", content)

    def test_05_f1817_report_run_script_hashes(self):
        self.assertTrue(os.path.exists(REPORT_F1817), "F1817 report must exist")
        with open(REPORT_F1817, "r", encoding="utf-8") as f:
            content = f.read()
        self.assertIn("0F33EFEBD4302D8FD1D6A7FC1E78CCC352AD187968D84082BFD91B4599D3FB53", content)
        self.assertIn("3,557", content)
        self.assertIn("3B9253DF21A65FD13694EC3FA9C88A9C91EB73AD6AFDA519122A38F439B10229", content)
        self.assertIn("15,552", content)
        self.assertIn("931E683CC4DF47C99CEB3AD33F97022A2E843606A76978DAD229A9D27C83AAC2", content)
        self.assertIn("15,835", content)
        self.assertIn("95D6207C89410EB6B3D3CBC88C52F7CF112398D7DCBF8FDF99FBBD15A48D46DA", content)
        self.assertIn("6,032", content)

    def test_06_regenerated_figures_and_hashes(self):
        self.assertTrue(os.path.exists(FIG_PNG), "Width figure PNG must exist")
        self.assertTrue(os.path.exists(FIG_PDF), "Width figure PDF must exist")
        self.assertEqual(sha256_file(FIG_PNG), "302906A7468BFD68514F61084A52F712CC72F1B681A93F0242CEF7A9BBD31802")
        self.assertEqual(sha256_file(FIG_PDF), "FB62BF7DD39DE330664B1913C7C0154291F238DEB5C893F1C40834E1F8007874")
        self.assertEqual(os.path.getsize(FIG_PNG), 787457)
        self.assertEqual(os.path.getsize(FIG_PDF), 67728)

    def test_07_f1818_receipt_and_report_exist(self):
        self.assertTrue(os.path.exists(REPORT_F1818), "F1818 report must exist")
        self.assertTrue(os.path.exists(RECEIPT_F1818), "F1818 receipt must exist")
        with open(RECEIPT_F1818, "r", encoding="utf-8") as f:
            rcpt = json.load(f)
        self.assertEqual(rcpt["task_id"], "F1818-CORRECTION-AND-REASSESSMENT")
        self.assertEqual(rcpt["correlation_id"], "HND-F1818-CORRECTION-REASSESSMENT-001")

    def test_08_governance_invariants(self):
        with open(RECEIPT_F1818, "r", encoding="utf-8") as f:
            rcpt = json.load(f)
        gov = rcpt["governing_objectives"]
        self.assertEqual(gov["cumulative_pbs_submissions"], 35)
        self.assertEqual(gov["new_pbs_submissions"], 0)
        self.assertEqual(gov["master_goal_status"], "OPEN")
        self.assertEqual(gov["frozen_production_uel_sha256"], FROZEN_UEL_SHA)
        self.assertEqual(gov["shared_framework_sha256"], FROZEN_FRAMEWORK_SHA)


if __name__ == "__main__":
    unittest.main()
