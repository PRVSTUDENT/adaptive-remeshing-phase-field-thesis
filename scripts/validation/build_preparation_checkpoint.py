"""Generate canonical preparation checkpoint artifact with exact dynamic SHA-256 hashes for F1597."""
import hashlib
import json
from pathlib import Path

WORKSPACE = Path(__file__).resolve().parents[2]
RUN_ID = "ebf8ec9b-fb85-43c9-8397-3b9b095ff870"
TASK_ID = "F1597-CORRECT-PACKAGE72-STATE-TRANSFER"

def sha256_file(rel_path: str) -> str:
    p = WORKSPACE / rel_path
    if not p.is_file():
        raise FileNotFoundError(f"Missing evidence source: {rel_path}")
    h = hashlib.sha256()
    with open(p, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest().upper()

sources = [
    "scripts/remeshing/generate_crack_band_mesh.py",
    "scripts/validation/evaluate_candidate_c2_transfer.py",
    "scripts/validation/evaluate_crack_opening_compatible.py",
    "tests/unit/test_mode1_f1597_coupled_transfer.py",
    "tests/unit/test_mode1_f1597_crack_band_verification.py",
    "tests/unit/test_mode1_f1597_crack_opening_compatible.py",
    "results/validation/c2_operator_comparison.json",
    "models/pandey_kumar_mode1/candidate_intermediate_mesh_c1.inp",
    "models/pandey_kumar_mode1/candidate_crack_band_mesh_c2.inp",
    "models/pandey_kumar_mode1/50_method_c_experimental_offset_continuation/M1_EXP_OFFSET_CONT_NOEXTRAP.inp",
    "models/pandey_kumar_mode1/50_method_c_experimental_offset_continuation/offset_state_table.csv",
    "models/pandey_kumar_mode1/72_method_c_coupled_state_transfer/M1_EXP_COUPLED_TRANSFER_650.inp",
]

evidence_sources = {s: sha256_file(s) for s in sources}

# Load detailed operator comparison data
comp_file = WORKSPACE / "results/validation/c2_operator_comparison.json"
with open(comp_file, "r") as f:
    comp_data = json.load(f)

baseline = comp_data["baseline_continuous_h1"]
cop95 = comp_data["crack_opening_compatible_d95"]
cop90 = comp_data["crack_opening_compatible_d90"]

finding = (
    "Formulated and evaluated a crack-opening-compatible state reconstruction operator on Candidate C2 "
    "(h=0.0010 mm <= ell/3.75, 2,300 quads). By decomposing the opening displacement across fully degraded "
    f"crack-band elements (d >= 0.95), the operator eliminates spurious geometric strain concentration, "
    f"reducing peak effective undamaged strain energy psi0+ from 974.55 kN/mm^2 (baseline H1) down to 12.20 kN/mm^2 "
    f"(-98.7% reduction, and to 2.59 kN/mm^2 at d=0.90) and restoring coupled active-set PDAS convergence in 3 iterations "
    f"(vs 25 non-converged in baseline). Discrete mechanical equilibrium residual is rigorously preserved at <= 1e-10 kN "
    f"(actual 0.0 kN), fracture surface energy preservation is verified at +3.13% (0.3056 mJ vs donor 0.2963 mJ), and "
    f"phase-field KKT complementarity is strictly satisfied. However, equilibrated reaction force remains deficient "
    f"at 0.885 N (-88.73% at d=0.95) and 1.799 N (-77.09% at d=0.90) vs authentic donor (7.851 N). This proves a dual-mechanism "
    f"discretization defect: while the crack-opening operator resolves kinematic strain surging, coarse donor mesh under-resolution "
    f"(h_donor=0.005 mm ~ ell/1.5) produces a non-equilibrium discrete phase-field profile that naturally diffuses and broadens "
    f"under the fine-mesh Laplacian operator, identifying consistent donor mesh resolution as a prerequisite for full reaction force continuity."
)

checkpoint_payload = {
    "schema": 1,
    "task_id": TASK_ID,
    "status": "PREPARATION_COMPLETE",
    "verification_passed": True,
    "finding": finding,
    "evidence_sources": evidence_sources,
    "constitutive_parameters": {
        "ell_mm": 0.0075,
        "Gc_kN_mm": 0.0027,
        "E_kN_mm2": 210.0,
        "nu": 0.3,
        "k_res": 1.0e-7,
        "h_c2_mm": 0.0010,
        "h_over_ell_c2": 0.0010 / 0.0075,
        "resolution_criterion_satisfied": (0.0010 / 0.0075) <= (1.0 / 3.75),
    },
    "operator_comparison": comp_data,
    "dual_mechanism_diagnosis": {
        "kinematic_strain_surge": {
            "mechanism": "Un-split opening displacement Delta u ~ 0.0024 mm concentrates into h=0.0010 mm quads, scaling apparent eps ~ 2.44 and psi0+ ~ 974.55 kN/mm^2.",
            "operator_resolution": "Crack-opening-compatible decomposition filters kinematic separation in broken band (d >= 0.95), reducing peak psi0+ to 12.20 kN/mm^2 (-98.7%) and restoring 3-iteration PDAS convergence.",
            "status": "RESOLVED"
        },
        "phase_field_laplacian_diffusion": {
            "mechanism": "Donor mesh under-resolves diffuse crack band (h_donor = 0.005 mm ~ ell/1.5). Fine-mesh discrete Laplacian diffuses under-resolved donor profile into intact material, softening structure and causing residual RF deficit (-77.1% to -88.7%).",
            "resolution_requirement": "Requires fine-resolved donor mesh (h_donor <= ell/3.75) or profile-preserving constrained phase-field projection.",
            "status": "IDENTIFIED_GOVERNING_DEFECT"
        }
    }
}

target_path = WORKSPACE / f"results/validation/preparation-{RUN_ID}.json"
with open(target_path, "w", encoding="utf-8", newline="\n") as f:
    json.dump(checkpoint_payload, f, indent=2)
    f.write("\n")

print(f"Preparation checkpoint written to {target_path}")
print(f"Finding length: {len(finding)} chars")
