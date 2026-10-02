#!/usr/bin/env python3
"""Regression & preflight assertions for Pandey & Kumar (2025) Mode-I INP step increment consistency.

Ensures that:
1. Every static step specifies an increment limit `inc` >= ceil(time_period / dt_max) so
   `***ERROR: TOO MANY INCREMENTS NEEDED TO COMPLETE THE STEP` cannot occur.
2. Step 1 and Step 2 boundary displacements monotonically span 0.0 -> 0.0050 mm -> 0.0100 mm.
3. User element definitions and material properties match the reference paper.
"""

import math
import os
import re
import unittest

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
STD_INP_PATH = os.path.join(
    PROJECT_ROOT,
    "models",
    "pandey_kumar_mode1",
    "01_standard_pfm_reference",
    "PK_MODE1_STANDARD_PFM.inp",
)


def parse_step_static_cards(inp_path: str):
    """Parses *Step and *Static cards from an Abaqus INP file."""
    steps = []
    current_step = None

    with open(inp_path, "r", encoding="utf-8", errors="replace") as f:
        lines = f.readlines()

    i = 0
    while i < len(lines):
        line = lines[i].strip()
        if line.upper().startswith("*STEP"):
            m_inc = re.search(r"inc\s*=\s*(\d+)", line, re.IGNORECASE)
            m_name = re.search(r"name\s*=\s*([^,]+)", line, re.IGNORECASE)
            inc_val = int(m_inc.group(1)) if m_inc else 100
            name_val = m_name.group(1).strip() if m_name else f"Step-{len(steps)+1}"
            current_step = {
                "name": name_val,
                "inc_max": inc_val,
                "static": None,
                "boundary_disp": [],
            }
            steps.append(current_step)
        elif line.upper().startswith("*STATIC") and current_step is not None:
            i += 1
            if i < len(lines):
                data_line = lines[i].strip()
                parts = [float(p.strip()) for p in data_line.split(",") if p.strip()]
                if len(parts) >= 2:
                    dt_init = parts[0]
                    t_period = parts[1]
                    dt_min = parts[2] if len(parts) > 2 else 1e-9
                    dt_max = parts[3] if len(parts) > 3 else dt_init
                    current_step["static"] = {
                        "dt_init": dt_init,
                        "t_period": t_period,
                        "dt_min": dt_min,
                        "dt_max": dt_max,
                    }
        elif line.upper().startswith("*BOUNDARY") and current_step is not None:
            # Read subsequent boundary lines until next keyword
            j = i + 1
            while j < len(lines) and not lines[j].strip().startswith("*"):
                b_line = lines[j].strip()
                if "N_RP" in b_line and "2" in b_line:
                    b_parts = [p.strip() for p in b_line.split(",") if p.strip()]
                    if len(b_parts) >= 4:
                        current_step["boundary_disp"].append(float(b_parts[3]))
                j += 1
        elif line.upper().startswith("*END STEP"):
            current_step = None
        i += 1

    return steps


class TestPandeyKumarStepIncrementConsistency(unittest.TestCase):
    def test_std_pfm_step_increment_consistency(self):
        """Assert that each Step's time period / dt_max <= inc (no increment overflow)."""
        self.assertTrue(os.path.exists(STD_INP_PATH), f"Missing INP file: {STD_INP_PATH}")
        steps = parse_step_static_cards(STD_INP_PATH)
        self.assertGreaterEqual(len(steps), 2, "Expected at least 2 steps (Step-1 and Step-2)")

        for step in steps:
            static_data = step["static"]
            self.assertIsNotNone(static_data, f"Step '{step['name']}' is missing *Static definition")
            t_period = static_data["t_period"]
            dt_max = static_data["dt_max"]
            inc_max = step["inc_max"]

            # Required increments for fixed or upper-bound time stepping
            n_req = math.ceil(t_period / dt_max)
            self.assertLessEqual(
                n_req,
                inc_max,
                f"Step '{step['name']}' requires at least {n_req} increments to complete "
                f"(T={t_period}, dt_max={dt_max}), but inc ceiling is only {inc_max}! "
                f"This will cause '***ERROR: TOO MANY INCREMENTS NEEDED TO COMPLETE THE STEP'.",
            )

    def test_std_pfm_displacement_schedule(self):
        """Verify Step-1 targets u=0.005 mm and Step-2 targets u=0.010 mm."""
        steps = parse_step_static_cards(STD_INP_PATH)
        step1 = steps[0]
        step2 = steps[1]

        self.assertIn(0.0050, step1["boundary_disp"], "Step 1 must target displacement 0.0050 mm")
        self.assertIn(0.0100, step2["boundary_disp"], "Step 2 must target displacement 0.0100 mm")

    def test_std_pfm_material_and_fracture_parameters(self):
        """Verify E=210 GPa, nu=0.3, Gc=0.0027 kN/mm, l0=0.0075 mm in UEL properties."""
        with open(STD_INP_PATH, "r", encoding="utf-8", errors="replace") as f:
            content = f.read()

        # Check UEL property line: 0.0075, 0.0027, 210.0, 0.3, ...
        self.assertIn("0.0075, 0.0027, 210.0, 0.3", content)
        self.assertIn("15192.0", content)


if __name__ == "__main__":
    unittest.main()