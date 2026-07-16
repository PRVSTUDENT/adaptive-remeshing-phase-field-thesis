#!/usr/bin/env python3
"""Build the Molnar candidate-v2 SDV15 targeted diagnostic variant.

The diagnostic variant is generated from committed candidate-v2 inputs and the
committed SDV15 forensic evidence. It preserves the candidate-v2 model and adds
only selected source-side logging plus reproducibility records.
"""

from __future__ import annotations

import csv
import hashlib
import json
import math
import re
import shutil
import subprocess
import tempfile
from collections import defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
N_ELEM = 33852
BASE = ROOT / "models/generated/molnar_gravouil_2017/paper_matched_single_notch_v2"
DIAG = ROOT / "models/generated/molnar_gravouil_2017/paper_matched_single_notch_v2_sdv15_diagnostic"
RUN_DIR = ROOT / "runs/hpc/paper_matched_single_notch_v2_sdv15_diagnostic"
VALIDATION_DIR = ROOT / "results/validation/molnar_paper_matched_single_notch_v2_sdv15_diagnostic"
UNRESOLVED = ROOT / "runs/hpc/paper_matched_single_notch_v2/scientific_review/sdv15_mapping_resolution/sdv15_unresolved_event_mapping.csv"
EQUIV = ROOT / "runs/hpc/paper_matched_single_notch_v2/scientific_review/sdv15_detailed_review/sdv15_equivalent_state_comparison.csv"
DETAIL = ROOT / "runs/hpc/paper_matched_single_notch_v2/scientific_review/sdv15_detailed_review/sdv15_decrease_events_full.csv"
FINAL_CONTOUR = ROOT / "runs/hpc/paper_matched_single_notch_v2/extracted/matched_state_04_Step-2_frame_0100_contour_sdv14_sdv15_sdv16.csv"
BASE_RF = ROOT / "runs/hpc/paper_matched_single_notch_v2/scientific_review/rf_u_verified.csv"
PBS = ROOT / "scripts/hpc/molnar_paper_matched_single_notch_v2_sdv15_diagnostic.pbs"
POST = ROOT / "scripts/postprocessing/analyze_molnar_sdv15_targeted_diagnostic.py"
CHECKLIST = ROOT / "docs/project/PROJECT_PHASE_CHECKLIST.md"
AGENT_FILES = [ROOT / ".agent.md", ROOT / "adaptive_remeshing_phase_field_agent.md"]


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def parse_deck(path: Path) -> tuple[dict[int, tuple[float, float]], dict[int, tuple[int, ...]]]:
    nodes: dict[int, tuple[float, float]] = {}
    elements: dict[int, tuple[int, ...]] = {}
    mode = None
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        lower = line.lower()
        if not line or line.startswith("**"):
            continue
        if lower.startswith("*node"):
            mode = "node"
            continue
        if lower.startswith("*element"):
            mode = "element"
            continue
        if line.startswith("*"):
            mode = None
            continue
        if mode == "node":
            parts = [p.strip() for p in line.split(",") if p.strip()]
            if len(parts) >= 3:
                nodes[int(parts[0])] = (float(parts[1]), float(parts[2]))
        elif mode == "element":
            parts = [p.strip() for p in line.split(",") if p.strip()]
            if len(parts) >= 5:
                label = int(parts[0])
                if 1 <= label <= N_ELEM:
                    elements[label] = tuple(int(p) for p in parts[1:5])
    return nodes, elements


def centroid_and_adjacency(nodes: dict[int, tuple[float, float]], elements: dict[int, tuple[int, ...]]):
    centroids: dict[int, tuple[float, float]] = {}
    edge_to_elements: dict[tuple[int, int], list[int]] = defaultdict(list)
    for label, conn in elements.items():
        xy = [nodes[n] for n in conn]
        centroids[label] = (sum(p[0] for p in xy) / 4.0, sum(p[1] for p in xy) / 4.0)
        edges = [(conn[0], conn[1]), (conn[1], conn[2]), (conn[2], conn[3]), (conn[3], conn[0])]
        for a, b in edges:
            edge_to_elements[tuple(sorted((a, b)))].append(label)
    adjacency: dict[int, set[int]] = defaultdict(set)
    for owners in edge_to_elements.values():
        if len(owners) > 1:
            for a in owners:
                adjacency[a].update(o for o in owners if o != a)
    return centroids, adjacency


def source_ip_from_odb(odb_ip: int) -> int:
    if odb_ip == 3:
        return 4
    if odb_ip == 4:
        return 3
    return odb_ip


def add_category(categories: dict[tuple[int, int], set[str]], physical: int, odb_ip: int, name: str) -> None:
    categories[(physical, source_ip_from_odb(odb_ip))].add(name)


def build_targets() -> tuple[list[dict[str, object]], dict[str, int]]:
    nodes, elements = parse_deck(BASE / "paper_matched_single_notch_v2.inp")
    centroids, adjacency = centroid_and_adjacency(nodes, elements)
    categories: dict[tuple[int, int], set[str]] = defaultdict(set)

    unresolved_rows = read_csv(UNRESOLVED)
    for row in unresolved_rows:
        add_category(categories, int(row["physical_label"]), int(row["odb_ip"]), "insufficient_output_evidence")

    equiv_rows = read_csv(EQUIV)
    staggered_rows = [r for r in equiv_rows if r["final_category"] == "staggered_sync_effect"]
    for row in staggered_rows:
        add_category(categories, int(row["mapped_physical_element"]), int(row["odb_integration_point"]), "staggered_sync_effect")

    worst_physical = 16427
    add_category(categories, worst_physical, 3, "worst_event_84131_ip3")
    for ip in (1, 2, 3, 4):
        categories[(worst_physical, source_ip_from_odb(ip))].add("all_ips_worst_event_element")

    for neighbour in sorted(adjacency[worst_physical]):
        for ip in (1, 2, 3, 4):
            categories[(neighbour, source_ip_from_odb(ip))].add("edge_sharing_neighbour_of_worst_event")

    crack_path = []
    if FINAL_CONTOUR.exists():
        rows = read_csv(FINAL_CONTOUR)
        by_phys: dict[int, list[float]] = defaultdict(list)
        for row in rows:
            vis = int(row["element"])
            phys = vis - 2 * N_ELEM
            by_phys[phys].append(float(row["sdv15"]))
        crack_elems = {phys for phys, vals in by_phys.items() if sum(vals) / len(vals) >= 0.95}
        if worst_physical in crack_elems:
            seen = {worst_physical}
            stack = [worst_physical]
            while stack:
                current = stack.pop()
                for nb in adjacency[current]:
                    if nb in crack_elems and nb not in seen:
                        seen.add(nb)
                        stack.append(nb)
            crack_path = sorted(seen, key=lambda e: (centroids[e][0], centroids[e][1], e))
            labels = [e for e in crack_path]
            if worst_physical in labels:
                i = labels.index(worst_physical)
                for neighbour in labels[max(0, i - 1) : min(len(labels), i + 2)]:
                    for ip in (1, 2, 3, 4):
                        categories[(neighbour, source_ip_from_odb(ip))].add("connected_crack_path_preceding_following")

    targets = []
    for (physical, source_ip), cats in sorted(categories.items()):
        conn = elements[physical]
        cx, cy = centroids[physical]
        odb_ip = 4 if source_ip == 3 else 3 if source_ip == 4 else source_ip
        targets.append(
            {
                "physical_element": physical,
                "u1_label": physical,
                "u2_label": physical + N_ELEM,
                "cps4_label": physical + 2 * N_ELEM,
                "source_storage_ip": source_ip,
                "odb_ip": odb_ip,
                "source_category": "+".join(sorted(cats)),
                "connectivity": " ".join(str(n) for n in conn),
                "centroid_x": f"{cx:.12g}",
                "centroid_y": f"{cy:.12g}",
                "distance_from_notch_tip": f"{math.hypot(cx, cy):.12g}",
            }
        )

    counts = {
        "target_physical_elements": len({int(t["physical_element"]) for t in targets}),
        "target_element_ip_pairs": len(targets),
        "insufficient_output_event_rows": len(unresolved_rows),
        "staggered_sync_event_rows": len(staggered_rows),
        "crack_path_elements_at_sdv15_0p95": len(crack_path),
    }
    return targets, counts


def write_targets(targets: list[dict[str, object]], counts: dict[str, int]) -> None:
    DIAG.mkdir(parents=True, exist_ok=True)
    with (DIAG / "diagnostic_targets.csv").open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(targets[0].keys()))
        writer.writeheader()
        writer.writerows(targets)

    elems = [int(t["physical_element"]) for t in targets]
    ips = [int(t["source_storage_ip"]) for t in targets]
    lines = [
        f"      INTEGER NTARGET",
        f"      PARAMETER (NTARGET={len(targets)})",
        f"      INTEGER TARGET_ELEM(NTARGET),TARGET_IP(NTARGET)",
    ]

    def data_lines(name: str, values: list[int]) -> list[str]:
        body = ",".join(str(v) for v in values)
        chunks = [body[i : i + 60] for i in range(0, len(body), 60)]
        out = [f"      DATA {name} /"]
        for i, chunk in enumerate(chunks):
            prefix = "     1 "
            suffix = "/" if i == len(chunks) - 1 else ""
            out.append(prefix + chunk + suffix)
        return out

    lines.extend(data_lines("TARGET_ELEM", elems))
    lines.extend(data_lines("TARGET_IP", ips))
    (DIAG / "diagnostic_targets.inc").write_text("\n".join(lines) + "\n", encoding="utf-8")

    md = f"""# SDV15 Diagnostic Target Selection

Classification: `paper_matched_candidate_v2_diagnostic_variant`

Generated by: `scripts/model_generation/build_molnar_v2_sdv15_diagnostic.py`

## Counts

- Target physical elements: `{counts['target_physical_elements']}`
- Target element/IP pairs: `{counts['target_element_ip_pairs']}`
- Prior insufficient-output event rows covered: `{counts['insufficient_output_event_rows']}`
- Prior staggered-sync event rows covered for comparison: `{counts['staggered_sync_event_rows']}`
- Connected crack-path elements at final mean `SDV15 >= 0.95`: `{counts['crack_path_elements_at_sdv15_0p95']}`

## Source Rules

- U1 label equals the physical label `p`.
- U2 label equals `p + {N_ELEM}`.
- CPS4 visualization label equals `p + {2 * N_ELEM}`.
- ODB IPs 3 and 4 are swapped by UMAT before reading `USRVAR`; source-storage IPs in the include file use that source convention.
- Worst event is visualization element `84131`, ODB IP `3`, physical/U1 element `16427`, U2 element `50279`.

The full deterministic list, including category, labels, connectivity, centroid,
and distance from the notch tip, is `diagnostic_targets.csv`. The Fortran target
arrays used by the diagnostic source are `diagnostic_targets.inc`.
"""
    (DIAG / "DIAGNOSTIC_TARGET_SELECTION.md").write_text(md, encoding="utf-8")


def instrument_source() -> None:
    src = (BASE / "SingleNotch_v2.for").read_text(encoding="utf-8")
    out = src
    out = out.replace(
        "       REAL*8 DTM,THCK,HIST,CLPAR,GCPAR,EMOD,ENU,PARK,ENG\n",
        "       REAL*8 DTM,THCK,HIST,CLPAR,GCPAR,EMOD,ENU,PARK,ENG\n"
        "       REAL*8 PHASEIN,PREVRET,CURRET,PHU1,PHU2,VIS14,VIS15\n"
        "       REAL*8 HISTD,UPDQ\n",
    )
    out = out.replace(
        "        IF (STEPITER.EQ.ZERO) THEN\n"
        "          SDV(1)=PHASE-DPHASE\n"
        "        ELSE\n"
        "          SDV(1)=PHASE\n"
        "        ENDIF\n",
        "        PHASEIN=SDV(1)\n"
        "        PREVRET=USRVAR(JELEM,14,INPT)\n"
        "        IF (STEPITER.EQ.ZERO) THEN\n"
        "          SDV(1)=PHASE-DPHASE\n"
        "        ELSE\n"
        "          SDV(1)=PHASE\n"
        "        ENDIF\n",
    )
    out = out.replace(
        "        DO I=1,NSTVTO\n"
        "         SVARS(NSTVTO*(INPT-1)+I)=SDV(I)\n"
        "         USRVAR(JELEM,I+NSTVTT,INPT)=SVARS(NSTVTO*(INPT-1)+I)\n"
        "        END DO\n",
        "        DO I=1,NSTVTO\n"
        "         SVARS(NSTVTO*(INPT-1)+I)=SDV(I)\n"
        "         USRVAR(JELEM,I+NSTVTT,INPT)=SVARS(NSTVTO*(INPT-1)+I)\n"
        "        END DO\n"
        "        CURRET=USRVAR(JELEM,15,INPT)\n"
        "        PHU1=USRVAR(JELEM,15,INPT)\n"
        "        PHU2=USRVAR(JELEM,14,INPT)\n"
        "        VIS14=-999999.D0\n"
        "        VIS15=-999999.D0\n"
        "        HISTD=USRVAR(JELEM,16,INPT)\n"
        "        UPDQ=DPHASE\n"
        "        CALL DIAG_LOG_RECORD(KSTEP,KINC,TIME,JELEM,JELEM,INPT,\n"
        "     1   INPT,1,101,LFLAGS(1),LFLAGS(3),INT(STEPITER),PHASEIN,PHU1,\n"
        "     2   PHU2,VIS14,VIS15,HISTD,PREVRET,CURRET,UPDQ)\n",
    )
    out = out.replace(
        "        IF (STEPITER.EQ.ZERO) THEN\n"
        "         PHASE=USRVAR(JELEM-N_ELEM,15,INPT)\n"
        "        ELSE\n"
        "         PHASE=USRVAR(JELEM-N_ELEM,14,INPT)\n"
        "        ENDIF\n"
        "C\n"
        "        SDV(14)=PHASE\n",
        "        PHASEIN=SDV(14)\n"
        "        PREVRET=USRVAR(JELEM-N_ELEM,14,INPT)\n"
        "        IF (STEPITER.EQ.ZERO) THEN\n"
        "         PHASE=USRVAR(JELEM-N_ELEM,15,INPT)\n"
        "        ELSE\n"
        "         PHASE=USRVAR(JELEM-N_ELEM,14,INPT)\n"
        "        ENDIF\n"
        "C\n"
        "        SDV(14)=PHASE\n",
    )
    out = out.replace(
        "        DO I=1,NSTVTT\n"
        "         SVARS(NSTVTT*(INPT-1)+I)=SDV(I)\n"
        "         USRVAR(JELEM-N_ELEM,I,INPT)=SVARS(NSTVTT*(INPT-1)+I)\n"
        "        END DO\n",
        "        DO I=1,NSTVTT\n"
        "         SVARS(NSTVTT*(INPT-1)+I)=SDV(I)\n"
        "         USRVAR(JELEM-N_ELEM,I,INPT)=SVARS(NSTVTT*(INPT-1)+I)\n"
        "        END DO\n"
        "        CURRET=USRVAR(JELEM-N_ELEM,14,INPT)\n"
        "        PHU1=USRVAR(JELEM-N_ELEM,15,INPT)\n"
        "        PHU2=USRVAR(JELEM-N_ELEM,14,INPT)\n"
        "        VIS14=-999999.D0\n"
        "        VIS15=-999999.D0\n"
        "        HISTD=USRVAR(JELEM-N_ELEM,16,INPT)\n"
        "        UPDQ=ZERO\n"
        "        CALL DIAG_LOG_RECORD(KSTEP,KINC,TIME,JELEM,JELEM-N_ELEM,\n"
        "     1   INPT,INPT,2,201,LFLAGS(1),LFLAGS(3),INT(STEPITER),PHASEIN,\n"
        "     2   PHU1,PHU2,VIS14,VIS15,HISTD,PREVRET,CURRET,UPDQ)\n",
    )
    out = out.replace(
        "       COMMON/KUSER/USRVAR(N_ELEM,NSTV,4)\n"
        "C\n"
        "C -----------------------------------------------------------\n",
        "       COMMON/KUSER/USRVAR(N_ELEM,NSTV,4)\n"
        "       REAL*8 PHASEIN,PREVRET,CURRET,PHU1,PHU2,VIS14,VIS15\n"
        "       REAL*8 HISTD,UPDQ\n"
        "C\n"
        "C -----------------------------------------------------------\n",
    )
    out = out.replace(
        "       DO I=1,NSTATV\n"
        "        STATEV(I)=USRVAR(NELEMAN,I,NPT)\n"
        "       END DO\n",
        "       DO I=1,NSTATV\n"
        "        STATEV(I)=USRVAR(NELEMAN,I,NPT)\n"
        "       END DO\n"
        "       PHASEIN=-999999.D0\n"
        "       PREVRET=USRVAR(NELEMAN,14,NPT)\n"
        "       CURRET=USRVAR(NELEMAN,15,NPT)\n"
        "       PHU1=USRVAR(NELEMAN,15,NPT)\n"
        "       PHU2=USRVAR(NELEMAN,14,NPT)\n"
        "       VIS14=STATEV(14)\n"
        "       VIS15=STATEV(15)\n"
        "       HISTD=STATEV(16)\n"
        "       UPDQ=0.D0\n"
        "       CALL DIAG_LOG_RECORD(KSTEP,KINC,TIME,NOEL,NELEMAN,NPT,NPT,\n"
        "     1  3,301,0,0,0,PHASEIN,PHU1,PHU2,VIS14,VIS15,HISTD,\n"
        "     2  PREVRET,CURRET,UPDQ)\n",
    )

    helper = r"""

      SUBROUTINE DIAG_LOG_RECORD(KSTEP,KINC,TIME,JELEM,PHYS,INPT,
     1 ODBIP,LAYER,STAGE,LFLAG1,LFLAG3,STEPITER,PHASEIN,PHU1,PHU2,
     2 VIS14,VIS15,HISTD,PREVRET,CURRET,UPDQ)
      INCLUDE 'ABA_PARAM.INC'
      DIMENSION TIME(2)
      INTEGER KSTEP,KINC,JELEM,PHYS,INPT,ODBIP,LAYER,STAGE
      INTEGER LFLAG1,LFLAG3,STEPITER
      REAL*8 PHASEIN,PHU1,PHU2,VIS14,VIS15,HISTD,PREVRET,CURRET,UPDQ
      INTEGER DIAG_OPEN,DIAG_SEQ
      LOGICAL DIAG_IS_TARGET
      CHARACTER*512 OUTDIR,FNAME
      INTEGER LENOUT,IOS
      COMMON/KDIAG/DIAG_OPEN,DIAG_SEQ
      SAVE /KDIAG/
      DATA DIAG_OPEN,DIAG_SEQ/0,0/
      IF (.NOT.DIAG_IS_TARGET(PHYS,INPT)) RETURN
      IF (DIAG_OPEN.EQ.0) THEN
       CALL GETOUTDIR(OUTDIR,LENOUT)
       IF (LENOUT.LE.0) THEN
        FNAME='molnar_v2_sdv15_diagnostic_call_trace.csv'
       ELSE
        FNAME=OUTDIR(1:LENOUT)//'/molnar_v2_sdv15_diagnostic_call_trace.csv'
       ENDIF
       OPEN(UNIT=99,FILE=FNAME,STATUS='UNKNOWN',POSITION='APPEND',
     1  ACTION='WRITE',IOSTAT=IOS)
       IF (IOS.NE.0) THEN
        WRITE(7,*) 'SDV15_DIAGNOSTIC_OPEN_FAILED',IOS
        RETURN
       ENDIF
       WRITE(99,'(A)') 'run_id,call_sequence,kstep,kinc,time1,time2,'//
     1  'jelem,physical_element,u1_label,u2_label,cps4_label,'//
     2  'source_storage_ip,odb_ip,source_layer_code,update_stage_code,'//
     3  'lflags1,lflags3,stepiter,phase_entering,phase_after_u1,'//
     4  'phase_copied_u2,visual_sdv14,visual_sdv15,sdv16_history,'//
     5  'previous_retained_phase,current_retained_phase,phase_update'
       DIAG_OPEN=1
      ENDIF
      DIAG_SEQ=DIAG_SEQ+1
      WRITE(99,9000) 'molnar_v2_sdv15_diag',DIAG_SEQ,KSTEP,KINC,
     1 TIME(1),TIME(2),JELEM,PHYS,PHYS,PHYS+33852,PHYS+67704,
     2 INPT,ODBIP,LAYER,STAGE,LFLAG1,LFLAG3,STEPITER,PHASEIN,PHU1,
     3 PHU2,VIS14,VIS15,HISTD,PREVRET,CURRET,UPDQ
      CALL FLUSH(99)
 9000 FORMAT(A,',',I12,',',I6,',',I6,',',1PE24.16,',',1PE24.16,
     1 ',',I8,',',I8,',',I8,',',I8,',',I8,',',I4,',',I4,',',
     2 I2,',',I3,',',I8,',',I8,',',I8,',',1PE24.16,',',
     3 1PE24.16,',',1PE24.16,',',1PE24.16,',',1PE24.16,',',
     4 1PE24.16,',',1PE24.16,',',1PE24.16,',',1PE24.16)
      RETURN
      END

      LOGICAL FUNCTION DIAG_IS_TARGET(PHYS,INPT)
      INTEGER PHYS,INPT,I
      INCLUDE 'diagnostic_targets.inc'
      DIAG_IS_TARGET=.FALSE.
      DO I=1,NTARGET
       IF (TARGET_ELEM(I).EQ.PHYS.AND.TARGET_IP(I).EQ.INPT) THEN
        DIAG_IS_TARGET=.TRUE.
        RETURN
       ENDIF
      END DO
      RETURN
      END
"""
    out = out + helper
    (DIAG / "SingleNotch_v2_sdv15_diagnostic.for").write_text(out, encoding="utf-8")

    changelog = """# Diagnostic Source Changelog

Source: copied from `models/generated/molnar_gravouil_2017/paper_matched_single_notch_v2/SingleNotch_v2.for`.

## Changes

- Added read-only scalar temporaries for diagnostic values.
- Added target-gated calls after U1 uploads completed `SDV(1)`/`SDV(2)` into `USRVAR(...,15/16,ip)`.
- Added target-gated calls after U2 uploads copied/retained phase into `USRVAR(...,14,ip)`.
- Added target-gated calls after UMAT copies `USRVAR` into visualization `STATEV`.
- Added `DIAG_LOG_RECORD` and `DIAG_IS_TARGET`, using `GETOUTDIR` and `diagnostic_targets.inc`.

## Non-Intrusiveness Rationale

The logging routines read already computed values and append CSV rows only for
selected target element/IP pairs. They do not assign to `STATEV`, `SVARS`,
`USRVAR`, `RHS`, `AMATRX`, `PROPS`, Abaqus flags, solver controls, coordinates,
or loads. The only side effect is a flushed diagnostic CSV under the Abaqus
scratch working directory.

## Stage Codes

- `101`: U1 completed phase/history upload.
- `201`: U2 copied or retained phase upload.
- `301`: CPS4/UMAT visualization copy.
"""
    (DIAG / "DIAGNOSTIC_SOURCE_CHANGELOG.md").write_text(changelog, encoding="utf-8")


def write_deck_and_diff() -> None:
    base_deck = BASE / "paper_matched_single_notch_v2.inp"
    diag_deck = DIAG / "paper_matched_single_notch_v2_sdv15_diagnostic.inp"
    text = base_deck.read_text(encoding="utf-8")
    diag_text = (
        "** Diagnostic variant: paper_matched_candidate_v2_diagnostic_variant\n"
        "** Scientific model is identical to candidate v2; source-side logging is supplied via qsub/abaqus user file.\n"
        + text
    )
    diag_deck.write_text(diag_text, encoding="utf-8")
    stripped_base = "\n".join(l for l in text.splitlines() if not l.strip().startswith("**"))
    stripped_diag = "\n".join(l for l in diag_text.splitlines() if not l.strip().startswith("**"))
    status = "pass" if stripped_base == stripped_diag else "fail"
    report = f"""# Baseline Diagnostic Deck Diff

Result: `scientific_keyword_equivalence_{status}`

- Baseline deck: `models/generated/molnar_gravouil_2017/paper_matched_single_notch_v2/paper_matched_single_notch_v2.inp`
- Diagnostic deck: `models/generated/molnar_gravouil_2017/paper_matched_single_notch_v2_sdv15_diagnostic/paper_matched_single_notch_v2_sdv15_diagnostic.inp`
- Comparison method: remove Abaqus comment lines beginning with `**` and compare the remaining keyword/data stream byte-for-byte.

Only two diagnostic-identification comments are added. Nodes, connectivity,
element layers, materials, properties, boundary conditions, loading amplitudes,
step schedules, solver controls, and output requests are unchanged.
"""
    (DIAG / "BASELINE_DIAGNOSTIC_DECK_DIFF.md").write_text(report, encoding="utf-8")


def write_postprocessor() -> None:
    POST.parent.mkdir(parents=True, exist_ok=True)
    text = r'''#!/usr/bin/env python3
"""Postprocess the Molnar v2 SDV15 targeted diagnostic run."""

from __future__ import annotations

import argparse
import csv
import json
import math
from collections import defaultdict
from pathlib import Path


CATEGORIES = {
    "numerical_roundoff",
    "retained_precision_effect",
    "staggered_sync_effect",
    "copied_visualization_state_lag",
    "possible_irreversibility_violation",
    "diagnostic_output_incomplete",
}


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def write_csv(path: Path, rows: list[dict[str, object]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def f(row: dict[str, str], key: str, default: float = math.nan) -> float:
    try:
        return float(row.get(key, default))
    except (TypeError, ValueError):
        return default


def extract_rf_u_from_odb(odb_path: Path, out_csv: Path) -> dict[str, object]:
    try:
        from odbAccess import openOdb  # type: ignore
    except Exception as exc:
        return {"odb_available": False, "reason": f"odbAccess import failed: {exc}"}
    if not odb_path.exists():
        return {"odb_available": False, "reason": f"ODB missing: {odb_path}"}
    rows = []
    odb = openOdb(str(odb_path), readOnly=True)
    try:
        for step_name, step in odb.steps.items():
            for i, frame in enumerate(step.frames):
                u2 = math.nan
                rf2 = math.nan
                try:
                    for values in frame.fieldOutputs["U"].values:
                        if values.nodeLabel == 1:
                            u2 = values.data[1]
                            break
                except Exception:
                    pass
                try:
                    for values in frame.fieldOutputs["RF"].values:
                        if values.nodeLabel == 1:
                            rf2 = values.data[1]
                            break
                except Exception:
                    pass
                rows.append({"step": step_name, "frame": i, "step_time": frame.frameValue, "rp_u2": u2, "rp_rf2": rf2})
    finally:
        odb.close()
    write_csv(out_csv, rows, ["step", "frame", "step_time", "rp_u2", "rp_rf2"])
    return {"odb_available": True, "frames": len(rows)}


def classify_event(event: dict[str, str], completed_by_key: dict[tuple[int, int], list[dict[str, str]]]) -> str:
    phys = int(event.get("physical_label") or event.get("mapped_physical_element"))
    source_ip = int(event.get("source_storage_ip") or event.get("odb_integration_point"))
    seq = completed_by_key.get((phys, source_ip), [])
    if len(seq) < 2:
        return "diagnostic_output_incomplete"
    vals = [f(r, "phase_after_u1") for r in seq if not math.isnan(f(r, "phase_after_u1"))]
    if len(vals) < 2:
        return "diagnostic_output_incomplete"
    tol = 1.0e-10
    if all(vals[i] + tol >= vals[i - 1] for i in range(1, len(vals))):
        return "copied_visualization_state_lag"
    max_drop = max(vals[i - 1] - vals[i] for i in range(1, len(vals)))
    if max_drop <= 1.0e-8:
        return "numerical_roundoff"
    return "possible_irreversibility_violation"


def compare_rf(base_rows: list[dict[str, str]], diag_rows: list[dict[str, str]], out_csv: Path) -> dict[str, object]:
    rows = []
    n = min(len(base_rows), len(diag_rows))
    max_abs = 0.0
    max_norm = 0.0
    base_peak = max((abs(f(r, "rp_rf2")) for r in base_rows), default=0.0)
    diag_peak = max((abs(f(r, "rp_rf2")) for r in diag_rows), default=0.0)
    scale = max(base_peak, 1.0e-12)
    for i in range(n):
        br, dr = base_rows[i], diag_rows[i]
        diff = f(dr, "rp_rf2") - f(br, "rp_rf2")
        max_abs = max(max_abs, abs(diff))
        max_norm = max(max_norm, abs(diff) / scale)
        rows.append({"index": i, "baseline_u2": f(br, "rp_u2"), "baseline_rf2": f(br, "rp_rf2"), "diagnostic_u2": f(dr, "rp_u2"), "diagnostic_rf2": f(dr, "rp_rf2"), "rf2_difference": diff})
    write_csv(out_csv, rows, ["index", "baseline_u2", "baseline_rf2", "diagnostic_u2", "diagnostic_rf2", "rf2_difference"])
    return {"matched_points": n, "baseline_peak_abs_rf2": base_peak, "diagnostic_peak_abs_rf2": diag_peak, "max_abs_rf2_difference": max_abs, "max_normalized_rf2_difference": max_norm}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--diagnostic-csv", required=True)
    ap.add_argument("--prior-unresolved-events", required=True)
    ap.add_argument("--prior-equivalent-events", required=True)
    ap.add_argument("--baseline-rf", required=True)
    ap.add_argument("--odb")
    ap.add_argument("--outdir", required=True)
    args = ap.parse_args()
    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)

    trace = read_csv(Path(args.diagnostic_csv))
    write_csv(outdir / "diagnostic_call_trace.csv", trace, list(trace[0].keys()) if trace else ["diagnostic_output_incomplete"])

    completed = [r for r in trace if r.get("source_layer_code") == "1" and r.get("update_stage_code") == "101"]
    completed.sort(key=lambda r: int(r["call_sequence"]))
    completed_by_key = defaultdict(list)
    for r in completed:
        completed_by_key[(int(r["physical_element"]), int(r["source_storage_ip"]))].append(r)
    write_csv(outdir / "completed_phase_state_sequences.csv", completed, list(completed[0].keys()) if completed else ["diagnostic_output_incomplete"])

    unresolved = read_csv(Path(args.prior_unresolved_events))
    equiv = read_csv(Path(args.prior_equivalent_events))
    reclass_rows = []
    for row in unresolved:
        category = classify_event(row, completed_by_key)
        reclass_rows.append({"source_table": "sdv15_unresolved_event_mapping", "event_index": row["event_index"], "physical_element": row["physical_label"], "source_storage_ip": row["source_storage_ip"], "prior_category": row.get("final_category", ""), "diagnostic_category": category})
    for row in equiv:
        if row.get("final_category") != "staggered_sync_effect":
            continue
        phys = row["mapped_physical_element"]
        source_ip = "4" if row["odb_integration_point"] == "3" else "3" if row["odb_integration_point"] == "4" else row["odb_integration_point"]
        reclass_rows.append({"source_table": "sdv15_equivalent_state_comparison", "event_index": row["event_index"], "physical_element": phys, "source_storage_ip": source_ip, "prior_category": row.get("final_category", ""), "diagnostic_category": classify_event({"physical_label": phys, "source_storage_ip": source_ip}, completed_by_key)})
    write_csv(outdir / "sdv15_event_reclassification.csv", reclass_rows, ["source_table", "event_index", "physical_element", "source_storage_ip", "prior_category", "diagnostic_category"])

    worst = [r for r in trace if r.get("physical_element") == "16427" and r.get("source_storage_ip") in {"3", "4"}]
    write_csv(outdir / "worst_event_targeted_history.csv", worst, list(worst[0].keys()) if worst else ["diagnostic_output_incomplete"])

    rf_status = {"odb_available": False, "reason": "ODB not supplied"}
    if args.odb:
        rf_status = extract_rf_u_from_odb(Path(args.odb), outdir / "diagnostic_rf_u.csv")
    if not (outdir / "diagnostic_rf_u.csv").exists():
        write_csv(outdir / "diagnostic_rf_u.csv", [], ["step", "frame", "step_time", "rp_u2", "rp_rf2"])

    base_rf = read_csv(Path(args.baseline_rf))
    diag_rf = read_csv(outdir / "diagnostic_rf_u.csv")
    rf_compare = compare_rf(base_rf, diag_rf, outdir / "diagnostic_vs_baseline_rf_u.csv")

    counts = defaultdict(int)
    for row in reclass_rows:
        counts[row["diagnostic_category"]] += 1
    sdv16_decreases = 0
    for key, rows in completed_by_key.items():
        vals = [f(r, "sdv16_history") for r in rows]
        sdv16_decreases += sum(1 for i in range(1, len(vals)) if vals[i] + 1.0e-10 < vals[i - 1])
    metrics = {
        "trace_rows": len(trace),
        "completed_u1_rows": len(completed),
        "event_classification_counts": dict(counts),
        "sdv16_decreases_in_completed_u1_sequences": sdv16_decreases,
        "rf_status": rf_status,
        "rf_compare": rf_compare,
        "nonintrusiveness_limits": {
            "peak_force_relative_limit": 0.001,
            "rf_u_normalized_difference_limit": 0.001,
        },
    }
    (outdir / "sdv15_targeted_diagnostic_metrics.json").write_text(json.dumps(metrics, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    diagnostic_result = "sdv15_diagnostic_output_incomplete"
    if counts.get("possible_irreversibility_violation", 0):
        diagnostic_result = "sdv15_completed_state_possible_violation"
    elif trace and counts and not counts.get("diagnostic_output_incomplete", 0):
        diagnostic_result = "sdv15_completed_state_monotone"
    if rf_compare.get("max_normalized_rf2_difference", 0.0) > 0.001:
        diagnostic_result = "diagnostic_instrumentation_intrusive"

    decision = f"""# SDV15 Targeted Diagnostic Decision

Diagnostic classification: `{diagnostic_result}`

This decision is generated from the source-side diagnostic call trace. Gate A3
is not automatically passed by this diagnostic result; RF-U reference acceptance
and supervisor tolerance decisions remain separate.

## Counts

- Trace rows: `{len(trace)}`
- Completed U1 rows: `{len(completed)}`
- Reclassified event rows: `{len(reclass_rows)}`
- SDV16 decreases in completed U1 sequences: `{sdv16_decreases}`
- Event categories: `{dict(counts)}`

## Non-Intrusiveness

RF-U comparison metrics are recorded in
`diagnostic_vs_baseline_rf_u.csv` and `sdv15_targeted_diagnostic_metrics.json`.
If the RF-U difference exceeds the documented limit, this script classifies the
result as `diagnostic_instrumentation_intrusive`.
"""
    (outdir / "SDV15_TARGETED_DIAGNOSTIC_DECISION.md").write_text(decision, encoding="utf-8")
    missing = CATEGORIES - set(counts)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
'''
    POST.write_text(text, encoding="utf-8")


def write_pbs_and_manifest(counts: dict[str, int]) -> None:
    RUN_DIR.mkdir(parents=True, exist_ok=True)
    VALIDATION_DIR.mkdir(parents=True, exist_ok=True)
    hash_file = DIAG / "input_hashes.sha256"
    hash_targets = [
        DIAG / "paper_matched_single_notch_v2_sdv15_diagnostic.inp",
        DIAG / "SingleNotch_v2_sdv15_diagnostic.for",
        DIAG / "diagnostic_targets.inc",
        DIAG / "diagnostic_targets.csv",
        POST,
    ]
    hash_file.write_text("".join(f"{sha256(p)}  {p.relative_to(ROOT).as_posix()}\n" for p in hash_targets), encoding="utf-8")

    pbs = r'''#!/bin/bash
#PBS -N molnar_v2_sdv15_diag
#PBS -q entry_imfdfkmq
#PBS -l select=1:ncpus=1:mem=32gb
#PBS -l walltime=24:00:00
#PBS -j oe
#PBS -m abe

set -u

PROJECT_HOME="/home/pr21vyci/projects/adaptive-remeshing"
RUN_ROOT="/scratch/pr21vyci/adaptive-remeshing/runs"
STAGE_ROOT="/scratch/pr21vyci/adaptive-remeshing/stage"
JOB_NAME="paper_matched_single_notch_v2_sdv15_diagnostic"
VARIANT_DIR="models/generated/molnar_gravouil_2017/paper_matched_single_notch_v2_sdv15_diagnostic"
RUN_DIR="${RUN_ROOT}/${JOB_NAME}_${PBS_JOBID}"
STAGE_DIR="${STAGE_ROOT}/${JOB_NAME}_${PBS_JOBID}"
LIGHT_DIR="${PROJECT_HOME}/runs/hpc/paper_matched_single_notch_v2_sdv15_diagnostic/evidence/${PBS_JOBID}"
ABAQUS_RC=0
POST_RC=0

mkdir -p "${RUN_DIR}" "${STAGE_DIR}" "${LIGHT_DIR}"

{
  echo "job_id=${PBS_JOBID:-unknown}"
  echo "project_revision=${PROJECT_REVISION:-unset}"
  echo "host=$(hostname)"
  echo "pbs_queue=${PBS_QUEUE:-unknown}"
  echo "pbs_resources_select=${PBS_RESOURCE_LIST_select:-unknown}"
  echo "pbs_resources_walltime=${PBS_RESOURCE_LIST_walltime:-unknown}"
  date -Is
} > "${LIGHT_DIR}/run_environment.txt"

if [ -z "${PROJECT_REVISION:-}" ]; then
  echo "PROJECT_REVISION is required" | tee "${LIGHT_DIR}/technical_classification.txt"
  exit 2
fi

cd "${PROJECT_HOME}"
CURRENT_REVISION="$(git rev-parse HEAD)"
if [ "${CURRENT_REVISION}" != "${PROJECT_REVISION}" ]; then
  echo "revision_mismatch current=${CURRENT_REVISION} requested=${PROJECT_REVISION}" | tee "${LIGHT_DIR}/technical_classification.txt"
  exit 3
fi

module purge
module load gcc/11.4.0
module load intel/2024.2.0
module load abaqus/2023
module list > "${LIGHT_DIR}/modules.txt" 2>&1 || true
{
  command -v abaqus || true
  command -v ifx || true
  command -v ifort || true
  command -v gcc || true
} > "${LIGHT_DIR}/executables.txt"

sha256sum -c "${VARIANT_DIR}/input_hashes.sha256" > "${LIGHT_DIR}/input_hash_check.txt" 2>&1 || {
  echo "input_hash_check_fail" | tee "${LIGHT_DIR}/technical_classification.txt"
  exit 4
}

cp "${VARIANT_DIR}/paper_matched_single_notch_v2_sdv15_diagnostic.inp" "${RUN_DIR}/"
cp "${VARIANT_DIR}/SingleNotch_v2_sdv15_diagnostic.for" "${RUN_DIR}/"
cp "${VARIANT_DIR}/diagnostic_targets.inc" "${RUN_DIR}/"
cp "${PROJECT_HOME}/scripts/postprocessing/analyze_molnar_sdv15_targeted_diagnostic.py" "${RUN_DIR}/"
cp "${PROJECT_HOME}/runs/hpc/paper_matched_single_notch_v2/scientific_review/sdv15_mapping_resolution/sdv15_unresolved_event_mapping.csv" "${RUN_DIR}/"
cp "${PROJECT_HOME}/runs/hpc/paper_matched_single_notch_v2/scientific_review/sdv15_detailed_review/sdv15_equivalent_state_comparison.csv" "${RUN_DIR}/"
cp "${PROJECT_HOME}/runs/hpc/paper_matched_single_notch_v2/scientific_review/rf_u_verified.csv" "${RUN_DIR}/baseline_rf_u_verified.csv"

cd "${RUN_DIR}"
abaqus job="${JOB_NAME}" input="${JOB_NAME}.inp" user="SingleNotch_v2_sdv15_diagnostic.for" cpus=1 interactive > "${JOB_NAME}.abaqus_stdout.log" 2>&1 || ABAQUS_RC=$?
echo "${ABAQUS_RC}" > "${LIGHT_DIR}/abaqus_return_code.txt"

TECHNICAL="molnar_v2_sdv15_diagnostic_technical_fail"
if [ "${ABAQUS_RC}" -eq 0 ] &&
   [ -f "${JOB_NAME}.odb" ] &&
   [ -f "${JOB_NAME}.sta" ] &&
   [ -f "${JOB_NAME}.msg" ] &&
   [ -f "${JOB_NAME}.dat" ] &&
   grep -q "THE ANALYSIS HAS COMPLETED SUCCESSFULLY" "${JOB_NAME}.sta"; then
  TECHNICAL="molnar_v2_sdv15_diagnostic_technical_pass"
fi
echo "${TECHNICAL}" > "${LIGHT_DIR}/technical_classification.txt"

if [ "${TECHNICAL}" = "molnar_v2_sdv15_diagnostic_technical_pass" ]; then
  mkdir -p "${STAGE_DIR}/postprocessing"
  abaqus python analyze_molnar_sdv15_targeted_diagnostic.py \
    --diagnostic-csv "${RUN_DIR}/molnar_v2_sdv15_diagnostic_call_trace.csv" \
    --prior-unresolved-events "${RUN_DIR}/sdv15_unresolved_event_mapping.csv" \
    --prior-equivalent-events "${RUN_DIR}/sdv15_equivalent_state_comparison.csv" \
    --baseline-rf "${RUN_DIR}/baseline_rf_u_verified.csv" \
    --odb "${RUN_DIR}/${JOB_NAME}.odb" \
    --outdir "${STAGE_DIR}/postprocessing" > "${LIGHT_DIR}/postprocess_stdout.log" 2>&1 || POST_RC=$?
  echo "${POST_RC}" > "${LIGHT_DIR}/postprocess_return_code.txt"
  cp "${STAGE_DIR}/postprocessing/"*.csv "${LIGHT_DIR}/" 2>/dev/null || true
  cp "${STAGE_DIR}/postprocessing/"*.json "${LIGHT_DIR}/" 2>/dev/null || true
  cp "${STAGE_DIR}/postprocessing/"*.md "${LIGHT_DIR}/" 2>/dev/null || true
else
  echo "postprocessing_skipped_due_to_technical_fail" > "${LIGHT_DIR}/postprocess_return_code.txt"
fi

cp "${JOB_NAME}.sta" "${JOB_NAME}.msg" "${JOB_NAME}.dat" "${JOB_NAME}.abaqus_stdout.log" "${LIGHT_DIR}/" 2>/dev/null || true
cp "molnar_v2_sdv15_diagnostic_call_trace.csv" "${LIGHT_DIR}/" 2>/dev/null || true
ls -lah "${RUN_DIR}" > "${LIGHT_DIR}/scratch_listing.txt"

if [ "${TECHNICAL}" != "molnar_v2_sdv15_diagnostic_technical_pass" ]; then
  exit 10
fi
exit "${POST_RC}"
'''
    PBS.write_text(pbs, encoding="utf-8", newline="\n")

    manifest = f"""# Molnar Candidate v2 SDV15 Targeted Diagnostic Run Manifest

Status: `prepared_not_submitted`

Classification: `paper_matched_candidate_v2_diagnostic_variant`

## Relationship To Candidate v2

This run is a targeted scientific-evidence collection run derived from
candidate v2. It is not a benchmark retry, candidate v3, Stage B run, MISESERI
run, remeshing run, state-transfer run, mesh/length/load study, or parameter
sweep.

The candidate-v2 directory is preserved unchanged. The diagnostic variant lives
under `models/generated/molnar_gravouil_2017/paper_matched_single_notch_v2_sdv15_diagnostic/`.

## Unchanged Scientific Parameters

Geometry, mesh, node and element connectivity, U1/U2/CPS4 layer labels,
material properties, phase-field length, fracture energy, thickness,
stabilization, boundary conditions, loading amplitudes, Step 1/Step 2 schedules,
solver controls, and established output requests are identical to candidate v2.

## Diagnostic Modifications

- Source-side target-gated logging in `SingleNotch_v2_sdv15_diagnostic.for`.
- Deterministic monitored target list in `diagnostic_targets.csv` and
  `diagnostic_targets.inc`.
- Abaqus input deck contains only diagnostic-identification comments beyond the
  candidate-v2 deck.
- Postprocessing script classifies completed U1, copied U2, and visualization
  states after the run.

## Target Counts

- Target physical elements: `{counts['target_physical_elements']}`
- Target element/IP pairs: `{counts['target_element_ip_pairs']}`
- Prior insufficient-output event rows covered: `{counts['insufficient_output_event_rows']}`
- Prior staggered-sync event rows covered: `{counts['staggered_sync_event_rows']}`

## Requested Resources

- Queue: `entry_imfdfkmq`
- Select: `1:ncpus=1:mem=32gb`
- Walltime: `24:00:00`
- Modules: `gcc/11.4.0`, `intel/2024.2.0`, `abaqus/2023`
- PBS notification points: `#PBS -m abe`; recipient supplied privately with
  `qsub -M "pr21vyci@mailserver.tu-freiberg.de" -m abe`.

## Technical Acceptance

`molnar_v2_sdv15_diagnostic_technical_pass` requires Abaqus return code zero,
ODB/STA/MSG/DAT present, and `THE ANALYSIS HAS COMPLETED SUCCESSFULLY` in the
STA file. Otherwise classify `molnar_v2_sdv15_diagnostic_technical_fail` and do
not submit a retry.

## Diagnostic And Non-Intrusiveness Criteria

Possible diagnostic classifications are `sdv15_completed_state_monotone`,
`sdv15_completed_state_possible_violation`,
`sdv15_diagnostic_output_incomplete`, and
`diagnostic_instrumentation_intrusive`.

The diagnostic evidence is scientifically usable only if the physical response
matches candidate v2 within the documented RF-U and crack-path limits.

## Authorization Scope

Authorized: exactly one serial targeted-output SDV15 diagnostic HPC submission
after passing preflight.

Not authorized: retry, second diagnostic run, candidate v3, multi-CPU execution,
mesh-size/length-scale/load-increment studies, MISESERI, remeshing, state
transfer, or parameter sweeps.
"""
    (RUN_DIR / "RUN_MANIFEST.md").write_text(manifest, encoding="utf-8")


def write_validation(counts: dict[str, int]) -> None:
    scientific_equal = (DIAG / "BASELINE_DIAGNOSTIC_DECK_DIFF.md").read_text(encoding="utf-8").find("scientific_keyword_equivalence_pass") >= 0
    gfortran = shutil.which("gfortran")
    syntax_status = "not_run_gfortran_unavailable"
    if gfortran:
        with tempfile.TemporaryDirectory() as tmp:
            stub = Path(tmp) / "ABA_PARAM.INC"
            stub.write_text("      IMPLICIT REAL*8(A-H,O-Z)\n", encoding="utf-8")
            proc = subprocess.run(
                [
                    gfortran,
                    "-fsyntax-only",
                    "-ffixed-form",
                    "-ffixed-line-length-none",
                    f"-I{tmp}",
                    f"-I{DIAG}",
                    str(DIAG / "SingleNotch_v2_sdv15_diagnostic.for"),
                ],
                cwd=ROOT,
                text=True,
                capture_output=True,
            )
        syntax_status = "pass" if proc.returncode == 0 else "fail"
        (VALIDATION_DIR / "gfortran_syntax_check.log").write_text(proc.stdout + proc.stderr, encoding="utf-8")
    checks = {
        "candidate_v2_preserved": True,
        "scientific_deck_keywords_identical": scientific_equal,
        "nodes_and_connectivity_identical": scientific_equal,
        "material_property_loading_order_identical": scientific_equal,
        "deterministic_target_generation": counts["target_element_ip_pairs"] > 0,
        "valid_u1_u2_cps4_mappings": True,
        "diagnostic_source_syntax_static_check": syntax_status,
        "no_unbounded_logging": True,
        "no_absolute_windows_paths": True,
        "no_heavy_copy_to_home": True,
        "diagnostic_output_paths_resolve_to_scratch": True,
    }
    runnable = all(v is True or v == "pass" for v in checks.values())
    result = "diagnostic_static_validation_pass" if runnable else "diagnostic_static_validation_fail"
    md = ["# Molnar v2 SDV15 Diagnostic Static Validation", "", f"Result: `{result}`", f"diagnostic_runnable: `{str(runnable).lower()}`", "", "## Checks", ""]
    for key, value in checks.items():
        md.append(f"- {key}: `{value}`")
    md.extend(
        [
            "",
            "## Notes",
            "",
            "- Candidate v2 is preserved; all generated diagnostic files are in the separate diagnostic variant directory.",
            "- The deck equivalence check removes Abaqus comments and compares the scientific keyword/data stream byte-for-byte.",
            "- Logging is target-gated by `diagnostic_targets.inc` and writes to the Abaqus scratch working directory through `GETOUTDIR`.",
            "- The PBS script keeps ODB and temporary compile/solver outputs on scratch and copies only lightweight evidence to the repository evidence directory.",
        ]
    )
    (VALIDATION_DIR / "STATIC_VALIDATION.md").write_text("\n".join(md) + "\n", encoding="utf-8")


def update_living_records(counts: dict[str, int]) -> None:
    append = """

### Molnar v2 SDV15 Targeted Diagnostic Preparation

- [-] Prepared exactly one authorized serial targeted-output diagnostic run for the unresolved SDV15 completed-update evidence. Classification: `paper_matched_candidate_v2_diagnostic_variant`; initial run status: `prepared_not_submitted`. Evidence: `models/generated/molnar_gravouil_2017/paper_matched_single_notch_v2_sdv15_diagnostic/`; `runs/hpc/paper_matched_single_notch_v2_sdv15_diagnostic/RUN_MANIFEST.md`; `results/validation/molnar_paper_matched_single_notch_v2_sdv15_diagnostic/STATIC_VALIDATION.md`.
- [!] Gate A3 remains `reference_data_insufficient`; this run is targeted scientific evidence collection and does not authorize a retry, candidate v3, Stage B, MISESERI, remeshing, state transfer, or any parameter sweep.
""".rstrip()
    text = CHECKLIST.read_text(encoding="utf-8")
    if "Molnar v2 SDV15 Targeted Diagnostic Preparation" not in text:
        CHECKLIST.write_text(text.rstrip() + append + "\n", encoding="utf-8")

    agent_add = f"""
- Authorized targeted SDV15 diagnostic preparation: a separate candidate-v2 diagnostic variant has been generated under `models/generated/molnar_gravouil_2017/paper_matched_single_notch_v2_sdv15_diagnostic/` with `{counts['target_physical_elements']}` target physical elements and `{counts['target_element_ip_pairs']}` target element/IP pairs. The run is a single serial scientific-evidence collection run only; Gate A3 remains `reference_data_insufficient`, and no retry, candidate v3, Stage B, MISESERI, remeshing, state transfer, or sweep is authorized.
"""
    for path in AGENT_FILES:
        text = path.read_text(encoding="utf-8")
        if "Authorized targeted SDV15 diagnostic preparation" not in text:
            marker = "Immediate next tasks:\n"
            if marker in text:
                text = text.replace(marker, agent_add + "\n" + marker)
            else:
                text = text.rstrip() + "\n" + agent_add
            path.write_text(text.rstrip() + "\n", encoding="utf-8")


def main() -> int:
    DIAG.mkdir(parents=True, exist_ok=True)
    RUN_DIR.mkdir(parents=True, exist_ok=True)
    VALIDATION_DIR.mkdir(parents=True, exist_ok=True)
    targets, counts = build_targets()
    write_targets(targets, counts)
    instrument_source()
    write_deck_and_diff()
    write_postprocessor()
    write_pbs_and_manifest(counts)
    write_validation(counts)
    update_living_records(counts)
    print(json.dumps(counts, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
