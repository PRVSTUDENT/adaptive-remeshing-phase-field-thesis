#!/bin/bash
# Postprocess completed C2F-v2 ODB vs frozen H1. No qsub.
set -euo pipefail
PROJECT_HOME="/home/pr21vyci/projects/adaptive-remeshing"
ODB="/scratch/pr21vyci/adaptive-remeshing/runs/molnar_c2f_v2_refined_final_threads4_1376444.mmaster02/molnar_c2f_v2_refined_final_threads4.odb"
H1_CSV="${PROJECT_HOME}/results/processed/molnar_lc015_h_convergence/source_csv/H1_RF2_U2.csv"
OUT="${PROJECT_HOME}/runs/hpc/stage_c2/recovery/c2f_v2_vs_h1"
CHAIN="${PROJECT_HOME}/runs/hpc/stage_c2/chain_state"

cd "${PROJECT_HOME}"
test -f "${ODB}"
test -f "${H1_CSV}"
test -f "${CHAIN}/C2F_V2.ok"
mkdir -p "${OUT}"

module purge >/dev/null 2>&1 || true
module load gcc/11.4.0 >/dev/null 2>&1 || true
module load intel/2024.2.0 >/dev/null 2>&1 || true
module load abaqus/2023 >/dev/null 2>&1 || true
module load python/gcc/11.4.0/3.11.7 >/dev/null 2>&1 || true

echo "=== extract RF-U from C2F ODB ==="
abaqus python scripts/postprocessing/extract_rfu_from_odb.py \
  --odb "${ODB}" \
  --out "${OUT}/C2F_V2_RF_U.csv" \
  > "${OUT}/extract_stdout.log" 2>&1
wc -l "${OUT}/C2F_V2_RF_U.csv"

echo "=== light SDV finiteness check (abaqus python) ==="
abaqus python - <<'PY' > "${OUT}/sdv_check_stdout.log" 2>&1 || true
from odbAccess import openOdb
import json
odb = openOdb(path="/scratch/pr21vyci/adaptive-remeshing/runs/molnar_c2f_v2_refined_final_threads4_1376444.mmaster02/molnar_c2f_v2_refined_final_threads4.odb", readOnly=True)
step = list(odb.steps.values())[-1]
fr = step.frames[-1]
out = {"frame": fr.frameId, "step": step.name, "fields": list(fr.fieldOutputs.keys())}
# RF/U presence
out["has_U"] = "U" in fr.fieldOutputs
out["has_RF"] = "RF" in fr.fieldOutputs
# SDV if present
sdv_ok = True
sdv_stats = {}
if "SDV" in fr.fieldOutputs:
    vals = fr.fieldOutputs["SDV"].values
    # sample first component where available
    bad = 0
    n = 0
    mn = 1e99
    mx = -1e99
    for v in vals:
        data = v.data
        if hasattr(data, "__len__"):
            x = float(data[0])
        else:
            x = float(data)
        n += 1
        if x != x or abs(x) == float("inf"):
            bad += 1
        else:
            if x < mn: mn = x
            if x > mx: mx = x
    sdv_ok = bad == 0 and n > 0
    sdv_stats = {"n": n, "bad": bad, "min0": mn if n else None, "max0": mx if n else None}
out["sdv_finite"] = sdv_ok
out["sdv_stats"] = sdv_stats
odb.close()
open("/home/pr21vyci/projects/adaptive-remeshing/runs/hpc/stage_c2/recovery/c2f_v2_vs_h1/C2F_V2_FIELD_CHECK.json","w").write(json.dumps(out, indent=2, sort_keys=True)+"\n")
print(out)
PY

echo "=== compare to H1 ==="
python3 scripts/postprocessing/compare_refined_to_h1.py \
  --ref-csv "${H1_CSV}" \
  --cand-csv "${OUT}/C2F_V2_RF_U.csv" \
  --out-json "${OUT}/C2F_V2_VS_H1_STATUS.json" \
  --out-csv "${OUT}/C2F_V2_VS_H1_RF_U_COMPARISON.csv" \
  --out-md "${OUT}/C2F_V2_VS_H1_REPORT.md" \
  --n-physical 10088 \
  --n-physical-h1 12064 \
  --walltime-s 924 \
  --cputime-s 2727 \
  --mem-kb 598916 \
  | tee "${OUT}/compare_stdout.log"

# Merge field check + remesh + classification
python3 - <<'PY'
import json
from pathlib import Path
from datetime import datetime, timezone
out = Path("/home/pr21vyci/projects/adaptive-remeshing/runs/hpc/stage_c2/recovery/c2f_v2_vs_h1")
cmp = json.loads((out / "C2F_V2_VS_H1_STATUS.json").read_text())
field = {}
fp = out / "C2F_V2_FIELD_CHECK.json"
if fp.is_file():
    field = json.loads(fp.read_text())
rem = json.loads(Path("/home/pr21vyci/projects/adaptive-remeshing/runs/hpc/stage_c2/C2C_V2/C2C_V2_REMESH_MANIFEST.json").read_text())
tech = {
    "pbs_exit_status": 0,
    "abaqus_completed": True,
    "C2F_V2_ok": True,
    "odb_path": "/scratch/pr21vyci/adaptive-remeshing/runs/molnar_c2f_v2_refined_final_threads4_1376444.mmaster02/molnar_c2f_v2_refined_final_threads4.odb",
    "job_id": "1376444.mmaster02",
    "has_U": field.get("has_U"),
    "has_RF": field.get("has_RF"),
    "sdv_finite": field.get("sdv_finite"),
}
# technical failure override
if not tech["abaqus_completed"]:
    cls = "stage_c_refined_solver_failed"
elif not cmp.get("scientific_peak_prepeak_pass"):
    cls = "stage_c_technically_valid_response_deviation"
else:
    cls = "stage_c_refined_response_supported"
final = {
    "stage": "Stage_C_final",
    "classification": cls,
    "technical": tech,
    "scientific_vs_H1": cmp,
    "mesh_remesh": {
        "n_physical": rem.get("n_elements"),
        "corridor_h": rem.get("corridor_h"),
        "global_h": rem.get("global_h"),
        "far_field": rem.get("far_field"),
        "refined_zone": rem.get("refined_zone"),
        "relative_MISESERI_threshold": 0.05,
        "marking_formula": rem.get("sizing", {}).get("marking_formula"),
        "local_h_over_lc_median": (rem.get("corridor_h") or {}).get("median", 0) / 0.015 if rem.get("corridor_h") else None,
    },
    "performance_caution": "H1 serial vs C2F 4-thread; element reduction is mesh-attributable; walltime is not solely remeshing credit",
    "written_at_utc": datetime.now(timezone.utc).isoformat(),
}
(out / "STAGE_C_FINAL_CLASSIFICATION.json").write_text(json.dumps(final, indent=2, sort_keys=True) + "\n")
# short md
md = []
md.append("# Stage C final classification")
md.append("")
md.append("## Classification")
md.append("")
md.append("`%s`" % cls)
md.append("")
md.append("## Technical")
md.append("")
md.append("- PBS Exit_status: 0")
md.append("- Abaqus: COMPLETED SUCCESSFULLY")
md.append("- C2F_V2.ok: present")
md.append("- ODB: present (~206 MB)")
md.append("- has_U: %s  has_RF: %s  sdv_finite: %s" % (field.get("has_U"), field.get("has_RF"), field.get("sdv_finite")))
md.append("")
md.append("## Scientific vs H1 (peak/pre-peak)")
md.append("")
m = cmp["metrics"]
g = cmp["gates"]
md.append("| Metric | Value | Pass |")
md.append("| --- | ---: | --- |")
md.append("| Peak RF rel | %.4f%% | %s |" % (100*m["rel_peak_force"], g["peak_force_rel_le_0.02"]))
md.append("| Initial stiffness rel | %.4f%% | %s |" % (100*m["rel_initial_stiffness"], g["initial_stiffness_rel_le_0.01"]))
md.append("| Pre-peak NRMSE | %.4f%% | %s |" % (100*m["prepeak_nrmse"], g["prepeak_nrmse_le_0.02"]))
md.append("| Peak U | ok=%s | %s |" % (g["peak_u_within_one_output_interval"], g["peak_u_within_one_output_interval"]))
md.append("")
md.append("Full NRMSE: %.4f%%  |  Post-peak NRMSE: %.4f%%" % (100*m["full_curve_nrmse"], 100*m["postpeak_nrmse"]))
md.append("")
md.append("## Mesh")
md.append("")
md.append("- Physical: 10088 vs H1 12064 (16.4%% reduction)")
md.append("- Layered: 30264")
md.append("- Corridor h median: %s  |  far median: %s" % ((rem.get("corridor_h") or {}).get("median"), (rem.get("far_field") or {}).get("median_h_far")))
md.append("- Zone: %s" % json.dumps(rem.get("refined_zone")))
md.append("- local h/lc median: %s" % final["mesh_remesh"]["local_h_over_lc_median"])
md.append("")
md.append("## Resources (C2F 1376444)")
md.append("")
md.append("- walltime 00:15:24 (924 s)")
md.append("- cputime 00:45:27 (2727 s)")
md.append("- mem ~599 MB")
md.append("- threads=4; H1 reference was serial — do not attribute speedup solely to remeshing")
md.append("")
(out / "STAGE_C_FINAL_CLASSIFICATION.md").write_text("\n".join(md) + "\n")
print(json.dumps({"classification": cls, "sci_pass": cmp.get("scientific_peak_prepeak_pass")}, indent=2))
PY

echo "C2F_V2_POSTPROCESS_DONE"
ls -la "${OUT}"
