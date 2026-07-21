#!/bin/bash
# Linux-only: verify frozen C2B products, then write C2B.ok under chain_state.
# Never invent markers without checks. Do not run from Windows PowerShell as the
# sole verification path.
set -euo pipefail

PROJECT_HOME="${PROJECT_HOME:-/home/pr21vyci/projects/adaptive-remeshing}"
C2B_OUTPUT_DIR="${C2B_OUTPUT_DIR:-${PROJECT_HOME}/runs/hpc/stage_c2/C2B_REFINED_MESH}"
CHAIN_STATE_DIR="${CHAIN_STATE_DIR:-${PROJECT_HOME}/runs/hpc/stage_c2/chain_state}"
OUT_JSON="${PROJECT_HOME}/runs/hpc/stage_c2/recovery/C2B_REUSE_VERIFICATION.json"

mkdir -p "${CHAIN_STATE_DIR}" "$(dirname "${OUT_JSON}")"

test -d "${C2B_OUTPUT_DIR}"
test -f "${C2B_OUTPUT_DIR}/C2B_FIELD_SUMMARY.json"
test -f "${C2B_OUTPUT_DIR}/C2B_GATE_REPORT.md"
test -f "${C2B_OUTPUT_DIR}/refined_physical.inp"
test -f "${C2B_OUTPUT_DIR}/refined_mesh_nodes.csv"
test -f "${C2B_OUTPUT_DIR}/refined_mesh_elements.csv"
test -f "${C2B_OUTPUT_DIR}/remeshing_rule_manifest.json"
test -f "${C2B_OUTPUT_DIR}/C2A_MISESERI_ELEMENT_DATA.csv"

module load gcc/11.4.0 >/dev/null 2>&1 || true
module load python/gcc/11.4.0/3.11.7 >/dev/null 2>&1 || true
PY=python3

${PY} - <<PY
import json
import hashlib
from pathlib import Path
from datetime import datetime, timezone

c2b = Path("${C2B_OUTPUT_DIR}")
out = Path("${OUT_JSON}")

def sha256(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()

summary = json.loads((c2b / "C2B_FIELD_SUMMARY.json").read_text())
manifest = json.loads((c2b / "remeshing_rule_manifest.json").read_text())
cls = summary.get("classification") or summary.get("scientific_classification")
assert cls == "miseseri_preanalysis_suitable_for_remeshing", cls
assert summary.get("gate_pass") is not False
assert manifest.get("status") == "pass", manifest
rule = manifest.get("rule") or {}
assert rule.get("errorTarget") == 0.05
assert rule.get("refinementFactor") == 2.0
assert rule.get("minElementSize_mm") == 0.0025
assert rule.get("maxElementSize_mm") == 0.025
assert rule.get("passes") == 1
assert rule.get("coarsening") is False

files = [
    "C2B_FIELD_SUMMARY.json",
    "C2B_GATE_REPORT.md",
    "refined_physical.inp",
    "refined_mesh_nodes.csv",
    "refined_mesh_elements.csv",
    "remeshing_rule_manifest.json",
    "C2A_MISESERI_ELEMENT_DATA.csv",
]
hashes = {name: sha256(c2b / name) for name in files}

payload = {
    "stage": "C2B",
    "classification": "reuse_verified",
    "job_id_source": "1376304.mmaster02",
    "c2a_job_reused": "1376298.mmaster02",
    "output_dir": str(c2b),
    "scientific_classification": cls,
    "gate_pass": summary.get("gate_pass"),
    "max_MISESERI": summary.get("checks", {}).get("max_MISESERI"),
    "max_von_mises_MPa": summary.get("checks", {}).get("max_von_mises_MPa"),
    "n_elements_refined": manifest.get("n_elements"),
    "n_nodes_refined": manifest.get("n_nodes"),
    "remeshing_rule": rule,
    "manifest_status": manifest.get("status"),
    "file_sha256": hashes,
    "c2b_rerun": False,
    "c2a_rerun": False,
    "verified_at_utc": datetime.now(timezone.utc).isoformat(),
    "marker_policy": "C2B.ok written only after this automated verification",
}
out.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
print("C2B_REUSE_VERIFIED", cls, "n_elements=", manifest.get("n_elements"))
print("wrote", out)
PY

# Marker only after automated verification succeeded
: > "${CHAIN_STATE_DIR}/C2B.ok"
# Clear downstream markers so recovery starts cleanly at C2C
rm -f "${CHAIN_STATE_DIR}/C2C.ok" "${CHAIN_STATE_DIR}/C2D.ok" \
      "${CHAIN_STATE_DIR}/C2E.ok" "${CHAIN_STATE_DIR}/C2F.ok"
echo "wrote ${CHAIN_STATE_DIR}/C2B.ok"
echo "cleared C2C-C2F markers"
