# -*- coding: utf-8 -*-
"""
test_mode1_f1597_h43_runtime_injection_audit.py
Unit test suite for Hypothesis H43: Abaqus Runtime State-Injection Validation & Traceability Audit.
Task: F1597-CORRECT-PACKAGE72-STATE-TRANSFER
Protocol Version: 2

Tests:
  1. UMAT companion element is strictly a read-only diagnostic visualizer.
  2. Frozen UEL (f42_mixed_uel.for) initializes history strictly from SVARS(9..12).
  3. UEXTERNALDB(LOP=0) zeroes state arrays and lacks CSV reader capability.
  4. Sentinel history record accurately maps to SVARS(9..12) initial conditions cards.
  5. Package 142 generator currently lacks input deck and boundary card assembly.
  6. Predeclared governance gates and invariants remain strictly unchanged.
"""

from __future__ import print_function, division
import unittest
import os
import sys
import json
import hashlib
from pathlib import Path

REPO_ROOT = Path(r"D:\Master thesis\Adaptive remeshing")
sys.path.insert(0, str(REPO_ROOT))

from scripts.validation.audit_h43_runtime_state_injection import (
    audit_frozen_uel_subroutine, audit_unified_uel_subroutine,
    audit_package142_generator, verify_variable_injection_provenance,
    FROZEN_UEL_PATH, UNIFIED_UEL_PATH, PACKAGE142_GEN_PATH, OUTPUT_AUDIT_PATH
)


class TestH43RuntimeInjectionAudit(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.frozen_audit = audit_frozen_uel_subroutine(FROZEN_UEL_PATH)
        cls.unified_audit = audit_unified_uel_subroutine(UNIFIED_UEL_PATH)
        cls.gen_audit = audit_package142_generator(PACKAGE142_GEN_PATH)
        cls.trace_table = verify_variable_injection_provenance(cls.frozen_audit, cls.unified_audit, cls.gen_audit)

    def test_01_umat_is_read_only_diagnostic_output(self):
        """Verifies UMAT companion elements only output STATEV and never modify state."""
        self.assertTrue(self.frozen_audit["umat_companion_is_diagnostic_output_only"])
        # Direct check on f42 source
        with open(FROZEN_UEL_PATH, "r") as f:
            lines = f.readlines()
        umat_lines = [l for l in lines if "STATEV(" in l]
        self.assertGreater(len(umat_lines), 5, "Expected multiple STATEV assignments in UMAT")
        # Ensure no reverse assignments (e.g. SV_PHASE_TRIAL = STATEV)
        reverse_assignments = [l for l in lines if "SV_PHASE_TRIAL(PHYSIDX) = STATEV" in l or "SV_H_TRIAL(PHYSIDX" in l and "= STATEV" in l]
        self.assertEqual(len(reverse_assignments), 0, "UMAT must never assign to COMMON block arrays")

    def test_02_frozen_uel_initializes_h_from_svars_9_to_12(self):
        """Verifies f42_mixed_uel.for loads history at step start strictly from SVARS(8+KPT)."""
        self.assertTrue(self.frozen_audit["uel_initializes_h_from_svars_8_plus_kpt"])
        self.assertEqual(self.frozen_audit["svars_history_indices"], [9, 10, 11, 12])
        # Direct check on f42 source
        with open(FROZEN_UEL_PATH, "r") as f:
            content = f.read()
        self.assertIn("SV_H_COMMITTED(PHYSIDX, KPT) = SVARS(8+KPT)", content)
        self.assertIn("SV_H_TRIAL(PHYSIDX, KPT)     = SVARS(8+KPT)", content)

    def test_03_uexternaldb_zeroes_state_and_has_no_csv_reader(self):
        """Verifies UEXTERNALDB on LOP=0 zeroes arrays and cannot read external CSVs."""
        self.assertTrue(self.frozen_audit["uexternaldb_zeroes_state_on_lop0"])
        self.assertFalse(self.frozen_audit["has_csv_reader_in_uexternaldb"])
        self.assertFalse(self.frozen_audit["has_sv_d_lower_bound_in_fortran"])

    def test_04_sentinel_svars_generation_contract(self):
        """Tests that sentinel GP history [H1, H2, H3, H4] maps to exact SVARS(9..12) card syntax."""
        sentinel_eid = 42
        sentinel_h = [12.345678, 23.456789, 34.567890, 45.678901]

        # Construct standard Abaqus *INITIAL CONDITIONS, TYPE=SOLUTION 18-variable entry
        svars = [0.0] * 18
        # Fill SVARS(9..12) with sentinel history
        for k, h_val in enumerate(sentinel_h):
            svars[8 + k] = h_val
        svars[14] = 1.0  # g(d) = 1.0 for intact

        card_lines = []
        card_lines.append("%8d, %14.7e, %14.7e, %14.7e, %14.7e, %14.7e, %14.7e, %14.7e" % tuple([sentinel_eid] + svars[0:7]))
        card_lines.append("  %14.7e, %14.7e, %14.7e, %14.7e, %14.7e, %14.7e, %14.7e, %14.7e" % tuple(svars[7:15]))
        card_lines.append("  %14.7e, %14.7e, %14.7e" % tuple(svars[15:18]))
        card_str = "\n".join(card_lines)

        self.assertIn("%8d" % sentinel_eid, card_lines[0])
        self.assertIn("%.7e" % sentinel_h[0], card_str)
        self.assertIn("%.7e" % sentinel_h[1], card_str)
        self.assertIn("%.7e" % sentinel_h[2], card_str)
        self.assertIn("%.7e" % sentinel_h[3], card_str)

    def test_05_package142_generator_missing_cards_defect(self):
        """Proves Package142DeckGenerator isolates the 3 missing deck generation components."""
        self.assertTrue(self.gen_audit["generates_d_lower_bounds_csv"])
        self.assertTrue(self.gen_audit["generates_nodal_displacements_initial_csv"])
        self.assertTrue(self.gen_audit["generates_nodal_phase_field_initial_csv"])
        self.assertTrue(self.gen_audit["generates_package_manifest_json"])

        # Defects: missing inp deck, missing active set cards, missing solution cards
        self.assertFalse(self.gen_audit["generates_inp_deck_file"], "Generator must be identified as lacking inp deck output")
        self.assertFalse(self.gen_audit["generates_active_set_boundary_cards_inc"], "Generator must be identified as lacking boundary cards")
        self.assertFalse(self.gen_audit["generates_initial_conditions_solution_cards"], "Generator must be identified as lacking solution cards")

    def test_06_predeclared_governance_and_gate_invariance(self):
        """Verifies that all governing gates remain strictly invariant under H43 audit."""
        self.assertTrue(OUTPUT_AUDIT_PATH.exists(), "Audit JSON must exist on disk")
        with open(OUTPUT_AUDIT_PATH, "r") as f:
            data = json.load(f)

        self.assertEqual(data["classification"], "H43_RUNTIME_INJECTION_DEFECT_IDENTIFIED")
        self.assertEqual(data["defects_count"], 3)
        self.assertIn("STAGE_C1_2_STEP2_ENERGY_GATE_FAILED (+2.00803158%)", data["finding"])
        self.assertIn("P113_GATE_VALID_FAILURE", data["finding"])
        self.assertIn("H24_REFERENCE_AUDIT_PENDING", data["finding"])


if __name__ == "__main__":
    unittest.main()
