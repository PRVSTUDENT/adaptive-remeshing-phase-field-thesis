#!/bin/bash
# Login-node diagnostics for C2F-v2 mechanical mismatch. No full fracture resubmit.
set -euo pipefail
PROJECT_HOME="/home/pr21vyci/projects/adaptive-remeshing"
cd "${PROJECT_HOME}"
# optional: git pull if already updated by caller

DIAG="${PROJECT_HOME}/runs/hpc/stage_c2/diagnostics"
mkdir -p "${DIAG}"

module load gcc/11.4.0 >/dev/null 2>&1 || true
module load python/gcc/11.4.0/3.11.7 >/dev/null 2>&1 || true
PY=python3

H1_INP="${PROJECT_HOME}/models/generated/molnar_gravouil_2017/h_convergence_lc015/H1_h0025/H1_h0025.inp"
H1_FOR="${PROJECT_HOME}/models/generated/molnar_gravouil_2017/h_convergence_lc015/H1_h0025/H1_h0025.for"
R_INP="${PROJECT_HOME}/models/generated/molnar_gravouil_2017/unified_preprocessing/H0_refined_layered_v2/H0_refined_fullgen.inp"
R_FOR="${PROJECT_HOME}/models/generated/molnar_gravouil_2017/unified_preprocessing/H0_refined_layered_v2/H0_refined_fullgen.for"
ODB="/scratch/pr21vyci/adaptive-remeshing/runs/molnar_c2f_v2_refined_final_threads4_1376444.mmaster02/molnar_c2f_v2_refined_final_threads4.odb"
SCI="${PROJECT_HOME}/runs/hpc/stage_c2/recovery/c2f_v2_vs_h1/C2F_V2_VS_H1_STATUS.json"
FIELD="${PROJECT_HOME}/runs/hpc/stage_c2/recovery/c2f_v2_vs_h1/C2F_V2_FIELD_CHECK.json"
REMESH="${PROJECT_HOME}/runs/hpc/stage_c2/C2C_V2/C2C_V2_REMESH_MANIFEST.json"

echo "=== freeze failed iteration ==="
${PY} - <<PY
import json, hashlib
from pathlib import Path
from datetime import datetime, timezone

def sha(p):
    p=Path(p)
    if not p.is_file():
        return None
    h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda: f.read(1024*1024), b''):
            h.update(b)
    return h.hexdigest()

diag=Path("${DIAG}")
sci=json.loads(Path("${SCI}").read_text()) if Path("${SCI}").is_file() else {}
field=json.loads(Path("${FIELD}").read_text()) if Path("${FIELD}").is_file() else {}
rem=json.loads(Path("${REMESH}").read_text()) if Path("${REMESH}").is_file() else {}
freeze={
  "job_id": "1376444.mmaster02",
  "commit_sha_at_submission": "2d85bdcfd6ccc584ec34e9a0522693641b4a99e9",
  "classification": [
    "stage_c_pipeline_executable",
    "stage_c_scientific_validation_open",
    "c2f_v2_mechanical_equivalence_failed",
    "stage_c_technically_valid_response_deviation",
  ],
  "h1_remains_production_reference": True,
  "do_not_present_as_successful_adaptive_result": True,
  "preserve_paths": {
    "c2c_v2_mesh": "runs/hpc/stage_c2/C2C_V2",
    "c2c_v2_deck": "models/generated/.../H0_refined_layered_v2",
    "c2e_v2": "scratch .../molnar_c2e_v2_integrity_threads4_1376443.mmaster02",
    "c2f_v2_odb": str(Path("${ODB}")),
    "c2f_v2_rfu": "runs/hpc/stage_c2/recovery/c2f_v2_vs_h1",
  },
  "hashes": {
    "deck_sha256": sha("${R_INP}"),
    "fortran_sha256": sha("${R_FOR}"),
    "odb_sha256": sha("${ODB}"),
    "h1_deck_sha256": sha("${H1_INP}"),
  },
  "mesh_statistics": rem,
  "rf_u_metrics": sci.get("metrics"),
  "sdv15": field.get("sdv15"),
  "resources": {"walltime_s": 924, "cputime_s": 2727, "mem_kb": 598916, "cpus": 4, "mp_mode": "threads"},
  "key_observation": {
    "K_C2F_v2_kN_per_mm": sci.get("metrics", {}).get("cand_initial_stiffness"),
    "K_H1_kN_per_mm": sci.get("metrics", {}).get("ref_initial_stiffness"),
    "stiffness_error_appears_before_fracture": True,
  },
  "frozen_at_utc": datetime.now(timezone.utc).isoformat(),
}
(diag/"C2F_V2_FAILED_ITERATION_FREEZE.json").write_text(json.dumps(freeze, indent=2, sort_keys=True)+"\n")
md=[
"# C2F-v2 failed iteration freeze",
"",
"## Classification",
"",
"- `stage_c_pipeline_executable`",
"- `stage_c_scientific_validation_open`",
"- `c2f_v2_mechanical_equivalence_failed`",
"",
"**H1 remains the production/report reference.**",
"",
"Do **not** present C2F-v2 as a successful adaptive-remeshing scientific result.",
"",
"## Identity",
"",
"| Item | Value |",
"| --- | --- |",
"| Job | 1376444.mmaster02 |",
"| Submission commit | 2d85bdcfd6ccc584ec34e9a0522693641b4a99e9 |",
"| Deck SHA-256 | %s |" % freeze["hashes"]["deck_sha256"],
"| Fortran SHA-256 | %s |" % freeze["hashes"]["fortran_sha256"],
"| ODB SHA-256 | %s |" % freeze["hashes"]["odb_sha256"],
"",
"## RF-U metrics vs H1",
"",
"```json",
json.dumps(sci.get("metrics"), indent=2),
"```",
"",
"## SDV15",
"",
"```json",
json.dumps(field.get("sdv15"), indent=2),
"```",
"",
"## Resources",
"",
"walltime 924 s, cputime 2727 s, mem ~599 MB, threads=4",
"",
"All listed paths are **failed-iteration evidence** and must not be overwritten.",
"",
]
(diag/"C2F_V2_FAILED_ITERATION_REVIEW.md").write_text("\n".join(md)+"\n")
print("freeze_ok")
PY

echo "=== deck audit H1 vs C2F-v2 ==="
${PY} scripts/validation/compare_molnar_layered_decks.py \
  --deck-a "${H1_INP}" \
  --deck-b "${R_INP}" \
  --for-a "${H1_FOR}" \
  --for-b "${R_FOR}" \
  --name-a H1 \
  --name-b C2F_v2 \
  --out-dir "${DIAG}"

echo "=== rebuild C2C-v3 physical mesh with y=0 notch fix (offline) ==="
C2B="${PROJECT_HOME}/runs/hpc/stage_c2/C2B_REFINED_MESH"
V3="${PROJECT_HOME}/runs/hpc/stage_c2/C2C_V3_notchfix"
REMESH_OUT="${V3}/refined_physical_local"
LAYERED_OUT="${PROJECT_HOME}/models/generated/molnar_gravouil_2017/unified_preprocessing/H0_refined_layered_v3_notchfix"
mkdir -p "${REMESH_OUT}" "${V3}"
${PY} scripts/remeshing/build_refined_mesh_from_miseseri.py \
  --csv "${C2B}/C2A_MISESERI_ELEMENT_DATA.csv" \
  --config configs/remeshing/miseseri_h0_to_h1_initial.json \
  --out "${REMESH_OUT}" | tee "${V3}/remesh_stdout.log"
cp -f "${REMESH_OUT}/remeshing_rule_manifest.json" "${V3}/C2C_V3_REMESH_MANIFEST.json"

# verify notch in CSV
${PY} - <<PY
from pathlib import Path
from collections import Counter
p=Path("${REMESH_OUT}/refined_mesh_nodes.csv")
ys=[]; xs_notch=[]
for line in p.read_text().splitlines()[1:]:
    _,x,y=line.split(',')[:3]
    x=float(x); y=float(y)
    ys.append(y)
    if abs(y)<1e-12 and x<0:
        xs_notch.append(round(x,10))
c=Counter(xs_notch)
print('has_y0', any(abs(y)<1e-12 for y in ys))
print('notch_line_nodes', len(xs_notch), 'unique_x', len(c), 'doubled', sum(1 for v in c.values() if v>=2))
assert any(abs(y)<1e-12 for y in ys), 'y=0 missing'
assert sum(1 for v in c.values() if v>=2) > 0, 'notch not split'
print('notch_fix_mesh_ok')
PY

echo "=== rebuild layered deck v3 ==="
mkdir -p "${LAYERED_OUT}"
${PY} scripts/preprocessing/build_molnar_unified_deck.py \
  --config configs/preprocessing/molnar_h0_h1_unified.yaml \
  --role-name H0_refined \
  --output-profile fracture_baseline \
  --from-nodes-csv "${REMESH_OUT}/refined_mesh_nodes.csv" \
  --from-elems-csv "${REMESH_OUT}/refined_mesh_elements.csv" \
  --out "${LAYERED_OUT}" | tee "${V3}/rebuild_stdout.log"
DECK=$(ls "${LAYERED_OUT}"/*fullgen.inp | head -n1)
FOR=$(ls "${LAYERED_OUT}"/*fullgen.for | head -n1)
echo "DECK_V3=${DECK}"
printf '%s\n' "${DECK}" > runs/hpc/stage_c2/C2C_V3_DECK_PATH.txt
printf '%s\n' "${FOR}" > runs/hpc/stage_c2/C2C_V3_FOR_PATH.txt

${PY} scripts/validation/validate_molnar_unified_deck.py \
  --config configs/preprocessing/molnar_h0_h1_unified.yaml \
  --deck "${DECK}" \
  --fortran "${FOR}" \
  --role H0_refined \
  --out-dir "${V3}/static_validation" | tee "${V3}/validate_stdout.log"

# re-audit v3 vs H1
${PY} scripts/validation/compare_molnar_layered_decks.py \
  --deck-a "${H1_INP}" \
  --deck-b "${DECK}" \
  --for-a "${H1_FOR}" \
  --for-b "${FOR}" \
  --name-a H1 \
  --name-b C2C_V3_notchfix \
  --out-dir "${DIAG}/v3_notchfix"

echo "=== diagnostic status json ==="
${PY} - <<'PY'
import json
from pathlib import Path
from datetime import datetime, timezone
diag=Path('/home/pr21vyci/projects/adaptive-remeshing/runs/hpc/stage_c2/diagnostics')
audit=json.loads((diag/'H1_VS_C2F_V2_DECK_AUDIT.json').read_text())
v3=json.loads((diag/'v3_notchfix'/'H1_VS_C2F_V2_DECK_AUDIT.json').read_text())
status={
  "stage": "Stage_C_mechanical_equivalence_diagnostic",
  "priority_order": [
    "deck_property_audit",
    "load_carrying_layer_audit",
    "bc_audit",
    "fortran_layer_index_audit",
    "tiny_elastic_probe",
    "phase_field_patch",
    "correct_demonstrated_defect",
    "repeat_tiny_probe",
    "one_full_c2f_v3",
  ],
  "hypotheses": [
    {
      "id": "H1_cps4_double_stiffness",
      "hypothesis": "CPS4 facsimile carried full continuum E in addition to U2 UEL",
      "evidence_for": [],
      "evidence_against": [
        "UMAT residual_stiffness = 1e-11 matches H1 on C2F-v2 deck",
        "U2 E=210, k=1e-7 matches H1",
      ],
      "test": "property parse of *User Material / *Uel property",
      "result": "REJECTED",
      "decision": "do not change residual umat policy",
    },
    {
      "id": "H2_missing_notch_split",
      "hypothesis": "Refined mesh lacked exact y=0 so notch free faces never formed; continuous plate",
      "evidence_for": [
        "C2F-v2: has_exact_y0=false, notch_split_present=false, notch_line_nodes=0",
        "H1: has_exact_y0=true, notch doubled x-stations=32",
        "K_C2F/K_H1 ~ 1.72 and monotone RF without softening",
        "SDV15 nearly uniform ~0.059 (no localization)",
      ],
      "evidence_against": [],
      "test": "geometry audit of part nodes on y=0",
      "result": "CONFIRMED",
      "decision": "force-include y=0 in remesh axis builder; rebuild C2C-v3 offline",
      "files_changed": [
        "scripts/remeshing/build_refined_mesh_from_miseseri.py",
        "scripts/preprocessing/build_molnar_unified_deck.py (notch nset reconstruction)",
      ],
    },
  ],
  "c2f_v2_primary_finding": audit.get("primary_finding"),
  "c2c_v3_notch_split_present": v3["deck_b"]["geometry"]["notch_split_present"],
  "c2c_v3_has_exact_y0": v3["deck_b"]["geometry"]["has_exact_y0"],
  "c2c_v3_n_physical": v3["deck_b"]["layers"]["n_physical_u1"],
  "remeshing_params_changed": False,
  "relative_MISESERI_threshold_frozen": 0.05,
  "next_required": "tiny elastic probe D1: |K_refined-K_H1|/K_H1 <= 1% before any full C2F-v3",
  "full_c2f_v3_authorized": False,
  "written_at_utc": datetime.now(timezone.utc).isoformat(),
}
(diag/'DIAGNOSTIC_STATUS.json').write_text(json.dumps(status, indent=2, sort_keys=True)+'\n')
print(json.dumps({
  'v2_notch': audit['deck_b']['geometry']['notch_split_present'],
  'v3_notch': v3['deck_b']['geometry']['notch_split_present'],
  'v3_n': v3['deck_b']['layers']['n_physical_u1'],
}, indent=2))
PY

echo "DIAGNOSTICS_DONE"
