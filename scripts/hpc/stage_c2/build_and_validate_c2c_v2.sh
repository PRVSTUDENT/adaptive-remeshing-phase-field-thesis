#!/bin/bash
# Offline C2C-v2: corrected local remesh + layered rebuild + static validation.
# Does NOT overwrite the 160400-element failed-design mesh.
# Does NOT submit PBS.
set -euo pipefail

PROJECT_HOME="/home/pr21vyci/projects/adaptive-remeshing"
C2B="${PROJECT_HOME}/runs/hpc/stage_c2/C2B_REFINED_MESH"
# Preserve original over-refined products under C2B; v2 remesh goes elsewhere
V2_ROOT="${PROJECT_HOME}/runs/hpc/stage_c2/C2C_V2"
REMESH_OUT="${V2_ROOT}/refined_physical_local"
LAYERED_OUT="${PROJECT_HOME}/models/generated/molnar_gravouil_2017/unified_preprocessing/H0_refined_layered_v2"
CHAIN_STATE_DIR="${PROJECT_HOME}/runs/hpc/stage_c2/chain_state"
CONFIG="${PROJECT_HOME}/configs/remeshing/miseseri_h0_to_h1_initial.json"
CSV="${C2B}/C2A_MISESERI_ELEMENT_DATA.csv"

cd "${PROJECT_HOME}"
test -f "${CSV}"
test -f "${CONFIG}"
mkdir -p "${REMESH_OUT}" "${V2_ROOT}" "${CHAIN_STATE_DIR}"

module load gcc/11.4.0 >/dev/null 2>&1 || true
module load python/gcc/11.4.0/3.11.7 >/dev/null 2>&1 || true
PY=python3
echo "using_python=$(command -v ${PY}) $(${PY} --version 2>&1)"
${PY} -c "import yaml; print('yaml_ok')"

echo "=== Part A: corrected local remesh ==="
${PY} scripts/remeshing/build_refined_mesh_from_miseseri.py \
  --csv "${CSV}" \
  --config "${CONFIG}" \
  --out "${REMESH_OUT}" | tee "${V2_ROOT}/remesh_stdout.log"

test -f "${REMESH_OUT}/remeshing_rule_manifest.json"
test -f "${REMESH_OUT}/refined_mesh_nodes.csv"
test -f "${REMESH_OUT}/refined_mesh_elements.csv"
cp -f "${REMESH_OUT}/remeshing_rule_manifest.json" "${V2_ROOT}/C2C_V2_REMESH_MANIFEST.json"

N_ELEM=$(${PY} -c "import json; print(json.load(open('${REMESH_OUT}/remeshing_rule_manifest.json'))['n_elements'])")
echo "n_elements_v2=${N_ELEM}"
if [ "${N_ELEM}" -ge 160400 ]; then
  echo "C2C_V2 still globally refined — refuse" >&2
  exit 14
fi

echo "=== Part B: rebuild layered UEL deck ==="
mkdir -p "${LAYERED_OUT}"
# Ensure baseline present
BASE_INP="${PROJECT_HOME}/models/baseline_original/molnar_gravouil_2017/02_Single_Notch_Tension/SingleNotch.inp"
BASE_FOR="${PROJECT_HOME}/models/baseline_original/molnar_gravouil_2017/02_Single_Notch_Tension/SingleNotch.for"
test -f "${BASE_INP}" && test -f "${BASE_FOR}"

${PY} scripts/preprocessing/build_molnar_unified_deck.py \
  --config configs/preprocessing/molnar_h0_h1_unified.yaml \
  --role-name H0_refined \
  --output-profile fracture_baseline \
  --from-nodes-csv "${REMESH_OUT}/refined_mesh_nodes.csv" \
  --from-elems-csv "${REMESH_OUT}/refined_mesh_elements.csv" \
  --out "${LAYERED_OUT}" | tee "${V2_ROOT}/rebuild_stdout.log"

DECK=$(ls "${LAYERED_OUT}"/*fullgen.inp "${LAYERED_OUT}"/*.inp 2>/dev/null | head -n1)
FOR=$(ls "${LAYERED_OUT}"/*fullgen.for "${LAYERED_OUT}"/*.for 2>/dev/null | head -n1)
test -f "${DECK}" && test -f "${FOR}"
echo "DECK=${DECK}"
echo "FOR=${FOR}"

if [ -f "${LAYERED_OUT}/generation_manifest.json" ]; then
  cp -f "${LAYERED_OUT}/generation_manifest.json" "${V2_ROOT}/C2C_V2_LAYER_MAPPING.json"
elif [ -f "${LAYERED_OUT}/layer_mapping.csv" ]; then
  ${PY} - <<PY
import json
from pathlib import Path
out = Path("${V2_ROOT}/C2C_V2_LAYER_MAPPING.json")
out.write_text(json.dumps({
  "layer_mapping_csv": "${LAYERED_OUT}/layer_mapping.csv",
  "deck": "${DECK}",
  "fortran": "${FOR}",
}, indent=2) + "\n")
PY
fi
# Prefer generation_manifest as the rich mapping record
if [ -f "${LAYERED_OUT}/generation_manifest.json" ]; then
  cp -f "${LAYERED_OUT}/generation_manifest.json" "${V2_ROOT}/C2C_V2_LAYER_MAPPING.json"
fi

echo "=== Part C: static validation H0_refined ==="
${PY} scripts/validation/validate_molnar_unified_deck.py \
  --config configs/preprocessing/molnar_h0_h1_unified.yaml \
  --deck "${DECK}" \
  --fortran "${FOR}" \
  --role H0_refined \
  --out-dir "${V2_ROOT}/static_validation" | tee "${V2_ROOT}/validate_stdout.log"
cp -f "${V2_ROOT}/static_validation/STATIC_VALIDATION.json" "${V2_ROOT}/C2C_V2_VALIDATION_REPORT.json"
(cd "${LAYERED_OUT}" && sha256sum -c input_hashes.sha256) | tee "${V2_ROOT}/input_hash_check.txt"

echo "=== Part D: adaptive efficiency report ==="
${PY} - <<'PY'
import json
from pathlib import Path
from datetime import datetime, timezone

v2 = Path("/home/pr21vyci/projects/adaptive-remeshing/runs/hpc/stage_c2/C2C_V2")
rem = json.loads((v2 / "C2C_V2_REMESH_MANIFEST.json").read_text())
val = json.loads((v2 / "C2C_V2_VALIDATION_REPORT.json").read_text())
old_path = Path("/home/pr21vyci/projects/adaptive-remeshing/runs/hpc/stage_c2/C2B_REFINED_MESH/remeshing_rule_manifest.json")
old = json.loads(old_path.read_text()) if old_path.is_file() else {}

n = rem["n_elements"]
H0, H1, H2 = 3930, 12064, 33852
guards = rem.get("guards", {})
static_pass = val.get("status") == "pass"
eff_pass = (
    rem.get("status") == "pass"
    and static_pass
    and n < 160400
    and guards.get("far_field_coarse_region_retained", False)
    and guards.get("refined_region_spatially_localized", False)
    and guards.get("minimum_size_reached_near_notch", False)
)

status = {
    "stage": "C2C_V2",
    "technical_rebuild": "pass" if static_pass else "fail",
    "adaptive_efficiency": "pass" if eff_pass else "fail",
    "classification": "locally_refined_miseseri_offline" if eff_pass else "refined_mesh_efficiency_fail",
    "C2E_release": bool(eff_pass),
    "C2F_release": bool(eff_pass),
    "n_physical": n,
    "n_layered": n * 3,
    "ratios": rem.get("ratios"),
    "corridor_h": rem.get("corridor_h"),
    "global_h": rem.get("global_h"),
    "refined_zone": rem.get("refined_zone"),
    "marking_rule": rem.get("sizing", {}).get("marking_rule"),
    "prior_over_refined_n_physical": old.get("n_elements", 160400),
    "static_validation": val.get("status"),
    "failed_static_checks": val.get("failed_checks"),
    "guards": guards,
    "generated_at_utc": datetime.now(timezone.utc).isoformat(),
}
(v2 / "C2C_V2_ADAPTIVE_EFFICIENCY_STATUS.json").write_text(
    json.dumps(status, indent=2, sort_keys=True) + "\n"
)

md = []
md.append("# C2C-v2 Adaptive Efficiency Report")
md.append("")
md.append("## Element counts")
md.append("")
md.append("| Mesh | Physical elements | vs H1 |")
md.append("| --- | ---: | ---: |")
md.append("| H0 | 3930 | 0.33× |")
md.append("| H1 | 12064 | 1.00× |")
md.append("| H2-PUB | 33852 | 2.81× |")
md.append("| C2C v1 (failed design) | %s | %.2f× |" % (old.get("n_elements", 160400), float(old.get("n_elements", 160400)) / H1))
md.append("| **C2C-v2** | **%d** | **%.2f×** |" % (n, n / float(H1)))
md.append("")
md.append("## Marking rule")
md.append("")
md.append("- **Corrected:** `%s`" % rem.get("sizing", {}).get("marking_formula"))
md.append("- **Legacy incorrect:** raw `MISESERI > errorTarget` (absolute 0.05 vs field max ~1390)")
md.append("- max_MISESERI: %s" % rem.get("sizing", {}).get("max_MISESERI"))
md.append("- absolute_equivalent_threshold: %s" % rem.get("sizing", {}).get("absolute_equivalent_threshold"))
md.append("- fraction_marked (relative, raw): %s" % rem.get("sizing", {}).get("fraction_marked"))
md.append("- fraction_marked (after notch component): %s" % rem.get("sizing", {}).get("fraction_marked_after_component"))
md.append("")
md.append("## Size statistics")
md.append("")
md.append("- refined zone: `%s`" % json.dumps(rem.get("refined_zone")))
md.append("- corridor h: `%s`" % json.dumps(rem.get("corridor_h")))
md.append("- global h: `%s`" % json.dumps(rem.get("global_h")))
md.append("")
md.append("## Guards")
md.append("")
for k, v in sorted(guards.items()):
    md.append("- `%s`: **%s**" % (k, v))
md.append("")
md.append("## Static validation: `%s`" % val.get("status"))
md.append("")
md.append("## Release: C2E/C2F = **%s**" % ("yes" if eff_pass else "no"))
md.append("")
(v2 / "C2C_V2_ADAPTIVE_EFFICIENCY_REPORT.md").write_text("\n".join(md) + "\n")

chain = Path("/home/pr21vyci/projects/adaptive-remeshing/runs/hpc/stage_c2/chain_state")
if eff_pass:
    (chain / "C2C_V2.ok").write_text("")
print(json.dumps({"eff_pass": eff_pass, "n_physical": n, "static": val.get("status")}, indent=2))
if not eff_pass:
    raise SystemExit("C2C_V2_EFFICIENCY_OR_STATIC_FAIL")
PY

# Write deck paths with shell (reliable)
printf '%s\n' "${DECK}" > "${PROJECT_HOME}/runs/hpc/stage_c2/C2C_V2_DECK_PATH.txt"
printf '%s\n' "${FOR}" > "${PROJECT_HOME}/runs/hpc/stage_c2/C2C_V2_FOR_PATH.txt"
printf '%s\n' "${LAYERED_OUT}" > "${PROJECT_HOME}/runs/hpc/stage_c2/C2C_V2_LAYERED_DIR.txt"
printf '%s\n' "${REMESH_OUT}" > "${PROJECT_HOME}/runs/hpc/stage_c2/C2C_V2_REMESH_DIR.txt"

# Fix marker if efficiency python already required it
if [ -f "${V2_ROOT}/C2C_V2_ADAPTIVE_EFFICIENCY_STATUS.json" ]; then
  ${PY} - <<PY
import json
from pathlib import Path
s=json.loads(Path("${V2_ROOT}/C2C_V2_ADAPTIVE_EFFICIENCY_STATUS.json").read_text())
ok=Path("${CHAIN_STATE_DIR}/C2C_V2.ok")
if s.get("C2E_release"):
    ok.write_text("")
    print("C2C_V2.ok ensured")
else:
    if ok.exists():
        ok.unlink()
    raise SystemExit("no_release")
PY
fi

echo "C2C_V2_DONE n_elements=${N_ELEM}"
