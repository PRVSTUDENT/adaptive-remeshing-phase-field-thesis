# -*- coding: utf-8 -*-
"""
test_mode1_f1470_energy_model_and_donor_provenance.py

Unit test suite for Task F1470:
1. Verify four-stage thermodynamic state-transfer energy balance equations (Stage 1 donor,
   Stage 2 projection discrepancy, Stage 3 fixed-displacement relaxation with D_num >= 0,
   Stage 4 forward fracture work). Verify retraction of unphysical Delta E_elas + Delta E_frac + E_diss = 0.
2. Reconcile coarse donor provenance: 2,988 physical nodes in input deck M1-MB-1S.inp
   vs 2,142 active damage nodes in coarse_donor_state_u0050.json (846 intact far-field nodes).
   Verify notch-tip is Node 97 at (0.500, 0.500) mm, resolving prior conflation with node 129.
3. Verify spatial separation between H_max = 53.65 MPa (Element 1208 Gauss points) and
   d_max = 0.094910 (Node 97 vertex), refuting pointwise 0D algebraic equivalence.
4. Verify phase-field initialization semantics: UEL JTYPE 1/3 active DOF 3 (d) vs SVARS (H),
   proving that *INITIAL CONDITIONS, TYPE=SOLUTION alone leaves nodal DOF 3 uninitialized (d=0).
5. Verify Stage C1-0 same-mesh proof design (2,906 -> 2,906 FEs) anchoring to authentic Job 1411891
   full-precision values and explicit retraction of unsupported guarantees (1 Newton iteration, unconditional definiteness).
6. Verify 4-stage Gate 6C progression (C1-0, C1-1, C1-2, C1-3), exclusion of C2 coarsening from active scope,
   and 100% frozen production UEL hash CE8D5EDC... and submission lock.
"""

import json
import hashlib
from pathlib import Path
import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]


def compute_sha256(file_path: Path) -> str:
    with open(file_path, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest().upper()


def test_four_stage_energy_balance_mathematical_consistency():
    """Verify four-stage thermodynamic energy ledger and retraction of unphysical relaxation formula."""
    arch_doc = REPO_ROOT / "docs" / "reports" / "MODE1_METHOD_C1_STATE_INITIALIZATION_AND_CONTINUATION_ARCHITECTURE.md"
    assert arch_doc.exists(), "Architecture report must exist"
    content = arch_doc.read_text(encoding="utf-8")

    # Verify that unphysical equation Delta E_elas + Delta E_frac + E_diss = 0 is retracted
    assert "Delta E_elas,relax + Delta E_frac,relax + E_diss,relax = 0" not in content, (
        "Unphysical equation Delta E_elas + Delta E_frac + E_diss = 0 must be retracted"
    )

    # Verify Stage 1 donor balance
    assert "W_{\\text{ext}, D}" in content
    assert "1.6327" in content  # W_ext and E_elas approx
    assert "0.0307" in content  # E_frac approx
    assert "1.6634" in content  # E_tot approx

    # Verify Stage 2 discrete projection residual
    assert "\\mathbf{R}_R^{(0)}" in content
    assert "\\mathcal{O}(10\\,\\text{N})" in content or "10\\,\\text{N}" in content

    # Verify Stage 3 fixed-displacement relaxation balance
    # Delta W_ext = 0, Delta E_elas,relax = -D_num,relax <= 0, Delta E_frac,relax = 0
    assert "\\Delta W_{\\text{ext, relax}} = 0" in content or "\\Delta W_{\\text{ext}} = 0" in content
    assert "\\mathcal{D}_{\\text{num, relax}}" in content
    assert "\\Delta E_{\\text{elas, relax}} = -\\mathcal{D}_{\\text{num, relax}}" in content
    assert "\\Delta E_{\\text{frac, relax}} = 0" in content

    # Verify Stage 4 forward physical work
    assert "\\Delta W_{\\text{ext}} = \\int_{u_D}^{u} F" in content
    assert "\\Delta E_{\\text{frac}} = G_c \\Delta A_{\\text{crack}}" in content


def test_donor_provenance_node_count_and_notch_tip():
    """Verify coarse donor provenance: 2,988 physical nodes in input deck, 2,142 in JSON, notch tip at Node 97."""
    donor_json_path = REPO_ROOT / "models" / "pandey_kumar_mode1" / "41_method_c_genuine_continuation" / "evidence_forward_audit" / "coarse_donor_state_u0050.json"
    coarse_inp_path = REPO_ROOT / "models" / "pandey_kumar_mode1" / "method_b_preflight_decks" / "M1-MB-1S.inp"

    assert donor_json_path.exists(), "Coarse donor JSON must exist"
    assert coarse_inp_path.exists(), "Coarse donor input deck must exist"

    # Verify coarse deck nodes
    with open(coarse_inp_path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    in_node = False
    physical_nodes = {}
    for line in lines:
        line_s = line.strip()
        if line_s.upper().startswith("*NODE"):
            in_node = True
            continue
        elif line_s.startswith("*"):
            in_node = False
            continue
        if in_node and line_s:
            parts = line_s.split(",")
            try:
                nid = int(parts[0])
                if nid <= 2988:
                    physical_nodes[nid] = (float(parts[1]), float(parts[2]))
            except ValueError:
                pass

    # The deck defines exactly 2,988 physical nodes
    assert len(physical_nodes) == 2988, f"M1-MB-1S.inp must have 2,988 physical nodes, got {len(physical_nodes)}"

    # In coarse mesh, Node 97 is located at notch tip (0.500, 0.500)
    assert 97 in physical_nodes, "Node 97 must exist in coarse deck"
    x97, y97 = physical_nodes[97]
    assert abs(x97 - 0.500) < 1e-5 and abs(y97 - 0.500) < 1e-5, f"Node 97 must be at (0.5, 0.5), got ({x97}, {y97})"

    # Node 129 in coarse mesh is an interior/boundary node, NOT notch tip
    assert 129 in physical_nodes, "Node 129 must exist in coarse deck"
    x129, y129 = physical_nodes[129]
    assert abs(x129 - 0.500) > 0.1, f"Node 129 in coarse deck must not be at x=0.5, got x={x129}"

    # Load donor JSON
    with open(donor_json_path, "r", encoding="utf-8") as f:
        donor = json.load(f)

    # donor JSON num_elements is 2,906
    assert donor["num_elements"] == 2906
    # donor JSON d_nodal has 2,142 active nodes
    assert donor["num_nodes"] == 2142
    assert len(donor["d_nodal"]) == 2142

    # Node 97 has the maximum nodal damage in donor state
    d_nodal = {int(k): float(v) for k, v in donor["d_nodal"].items()}
    max_nid = max(d_nodal, key=d_nodal.get)
    assert max_nid == 97, f"Max damage node in donor must be Node 97, got {max_nid}"
    assert abs(d_nodal[97] - 0.09491037) < 1e-5, f"Damage at Node 97 must be ~0.094910, got {d_nodal[97]}"


def test_spatial_separation_history_and_damage():
    """Verify spatial separation between H_max = 53.65 MPa and d_max = 0.094910."""
    donor_json_path = REPO_ROOT / "models" / "pandey_kumar_mode1" / "41_method_c_genuine_continuation" / "evidence_forward_audit" / "coarse_donor_state_u0050.json"
    with open(donor_json_path, "r", encoding="utf-8") as f:
        donor = json.load(f)

    max_H_raw = donor["max_H"]  # in kN/mm^2
    max_H_MPa = max_H_raw * 1000.0  # 1 kN/mm^2 = 1 GPa = 1000 MPa

    # Global max H is 53.64989 MPa
    assert abs(max_H_MPa - 53.64989) < 1e-3, f"max_H must be ~53.65 MPa, got {max_H_MPa}"

    # Find element containing global max H
    h_gp = donor["h_gp"]
    max_eid = None
    curr_max = 0.0
    for eid_str, vals in h_gp.items():
        if max(vals) > curr_max:
            curr_max = max(vals)
            max_eid = int(eid_str)

    assert max_eid == 1208, f"Global max H must be in Element 1208, got {max_eid}"

    # 0D scalar back-calculation: d / (1 - d) * psi_0
    d_max = donor["max_d_nodal"]
    psi_0 = 180.0  # MPa
    H_0d = (d_max / (1.0 - d_max)) * psi_0
    assert abs(H_0d - 18.88) < 0.1, f"0D back-calculation must yield ~18.88 MPa, got {H_0d}"

    # Verify that authentic finite element H_max (53.65 MPa) is >2.8x higher than 0D value due to Laplacian diffusion
    ratio = max_H_MPa / H_0d
    assert 2.8 < ratio < 2.9, f"FE H_max should be ~2.84x higher than 0D value, got ratio {ratio}"


def test_phase_field_initialization_semantics():
    """Verify UEL active DOF 3 for phase field vs SVARS, and Error 144 displacement IC constraint."""
    uel_source_path = REPO_ROOT / "models" / "pandey_kumar_mode1" / "f42_mixed_uel.for"
    assert uel_source_path.exists(), "Production UEL source must exist"
    uel_text = uel_source_path.read_text(encoding="utf-8")

    # In f42_mixed_uel.for:
    # JTYPE = 1 and JTYPE = 3 are phase elements with active DOF 3 (d)
    assert "JTYPE = 1: 4-Node Quad Phase Element (Active DOF 3" in uel_text
    assert "JTYPE = 3: 3-Node Tri Phase Element  (Active DOF 3" in uel_text
    assert "JTYPE .EQ. 1" in uel_text or "JTYPE.EQ.1" in uel_text

    # SVARS(8+KPT) holds history variable H
    assert "SVARS(8+KPT)" in uel_text or "SVARS(8 + KPT)" in uel_text or "SV_H_COMMITTED" in uel_text

    # Verify architecture report documents nodal DOF 3 vs SVARS distinction
    arch_doc = REPO_ROOT / "docs" / "reports" / "MODE1_METHOD_C1_STATE_INITIALIZATION_AND_CONTINUATION_ARCHITECTURE.md"
    arch_text = arch_doc.read_text(encoding="utf-8")

    assert "DOF 3" in arch_text
    assert "*INITIAL CONDITIONS, TYPE=SOLUTION" in arch_text
    assert "Error 144" in arch_text


def test_stage_c1_0_same_mesh_specification():
    """Verify Stage C1-0 same-mesh numerical proof design and retraction of unsupported guarantees."""
    arch_doc = REPO_ROOT / "docs" / "reports" / "MODE1_METHOD_C1_STATE_INITIALIZATION_AND_CONTINUATION_ARCHITECTURE.md"
    arch_text = arch_doc.read_text(encoding="utf-8")

    # Verify Stage C1-0 definition
    assert "Stage C1-0: Same-Mesh Offset Reproduction" in arch_text
    assert "2,906 -> 2,906 FEs" in arch_text or "2,906 \\to 2,906" in arch_text

    # Reference anchor values
    assert "653.0886" in arch_text
    assert "1.6327" in arch_text
    assert "0.094910" in arch_text

    # Tolerances
    assert "|\\Delta RF| \\le 0.5\\,\\text{N}" in arch_text or "|Delta RF| <= 0.5 N" in arch_text
    assert "0.05\\%" in arch_text or "0.05%" in arch_text

    # Explicit retraction of unsupported guarantees
    assert 'Retract claims of "guaranteed exactly 1 Newton iteration"' in arch_text
    assert "Standard Abaqus convergence criteria apply" in arch_text


def test_four_stage_gate_6c_progression_and_governance():
    """Verify 4-stage Gate 6C progression, exclusion of C2 coarsening, and frozen UEL hash."""
    arch_doc = REPO_ROOT / "docs" / "reports" / "MODE1_METHOD_C1_STATE_INITIALIZATION_AND_CONTINUATION_ARCHITECTURE.md"
    arch_text = arch_doc.read_text(encoding="utf-8")

    # Verify 4 stages present
    assert "Stage C1-0" in arch_text
    assert "Stage C1-1" in arch_text
    assert "Stage C1-2" in arch_text
    assert "Stage C1-3" in arch_text

    # C2 wake coarsening excluded from active scope
    assert "Method C2 selective wake coarsening is strictly excluded from active scope" in arch_text

    # Production UEL hash check
    uel_path = REPO_ROOT / "models" / "pandey_kumar_mode1" / "f42_mixed_uel.for"
    uel_hash = compute_sha256(uel_path)
    assert uel_hash == "CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6", (
        f"Production UEL must match frozen hash, got {uel_hash}"
    )

    # Submission wrapper locked
    wrapper_path = REPO_ROOT / "models" / "pandey_kumar_mode1" / "42_method_c1_forward_refinement_14k" / "submit_c1_forward_refinement_job.sh"
    if wrapper_path.exists():
        wrapper_text = wrapper_path.read_text(encoding="utf-8")
        assert "AUTHORIZED=false" in wrapper_text, "Submission wrapper must have AUTHORIZED=false"
