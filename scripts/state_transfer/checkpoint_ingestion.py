"""Mode-I Method C: Checkpoint Ingestion and Segmented Restart Engine.

Task: F1597-CORRECT-PACKAGE72-STATE-TRANSFER
Protocol Version: 2

Provides rigorous ingestion, validation, and restart asset generation
from authentic committed continuation checkpoints (converged_checkpoint_%02d.json)
for seamless multi-segment HPC execution without state loss, unintended unloading,
or convergence criterion divergence.
"""
from __future__ import print_function, division
import csv
import io
import json
import math
from pathlib import Path


NUM_PHYSICAL_NODES = 7265
NUM_PHYSICAL_ELEMENTS = 7056
NUM_GPS_PER_ELEMENT = 4
TOTAL_HISTORY_POINTS = NUM_PHYSICAL_ELEMENTS * NUM_GPS_PER_ELEMENT  # 28224
HEALING_TOLERANCE = 1.0e-6
ROUNDTRIP_CARD_TOLERANCE_MPA = 1.0e-12


def validate_checkpoint_structure(data, expected_target_uy=None, predecessor_data=None):
    """Validate structure, completeness, bounds, and monotonicity of checkpoint data.

    Returns:
        dict: Parsed and indexed state {
            'target_uy_mm': float,
            'u': {node_id: (u1, u2)},
            'd': {node_id: d},
            'h': {(element_id, gp): H_MPa}
        }
    """
    if not isinstance(data, dict):
        raise ValueError("Checkpoint must be a JSON dictionary")

    if data.get("schema") != 1:
        raise ValueError("Unsupported checkpoint schema: %s (expected 1)" % data.get("schema"))

    if not data.get("coupled_convergence", False):
        raise ValueError("Checkpoint rejected: coupled_convergence is not True")

    target_uy = float(data.get("target_uy_mm", 0.0))
    if not math.isfinite(target_uy) or target_uy <= 0.0:
        raise ValueError("Invalid target_uy_mm: %s" % target_uy)

    if expected_target_uy is not None:
        if abs(target_uy - expected_target_uy) > 1.0e-12:
            raise ValueError(
                "Loading coordinate discontinuity: checkpoint uy=%.17g != expected uy=%.17g"
                % (target_uy, expected_target_uy)
            )

    # 1. Validate displacement
    disp_raw = data.get("displacement")
    if not isinstance(disp_raw, list) or len(disp_raw) != NUM_PHYSICAL_NODES:
        raise ValueError(
            "Incomplete displacement list: got %s, expected %d"
            % (len(disp_raw) if isinstance(disp_raw, list) else None, NUM_PHYSICAL_NODES)
        )

    u_dict = {}
    for entry in disp_raw:
        if not (isinstance(entry, (list, tuple)) and len(entry) >= 3):
            raise ValueError("Malformed displacement record: %s" % (entry,))
        nid = int(entry[0])
        u1, u2 = float(entry[1]), float(entry[2])
        if not (1 <= nid <= NUM_PHYSICAL_NODES):
            raise ValueError("Out of range node_id: %d" % nid)
        if nid in u_dict:
            raise ValueError("Duplicate node_id in displacement: %d" % nid)
        if not (math.isfinite(u1) and math.isfinite(u2)):
            raise ValueError("Non-finite displacement at node %d: (%s, %s)" % (nid, u1, u2))
        u_dict[nid] = (u1, u2)

    if len(u_dict) != NUM_PHYSICAL_NODES:
        raise ValueError("Displacement node coverage incomplete: %d != %d" % (len(u_dict), NUM_PHYSICAL_NODES))

    # 2. Validate damage
    damage_raw = data.get("damage")
    if not isinstance(damage_raw, list) or len(damage_raw) != NUM_PHYSICAL_NODES:
        raise ValueError(
            "Incomplete damage list: got %s, expected %d"
            % (len(damage_raw) if isinstance(damage_raw, list) else None, NUM_PHYSICAL_NODES)
        )

    d_dict = {}
    for entry in damage_raw:
        if not (isinstance(entry, (list, tuple)) and len(entry) >= 2):
            raise ValueError("Malformed damage record: %s" % (entry,))
        nid = int(entry[0])
        d_val = float(entry[1])
        if not (1 <= nid <= NUM_PHYSICAL_NODES):
            raise ValueError("Out of range node_id in damage: %d" % nid)
        if nid in d_dict:
            raise ValueError("Duplicate node_id in damage: %d" % nid)
        if not math.isfinite(d_val):
            raise ValueError("Non-finite damage at node %d" % nid)
        if not (0.0 <= d_val <= 1.0 + 1.0e-12):
            raise ValueError("Damage out of physical bounds [0, 1] at node %d: %.17g" % (nid, d_val))
        d_dict[nid] = min(max(d_val, 0.0), 1.0)

    if len(d_dict) != NUM_PHYSICAL_NODES:
        raise ValueError("Damage node coverage incomplete: %d != %d" % (len(d_dict), NUM_PHYSICAL_NODES))

    # 3. Validate history
    history_raw = data.get("history")
    if not isinstance(history_raw, list) or len(history_raw) != TOTAL_HISTORY_POINTS:
        raise ValueError(
            "Incomplete history list: got %s, expected %d"
            % (len(history_raw) if isinstance(history_raw, list) else None, TOTAL_HISTORY_POINTS)
        )

    h_dict = {}
    for entry in history_raw:
        if not (isinstance(entry, (list, tuple)) and len(entry) >= 3):
            raise ValueError("Malformed history record: %s" % (entry,))
        eid = int(entry[0])
        gp = int(entry[1])
        h_val = float(entry[2])
        if not (1 <= eid <= NUM_PHYSICAL_ELEMENTS):
            raise ValueError("Out of range element_id in history: %d" % eid)
        if not (1 <= gp <= NUM_GPS_PER_ELEMENT):
            raise ValueError("Out of range gp in history: %d" % gp)
        key = (eid, gp)
        if key in h_dict:
            raise ValueError("Duplicate (element, gp) in history: %s" % (key,))
        if not math.isfinite(h_val) or h_val < -1.0e-15:
            raise ValueError("Invalid driving history at %s: %.17g" % (key, h_val))
        h_dict[key] = max(h_val, 0.0)

    if len(h_dict) != TOTAL_HISTORY_POINTS:
        raise ValueError("History GP coverage incomplete: %d != %d" % (len(h_dict), TOTAL_HISTORY_POINTS))

    # 4. Monotonicity checks against predecessor if available
    if predecessor_data is not None:
        pred_state = validate_checkpoint_structure(predecessor_data)
        if target_uy <= pred_state["target_uy_mm"]:
            raise ValueError(
                "Unintended unloading: target uy %.17g <= predecessor uy %.17g"
                % (target_uy, pred_state["target_uy_mm"])
            )
        # Check healing
        max_healing = max(pred_state["d"][n] - d_dict[n] for n in d_dict)
        if max_healing > HEALING_TOLERANCE:
            raise ValueError("Damage healing violation: max healing %.17g > %.1e" % (max_healing, HEALING_TOLERANCE))
        # Check history monotonicity
        for key, h_val in h_dict.items():
            if h_val < pred_state["h"][key] - 1.0e-14:
                raise ValueError(
                    "History monotonicity violation at %s: %.17g < predecessor %.17g"
                    % (key, h_val, pred_state["h"][key])
                )

    return {
        "target_uy_mm": target_uy,
        "u": u_dict,
        "d": d_dict,
        "h": h_dict,
    }


def format_solution_cards(h_dict):
    """Format canonical 7+8+3 solution cards for all 7056 elements.

    Returns:
        str: Multiline card text including header '*Initial Conditions, type=SOLUTION\n'
    """
    lines = ["*Initial Conditions, type=SOLUTION\n"]
    for eid in range(1, NUM_PHYSICAL_ELEMENTS + 1):
        # Card 1: eid, 0, 0, 0, 0, 0, 0, 0 (8 entries)
        lines.append("%d, 0, 0, 0, 0, 0, 0, 0\n" % eid)
        # Card 2: 0, H1, H2, H3, H4, 0, 0, 0 (8 entries)
        h1 = h_dict[eid, 1]
        h2 = h_dict[eid, 2]
        h3 = h_dict[eid, 3]
        h4 = h_dict[eid, 4]
        lines.append("0, %.17g, %.17g, %.17g, %.17g, 0, 0, 0\n" % (h1, h2, h3, h4))
        # Card 3: 0, 0, 0 (3 entries)
        lines.append("0, 0, 0\n")
    return "".join(lines)


def verify_solution_cards(cards_text, h_dict):
    """Verify solution card roundtrip against h_dict within double precision."""
    rows = []
    for line in cards_text.splitlines():
        line = line.strip()
        if not line or line.startswith("*"):
            continue
        rows.append([float(x.strip()) for x in line.split(",")])

    expected_rows = NUM_PHYSICAL_ELEMENTS * 3
    if len(rows) != expected_rows:
        raise ValueError("Solution cards row count mismatch: got %d, expected %d" % (len(rows), expected_rows))

    max_error = 0.0
    for idx in range(0, expected_rows, 3):
        card1, card2, card3 = rows[idx], rows[idx + 1], rows[idx + 2]
        if len(card1) != 8 or len(card2) != 8 or len(card3) != 3:
            raise ValueError("Invalid card row lengths at element index %d" % (idx // 3 + 1))
        eid = int(card1[0])
        h1, h2, h3, h4 = card2[1], card2[2], card2[3], card2[4]
        for gp, val in [(1, h1), (2, h2), (3, h3), (4, h4)]:
            err = abs(val - h_dict[eid, gp])
            if err > max_error:
                max_error = err

    if max_error > ROUNDTRIP_CARD_TOLERANCE_MPA:
        raise ValueError("Solution card history discrepancy: %.17g MPa > %.1e MPa" % (max_error, ROUNDTRIP_CARD_TOLERANCE_MPA))

    return max_error


def generate_restart_assets(parsed_state, output_dir):
    """Generate all 5 canonical restart files into output_dir.

    Files:
      - nodal_displacements_initial.csv (7265 rows)
      - nodal_phase_field_initial.csv (7265 rows)
      - d_lower_bounds.csv (7056 rows)
      - initial_conditions_solution.inc (21169 lines)
      - active_set_boundary_cards.inc (7266 lines)
    """
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)

    u_dict = parsed_state["u"]
    d_dict = parsed_state["d"]
    h_dict = parsed_state["h"]

    # 1. nodal_displacements_initial.csv
    disp_csv = io.StringIO(newline="")
    writer = csv.writer(disp_csv, lineterminator="\n")
    writer.writerow(["node_id", "u1", "u2"])
    for nid in range(1, NUM_PHYSICAL_NODES + 1):
        u1, u2 = u_dict[nid]
        writer.writerow([nid, "%.17g" % u1, "%.17g" % u2])
    (out / "nodal_displacements_initial.csv").write_bytes(disp_csv.getvalue().encode("utf-8"))

    # 2. nodal_phase_field_initial.csv
    phase_csv = io.StringIO(newline="")
    writer = csv.writer(phase_csv, lineterminator="\n")
    writer.writerow(["node_id", "d"])
    for nid in range(1, NUM_PHYSICAL_NODES + 1):
        writer.writerow([nid, "%.17g" % d_dict[nid]])
    (out / "nodal_phase_field_initial.csv").write_bytes(phase_csv.getvalue().encode("utf-8"))

    # 3. d_lower_bounds.csv
    # Column mapping: gp (1, 2, 4, 3) mapped to h0_1, h0_2, h0_3, h0_4
    bounds_csv = io.StringIO(newline="")
    writer = csv.writer(bounds_csv, lineterminator="\n")
    writer.writerow(["element_id", "h0_1", "h0_2", "h0_3", "h0_4"])
    for eid in range(1, NUM_PHYSICAL_ELEMENTS + 1):
        writer.writerow([
            eid,
            "%.17g" % h_dict[eid, 1],
            "%.17g" % h_dict[eid, 2],
            "%.17g" % h_dict[eid, 4],
            "%.17g" % h_dict[eid, 3],
        ])
    (out / "d_lower_bounds.csv").write_bytes(bounds_csv.getvalue().encode("utf-8"))

    # 4. initial_conditions_solution.inc
    cards_text = format_solution_cards(h_dict)
    card_err = verify_solution_cards(cards_text, h_dict)
    (out / "initial_conditions_solution.inc").write_bytes(cards_text.encode("utf-8"))

    # 5. active_set_boundary_cards.inc
    active_cards = ["*Boundary\n"]
    for nid in range(1, NUM_PHYSICAL_NODES + 1):
        active_cards.append("%d, 3, 3, %.17g\n" % (nid, d_dict[nid]))
    (out / "active_set_boundary_cards.inc").write_bytes("".join(active_cards).encode("utf-8"))

    return {
        "files_generated": [
            "nodal_displacements_initial.csv",
            "nodal_phase_field_initial.csv",
            "d_lower_bounds.csv",
            "initial_conditions_solution.inc",
            "active_set_boundary_cards.inc",
        ],
        "nodes": NUM_PHYSICAL_NODES,
        "elements": NUM_PHYSICAL_ELEMENTS,
        "history_points": TOTAL_HISTORY_POINTS,
        "max_card_difference_MPa": card_err,
        "target_uy_mm": parsed_state["target_uy_mm"],
    }


def make_fixture_checkpoint_from_accepted_step1(endpoint_json_path, history_json_path, output_checkpoint_path):
    """Construct an authentic schema=1 test fixture checkpoint from accepted Step 1 data.

    Preserves 100% authentic values from Job 1419113.mmaster02.
    """
    endpoint = json.loads(Path(endpoint_json_path).read_text(encoding="utf-8"))
    history = json.loads(Path(history_json_path).read_text(encoding="utf-8"))

    nodes = endpoint["nodes"]
    if len(nodes) != NUM_PHYSICAL_NODES:
        raise ValueError("Invalid node count in endpoint: %d" % len(nodes))

    disp = [[r[0], r[1], r[2]] for r in nodes]
    damage = [[r[0], r[3]] for r in nodes]

    h_records = history["history_gp_records"]
    if len(h_records) != TOTAL_HISTORY_POINTS:
        raise ValueError("Invalid history count in history: %d" % len(h_records))

    hist = [[r["element_id"], r["gp"], r["h_MPa"]] for r in h_records]

    checkpoint = {
        "schema": 1,
        "target_uy_mm": float(endpoint["rp_u2"]),
        "displacement": disp,
        "damage": damage,
        "history": hist,
        "coupled_convergence": True,
        "physical_acceptance": "UNVERIFIED",
        "physical_review": "Matching-load reference comparison <=5% force and <=2% raw energy required",
        "source_provenance": {
            "endpoint_source": str(endpoint_json_path),
            "history_source": str(history_json_path),
            "pbs_job_id": "1419113.mmaster02",
        },
    }

    out_path = Path(output_checkpoint_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(checkpoint, indent=2) + "\n", encoding="utf-8")
    return checkpoint
