# -*- coding: utf-8 -*-
"""
tests/unit/test_f1817_evidence_completion.py
============================================
Task F1817: Evidence Completion for F1816 Multi-Step Narrowing.
Validates:
  1. Bitwise frozen UEL (CE8D5EDC...) and framework invariance (4276A5DC...)
  2. All 12 Step 1 and Step 2 variant meshes exist and match whole-file and body SHA-256
  3. All 6 donor ODB files exist and match exact SHA-256 hashes
  4. Step 2 envelope summary JSON contains strictly repo-relative paths (zero Windows absolute paths)
  5. F1816 report section 2.1 framework explanation and artifact table actual hashes
  6. Existence and integrity of run scripts for Step 1 and Step 2
  7. Element counts and gate values of all 12 variant meshes
  8. Master receipt and governance invariants (cumulative 35, 0 new PBS, MASTER_GOAL_STATUS = OPEN)
"""
import os
import sys
import json
import hashlib
import unittest

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

FROZEN_UEL_SHA = "CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6"
FROZEN_FRAMEWORK_SHA = "4276A5DC1AF22A6A117102D8C24492789E8AA4EBFD4AF079C58EE86DBEEC7C8B"

UEL_PATH = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "f42_mixed_uel.for")
FRAMEWORK_PATH = os.path.join(REPO_ROOT, "scripts", "remeshing", "reusable_2d_adaptive_framework.py")

BASE_NARROWING_DIR = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "263_f1816_multistep_narrowing")
STEP1_SUMMARY = os.path.join(BASE_NARROWING_DIR, "step1_minmax", "step1_minmax_summary.json")
STEP2_SUMMARY = os.path.join(BASE_NARROWING_DIR, "step2_envelope", "step2_envelope_summary.json")
RECEIPT_PATH = os.path.join(BASE_NARROWING_DIR, "PK_F1816_MULTISTEP_NARROWING_RECEIPT.json")

F1816_REPORT = os.path.join(REPO_ROOT, "docs", "validation", "F1816_MULTISTEP_REFINEMENT_NARROWING_REPORT.md")


def sha256_file(filepath):
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while True:
            chunk = f.read(65536)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest().upper()


def sha256_body(filepath):
    h = hashlib.sha256()
    with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
        for line in f:
            if line.startswith("**"):
                continue
            h.update(line.strip().encode("utf-8"))
            h.update(b"\n")
    return h.hexdigest().upper()


class TestF1817EvidenceCompletion(unittest.TestCase):

    def test_01_frozen_uel_and_framework(self):
        self.assertTrue(os.path.exists(UEL_PATH), "UEL file must exist")
        self.assertEqual(sha256_file(UEL_PATH), FROZEN_UEL_SHA, "Production UEL must be bitwise frozen")
        self.assertTrue(os.path.exists(FRAMEWORK_PATH), "Framework file must exist")
        self.assertEqual(sha256_file(FRAMEWORK_PATH), FROZEN_FRAMEWORK_SHA,
                         "Shared framework must remain bitwise invariant at 4276A5DC...")

    def test_02_twelve_variant_meshes_exist_and_hashes(self):
        expected_meshes = {
            # Step 1
            "PK_F1816_STEP1_CASE_1_ADAPT_PHYS.inp": {
                "dir": os.path.join(BASE_NARROWING_DIR, "step1_minmax"),
                "sha": "7D18F3298C3B3ECE3F2FAC0A5166C3E23736D9C9AC7780FF6020883DB4000A49",
                "body": "B15F948C820F7A773D61D62651638800ED525ABC3E538412A383E8E36AD6DB9E",
                "size": 4519502
            },
            "PK_F1816_STEP1_CASE_2_ADAPT_PHYS.inp": {
                "dir": os.path.join(BASE_NARROWING_DIR, "step1_minmax"),
                "sha": "E9F0F32F318E074591C182EA4A6B5600AD87263C6F730283DAAB8B9C410C91AF",
                "body": "1768934BC090C404F00078EB112A92C52644E307AC28E3008B9CFEDA2B0A6465",
                "size": 4034482
            },
            "PK_F1816_STEP1_CASE_3_ADAPT_PHYS.inp": {
                "dir": os.path.join(BASE_NARROWING_DIR, "step1_minmax"),
                "sha": "04983203F55473F34D87493B6F7E6D0C94B297DC5C725EF754C2EFACE1442934",
                "body": "86E5417268FFA9E3DF721D9E40EDCE4A424D72AED4C920A30BA340BC3E734290",
                "size": 6285686
            },
            "PK_F1816_STEP1_CASE_5_ADAPT_PHYS.inp": {
                "dir": os.path.join(BASE_NARROWING_DIR, "step1_minmax"),
                "sha": "853BFC7376192FDC46264A0847B6A7776EE0D4629CFC6A5D242F43913BA1AAD1",
                "body": "2EB19443F845B1B0B08DD4F1E81A60BAE609E2A2A36004C96D8759CE406EB2D9",
                "size": 3725763
            },
            # Variant 2b
            "PK_F1816_V2B_CASE_1_PHYS.inp": {
                "dir": os.path.join(BASE_NARROWING_DIR, "step2_envelope", "variant_2b_reduced"),
                "sha": "CEC9C937CD89F66FE4423F1D52E3AD9336AD8C69486D07B7DD53F59417DFEC89",
                "body": "6C7D199C1A18FC0E71E60809BF3BB4DD654778FA4CBD783BFD13659261B2EA4D",
                "size": 2102583
            },
            "PK_F1816_V2B_CASE_2_PHYS.inp": {
                "dir": os.path.join(BASE_NARROWING_DIR, "step2_envelope", "variant_2b_reduced"),
                "sha": "C7B4C9F181E6EF6F31DAFC2F0349C03C7CDECEC21E3F729E0B87A5AD8926F6AC",
                "body": "489D79A2BC8D6735221EB56F0D5C8343FE9C2E7DA33B754DA63A6EA1D535638B",
                "size": 6014582
            },
            "PK_F1816_V2B_CASE_3_PHYS.inp": {
                "dir": os.path.join(BASE_NARROWING_DIR, "step2_envelope", "variant_2b_reduced"),
                "sha": "904C035C46D032B2A1440F7E4747BB65ED0B17AC4518588F465706C31201570A",
                "body": "E40C18A29C9F9A9872B8C24F51FF63050C629EA0C000F6E7E4081418D75E76CE",
                "size": 3698489
            },
            "PK_F1816_V2B_CASE_5_PHYS.inp": {
                "dir": os.path.join(BASE_NARROWING_DIR, "step2_envelope", "variant_2b_reduced"),
                "sha": "51407589C145B3AC8E8BB5CA36D16A35CD214126D55C586FF4EDAA73C858DAC4",
                "body": "78009AAEE4FE732C0FA56F2DE5487C1717E82E245B4CAF32C3B9CE19AB2B4065",
                "size": 1127966
            },
            # Variant 2a
            "PK_F1816_V2A_CASE_1_PHYS.inp": {
                "dir": os.path.join(BASE_NARROWING_DIR, "step2_envelope", "variant_2a_overlapping"),
                "sha": "24281F8D7BF7D0FF393A37EBEF447521279C547F0AE00A3ED7B01E8AED757F17",
                "body": "508AB2A66248D92EBA656C3EFB6BCA04A6B5D7FBF7846E7DAFCA5A52F2801E06",
                "size": 2691886
            },
            "PK_F1816_V2A_CASE_2_PHYS.inp": {
                "dir": os.path.join(BASE_NARROWING_DIR, "step2_envelope", "variant_2a_overlapping"),
                "sha": "2CBEBBB080EDA770B84968ED4F4A68CEAB1C0AD6ACC5C487510CACC8EAD32C52",
                "body": "D890731827B792711CE7FE9DD52E672BDA86E03DBBF380E94BD9708DCD804770",
                "size": 5940109
            },
            "PK_F1816_V2A_CASE_3_PHYS.inp": {
                "dir": os.path.join(BASE_NARROWING_DIR, "step2_envelope", "variant_2a_overlapping"),
                "sha": "D5C94A117231A5E056DBEDA84F39990AF2CD21DF107B2D6A7ECA69D86E98B508",
                "body": "0D50E687B9E0412FDB5AB77C3D0D4DE92F5C7016A86963BF2C446D9C4DE93AF5",
                "size": 4122548
            },
            "PK_F1816_V2A_CASE_5_PHYS.inp": {
                "dir": os.path.join(BASE_NARROWING_DIR, "step2_envelope", "variant_2a_overlapping"),
                "sha": "D5444D85541A36B780FDA51A3EDEF5F8D30F89370D9183C2CCAE85CF89B25B3C",
                "body": "EF118E491812EFE35CC9CFF15EE84064B8A560C0A53B9CAAFE534FF471F2BB9D",
                "size": 1127978
            }
        }
        for name, meta in expected_meshes.items():
            path = os.path.join(meta["dir"], name)
            self.assertTrue(os.path.exists(path), "Mesh file must exist: %s" % path)
            self.assertEqual(os.path.getsize(path), meta["size"], "Size mismatch for %s" % name)
            self.assertEqual(sha256_file(path), meta["sha"], "SHA256 mismatch for %s" % name)
            self.assertEqual(sha256_body(path), meta["body"], "Body SHA mismatch for %s" % name)

    def test_03_six_donor_odbs_exist_and_hashes(self):
        donors_dir = os.path.join(BASE_NARROWING_DIR, "step2_envelope", "donors")
        expected_donors = {
            "PK_CASE1_2STATE_ENVELOPE.odb": {
                "size": 7495536,
                "sha": "AD453610F03E8EE64062E6A07134EF548FAEB128D14AEC701346C82A454C4F71"
            },
            "PK_CASE1_MULTISTEP_RULES.odb": {
                "size": 7793800,
                "sha": "4BE7E1D431B6B4DDE145028D400CC653B65E3CAF06CBCA0ED12D245C63DA2632"
            },
            "PK_CASE2_2STATE_ENVELOPE.odb": {
                "size": 7499600,
                "sha": "0CB56F9BDBD44027E1AFFDE9E624D62DD8BD396252ED55F6202E38DEDB03EE22"
            },
            "PK_CASE2_MULTISTEP_RULES.odb": {
                "size": 7706524,
                "sha": "6289E036B8F01227F2A28015006F4754467D83944AE7489E2E1C0F3F4AF43CE2"
            },
            "PK_CASE3_2STATE_ENVELOPE.odb": {
                "size": 10043780,
                "sha": "2E4ED91108F044EF86B638CCC2CB1027ED69C39FC41E0CB09DC5AACFD2594C24"
            },
            "PK_CASE3_MULTISTEP_RULES.odb": {
                "size": 10167932,
                "sha": "437AAA27C7A99A17BE6581E0ABA63108265BD5D16D86F08C88E0B7D9EB525121"
            }
        }
        for name, meta in expected_donors.items():
            path = os.path.join(donors_dir, name)
            self.assertTrue(os.path.exists(path), "Donor ODB must exist: %s" % path)
            self.assertEqual(os.path.getsize(path), meta["size"], "Size mismatch for donor %s" % name)
            self.assertEqual(sha256_file(path), meta["sha"], "SHA256 mismatch for donor %s" % name)

    def test_04_step2_envelope_summary_repo_relative_paths(self):
        self.assertTrue(os.path.exists(STEP2_SUMMARY), "Step 2 summary must exist")
        with open(STEP2_SUMMARY, "r", encoding="utf-8") as f:
            raw_text = f.read()
            d2 = json.loads(raw_text)
        self.assertNotIn("D:\\", raw_text, "Step 2 summary must contain zero Windows absolute drive prefixes")
        self.assertNotIn("\\Master thesis\\", raw_text, "Step 2 summary must contain zero Windows backslash path fragments")
        for var_name in ["variant_2b_reduced", "variant_2a_overlapping"]:
            for cid, case_data in d2[var_name].items():
                p = case_data["phys_inp"]
                self.assertFalse(p.startswith("D:"), "%s %s path must not start with D:" % (var_name, cid))
                self.assertIn("/", p, "%s %s path must use forward slashes" % (var_name, cid))
                self.assertTrue(p.startswith("models/"), "%s %s path must be repo-relative" % (var_name, cid))

    def test_05_f1816_report_artifact_table_integrity(self):
        self.assertTrue(os.path.exists(F1816_REPORT), "F1816 report must exist")
        with open(F1816_REPORT, "r", encoding="utf-8") as f:
            content = f.read()
        
        # Verify actual summary and receipt hashes are present in report
        self.assertIn("10E7D51946C25731BB0875EB22A6A315CF05AFB63A97846567C72CCF7BA9BA86", content,
                      "Report must contain actual Step 1 summary hash")
        self.assertIn("7,608", content, "Report must contain actual Step 1 summary byte size")
        self.assertIn("A6DEFD62AE43F397F0B65439868A16F445BC6952989DFC1CBDA7F25EC3BEFB2D", content,
                      "Report must contain actual Step 2 summary hash")
        self.assertIn("8,397", content, "Report must contain actual Step 2 summary byte size")
        self.assertIn("FD1377F90AFAE7D1164E6940A513E46C57E02CA535B9AD1A9E65B1382AA0BD52", content,
                      "Report must contain actual receipt hash")
        
        # Verify section 2.1 framework invariance explanation
        self.assertIn("intentionally not modified", content,
                      "Report section 2.1 must explain why the shared framework was not modified")
        self.assertIn("4276A5DC1AF22A6A117102D8C24492789E8AA4EBFD4AF079C58EE86DBEEC7C8B", content,
                      "Report section 2.1 must record the unchanged framework SHA")

    def test_06_step1_and_step2_run_scripts_exist(self):
        scripts = [
            "scripts/remeshing/run_f1816_step1_master.py",
            "scripts/remeshing/run_f1816_step1_minmax.py",
            "scripts/remeshing/run_f1816_step2_master.py",
            "scripts/remeshing/run_f1816_step2_single.py"
        ]
        for s in scripts:
            full = os.path.join(REPO_ROOT, s)
            self.assertTrue(os.path.exists(full), "Run script must exist: %s" % s)
            self.assertGreater(os.path.getsize(full), 1000, "Script must be non-trivial: %s" % s)

    def test_07_variant_mesh_element_counts(self):
        with open(STEP1_SUMMARY, "r", encoding="utf-8") as f:
            d1 = json.load(f)
        with open(STEP2_SUMMARY, "r", encoding="utf-8") as f:
            d2 = json.load(f)
        
        # Step 1 element counts
        self.assertEqual(d1["cases"]["case_1"]["total_elements"], 63210)
        self.assertEqual(d1["cases"]["case_2"]["total_elements"], 56300)
        self.assertEqual(d1["cases"]["case_3"]["total_elements"], 87786)
        self.assertEqual(d1["cases"]["case_5"]["total_elements"], 51598)
        
        # Step 2b element counts and gate failures
        self.assertEqual(d2["variant_2b_reduced"]["case_1"]["elements"], 29314)
        self.assertFalse(d2["variant_2b_reduced"]["case_1"]["scientific_gate"]["pass"])
        self.assertEqual(d2["variant_2b_reduced"]["case_2"]["elements"], 83913)
        self.assertEqual(d2["variant_2b_reduced"]["case_3"]["elements"], 51549)
        self.assertFalse(d2["variant_2b_reduced"]["case_3"]["scientific_gate"]["pass"])
        self.assertEqual(d2["variant_2b_reduced"]["case_5"]["elements"], 15466)
        self.assertTrue(d2["variant_2b_reduced"]["case_5"]["scientific_gate"]["pass"])
        
        # Step 2a element counts and gate failures
        self.assertEqual(d2["variant_2a_overlapping"]["case_1"]["elements"], 37511)
        self.assertEqual(d2["variant_2a_overlapping"]["case_2"]["elements"], 82869)
        self.assertEqual(d2["variant_2a_overlapping"]["case_3"]["elements"], 57464)
        self.assertFalse(d2["variant_2a_overlapping"]["case_3"]["scientific_gate"]["pass"])
        self.assertEqual(d2["variant_2a_overlapping"]["case_5"]["elements"], 15466)
        self.assertTrue(d2["variant_2a_overlapping"]["case_5"]["scientific_gate"]["pass"])

    def test_08_governance_invariants(self):
        with open(RECEIPT_PATH, "r", encoding="utf-8") as f:
            rcpt = json.load(f)
        self.assertEqual(rcpt["governing_objectives"]["cumulative_pbs_submissions"], 35)
        self.assertEqual(rcpt["governing_objectives"]["new_pbs_submissions"], 0)
        self.assertEqual(rcpt["governing_objectives"]["master_goal_status"], "OPEN")


if __name__ == "__main__":
    unittest.main()
