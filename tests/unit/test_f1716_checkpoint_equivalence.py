import pathlib
import re
import pytest

REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]
DAT_PATH = REPO_ROOT / "results" / "validation" / "PK_F1716_CHECKPOINT_4T.dat"
CSV_PATH = REPO_ROOT / "results" / "validation" / "f1716_checkpoint_4t_uel_energy_balance.csv"


def parse_checkpoint_dat(dat_path):
    with open(dat_path, "r", encoding="utf-8") as f:
        text = f.read()

    # Split into increment output blocks
    # Look for "THE FOLLOWING TABLE IS PRINTED FOR NODES BELONGING TO NODE SET N_RP"
    rp_blocks = re.findall(
        r"THE FOLLOWING TABLE IS PRINTED FOR NODES BELONGING TO NODE SET N_RP\s+"
        r"NODE FOOT-\s+U2\s+RF2\s+NOTE\s+"
        r"13276\s+([0-9.E+-]+)\s+([0-9.E+-]+)",
        text,
    )

    # Look for N_BOTTOM tables
    bottom_blocks = re.findall(
        r"THE FOLLOWING TABLE IS PRINTED FOR NODES BELONGING TO NODE SET N_BOTTOM(.*?)(?:MAXIMUM|THE FOLLOWING|\Z)",
        text,
        re.DOTALL,
    )

    results = []
    for i, (u2_str, rf2_str) in enumerate(rp_blocks):
        u2_rp = float(u2_str)
        rf2_rp = float(rf2_str)

        # Parse bottom nodes in corresponding block
        bottom_lines = bottom_blocks[i].strip().split("\n")
        bottom_rf_sum = 0.0
        n_bottom_nodes = 0
        for line in bottom_lines:
            parts = line.strip().split()
            if len(parts) == 2 and parts[0].isdigit():
                rf_val = float(parts[1])
                bottom_rf_sum += rf_val
                n_bottom_nodes += 1

        f_bottom_tensile = -bottom_rf_sum
        diff = abs(rf2_rp - f_bottom_tensile)
        rel_diff = (diff / rf2_rp) * 100.0 if rf2_rp > 0 else 0.0

        results.append({
            "inc": i + 1,
            "u2_rp": u2_rp,
            "rf2_rp": rf2_rp,
            "f_bottom": f_bottom_tensile,
            "diff": diff,
            "rel_diff_pct": rel_diff,
            "n_bottom": n_bottom_nodes,
        })

    return results


def test_checkpoint_force_equilibrium():
    assert DAT_PATH.is_file(), f"Missing {DAT_PATH}"
    results = parse_checkpoint_dat(DAT_PATH)
    assert len(results) == 21, f"Expected 21 increments, got {len(results)}"

    print("\n--- F1716 PRODUCTION CHECKPOINT FORCE EQUILIBRIUM ---")
    print(f"{'Inc':<4} {'U2_RP (mm)':<14} {'RF2_RP (kN)':<16} {'F_bottom (kN)':<16} {'Delta RF (kN)':<16} {'Rel Err (%)'}")
    print("-" * 80)
    for r in results:
        print(f"{r['inc']:<4} {r['u2_rp']:<14.6e} {r['rf2_rp']:<16.8f} {r['f_bottom']:<16.8f} {r['diff']:<16.2e} {r['rel_diff_pct']:.6f}%")
        assert r["n_bottom"] == 52, f"Expected 52 bottom nodes, got {r['n_bottom']}"
        assert r["rf2_rp"] > 0, "Top reaction force must be positive"
        assert r["diff"] < 1e-5, f"Top/bottom force mismatch at inc {r['inc']}: {r['diff']}"
        assert r["rel_diff_pct"] < 0.01, f"Relative force mismatch > 0.01%: {r['rel_diff_pct']}%"

    # Terminal state check
    r_final = results[-1]
    assert r_final["u2_rp"] == pytest.approx(0.0050, abs=1e-6)
    assert r_final["rf2_rp"] == pytest.approx(0.83321661, rel=1e-4)
    print(f"\nFinal Increment 21: U2 = {r_final['u2_rp']:.6f} mm, F_top = {r_final['rf2_rp']:.6f} kN, F_bottom = {r_final['f_bottom']:.6f} kN")
    print(f"Force equilibrium discrepancy: {r_final['diff']:.2e} kN ({r_final['rel_diff_pct']:.6f}%)")


def test_checkpoint_energy_balance():
    assert CSV_PATH.is_file(), f"Missing {CSV_PATH}"
    with open(CSV_PATH, "r", encoding="utf-8") as f:
        lines = [line.strip() for line in f if line.strip() and not line.startswith("Step")]

    assert len(lines) >= 21, f"Expected >= 21 lines in CSV, got {len(lines)}"

    # Parse last 21 rows (the current run)
    rows = lines[-21:]
    prev_elas = 0.0
    prev_frac = 0.0

    print("\n--- F1716 PRODUCTION CHECKPOINT UEL DOMAIN ENERGY BALANCE ---")
    print(f"{'Inc':<4} {'StepTime (s)':<14} {'E_elas (J)':<16} {'E_frac (J)':<16} {'E_total (J)'}")
    print("-" * 65)
    for row in rows:
        parts = [p.strip() for p in row.split(",")]
        inc = int(parts[1])
        t_step = float(parts[3])
        e_elas = float(parts[4])
        e_frac = float(parts[5])
        e_total = float(parts[6])

        # Verify no NaN or Inf
        assert e_elas == e_elas and e_elas >= 0.0
        assert e_frac == e_frac and e_frac >= 0.0
        assert e_total == e_total and e_total >= 0.0
        assert abs(e_total - (e_elas + e_frac)) < 1e-9

        # Verify monotonicity of elastic and fracture energy
        assert e_elas >= prev_elas - 1e-12
        assert e_frac >= prev_frac - 1e-12
        prev_elas = e_elas
        prev_frac = e_frac

        print(f"{inc:<4} {t_step:<14.6e} {e_elas:<16.8e} {e_frac:<16.8e} {e_total:<16.8e}")

    print(f"\nFinal Energy at Inc 21: E_elas = {prev_elas:.6e} J, E_frac = {prev_frac:.6e} J, E_tot = {prev_elas+prev_frac:.6e} J")
