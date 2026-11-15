"""
Audit script for Case 2 (plate with off-axis hole) ODB candidates.
Inspects all local Case 2 ODB artifacts to determine whether an authentic later-state
native Abaqus MISESERI field exists at a known causal cutoff.
"""

import os
import sys
import json
import hashlib
import shutil
import tempfile
import subprocess

# Ensure stdout flushes immediately
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(line_buffering=True)

ABAQUS_BAT = r"C:\SIMULIA\Commands\abaqus.bat" if os.path.exists(r"C:\SIMULIA\Commands\abaqus.bat") else "abaqus.bat"

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

# Candidate ODB paths relative to repo root
CANDIDATE_ODBS = [
    # 176_method_a_plate_with_hole
    "models/pandey_kumar_mode1/176_method_a_plate_with_hole/PK_HOLE_METHOD_A_PREANALYSIS.odb",
    "models/pandey_kumar_mode1/176_method_a_plate_with_hole/PK_HOLE_COARSE_JOB1.odb",
    # 188_pk_sec43_hole_plate
    "models/pandey_kumar_mode1/188_pk_sec43_hole_plate/PK_SEC43_COARSE_JOB1.odb",
    "models/pandey_kumar_mode1/188_pk_sec43_hole_plate/PK_SEC43_COARSE_JOB1_DC.odb",
    "models/pandey_kumar_mode1/188_pk_sec43_hole_plate/PK_SEC43_COARSE_RECOVERY.odb",
    # 190_pk_sec43_job1_rerun
    "models/pandey_kumar_mode1/190_pk_sec43_job1_rerun/PK_SEC43_RERUN_JOB1_DC.odb",
    "models/pandey_kumar_mode1/190_pk_sec43_job1_rerun/PK_SEC43_RERUN_RECOVERY.odb",
    # 192_pk_sec43_staggered_job1
    "models/pandey_kumar_mode1/192_pk_sec43_staggered_job1/PK_SEC43_STAGGERED_RECOVERY_DEG.odb",
    "models/pandey_kumar_mode1/192_pk_sec43_staggered_job1/PK_SEC43_STAGGERED_RECOVERY_ELAS.odb",
    "models/pandey_kumar_mode1/192_pk_sec43_staggered_job1/PK_SEC43_STAGGERED_RECOVERY_SEC_INIT.odb",
    "models/pandey_kumar_mode1/192_pk_sec43_staggered_job1/PK_SEC43_STAGGERED_RECOVERY_SEC_MIDPROP.odb",
    # 196_pk_sec43_standard_elastic
    "models/pandey_kumar_mode1/196_pk_sec43_standard_elastic/PK_SEC43_STANDARD_JOB1.odb",
    "models/pandey_kumar_mode1/196_pk_sec43_standard_elastic/PK_SEC43_STANDARD_JOB1_DC.odb",
    # 197_pk_sec43_coupled_umat
    "models/pandey_kumar_mode1/197_pk_sec43_coupled_umat/PK_SEC43_COUPLED_UMAT.odb",
    "models/pandey_kumar_mode1/197_pk_sec43_coupled_umat/PK_SEC43_COUPLED_UMAT_MIDPROP.odb",
    # 198_pk_sec43_coupled_validation
    "models/pandey_kumar_mode1/198_pk_sec43_coupled_validation/SEC43_STATE1_INIT.odb",
    "models/pandey_kumar_mode1/198_pk_sec43_coupled_validation/SEC43_STATE2_HOLE_ARREST.odb",
    "models/pandey_kumar_mode1/198_pk_sec43_coupled_validation/SEC43_STATE3_SEC_INIT.odb",
    "models/pandey_kumar_mode1/198_pk_sec43_coupled_validation/SEC43_STATE4_SEC_MIDPROP.odb",
    "models/pandey_kumar_mode1/198_pk_sec43_coupled_validation/SEC43_STATE5_TERMINAL.odb",
    "models/pandey_kumar_mode1/198_pk_sec43_coupled_validation/PK_SEC43_MULTISTATE_ENVELOPE_DONOR.odb",
    # 200_pk_sec43_prescribed_displacement
    "models/pandey_kumar_mode1/200_pk_sec43_prescribed_displacement/PK_SEC43_PRESCRIBED_STATE2.odb",
    "models/pandey_kumar_mode1/200_pk_sec43_prescribed_displacement/PK_SEC43_PRESCRIBED_STATE4.odb",
    "models/pandey_kumar_mode1/200_pk_sec43_prescribed_displacement/PK_SEC43_PRESCRIBED_STATE5.odb",
    # 202_pk_sec43_continuous_displacement
    "models/pandey_kumar_mode1/202_pk_sec43_continuous_displacement/PK_SEC43_CONTINUOUS_STATE2.odb",
    "models/pandey_kumar_mode1/202_pk_sec43_continuous_displacement/PK_SEC43_CONTINUOUS_STATE4.odb",
    "models/pandey_kumar_mode1/202_pk_sec43_continuous_displacement/PK_SEC43_CONTINUOUS_STATE5.odb",
    # 224_f1734_case2_distal_refinement
    "models/pandey_kumar_mode1/224_f1734_case2_distal_refinement/PK_F1779_CASE2_ENVELOPE.odb",
    # 233_f1750_local_sizing_probe
    "models/pandey_kumar_mode1/233_f1750_local_sizing_probe/PK_SEC43_STATE_B_DAMAGE_DONOR.odb",
    # Root directory and runs/ Case 2 recovery artifacts
    "PK_HOLE_COUPLED_RECOVERY.odb",
    "PK_HOLE_F1656_RECOVERY.odb",
    "PK_HOLE_F1659_RECOVERY.odb",
    "PK_HOLE_F1661_RECOVERY.odb",
    "PK_HOLE_RECOVERY_SOLVE.odb",
    "PK_HOLE_SIZING_SOLVE.odb",
    "runs/f1683_recovery_candidate_b/PK_HOLE_RECOVERY_B.odb",
    "runs/f1683_recovery_candidate_c/PK_HOLE_RECOVERY_C.odb",
    "runs/f1683_recovery_candidate_d/PK_HOLE_RECOVERY_D.odb",
    "runs/f1684_multistep_recovery/PK_HOLE_MULTISTEP_RECOVERY.odb",
]

def sha256_file(filepath):
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(1024 * 1024):
            h.update(chunk)
    return h.hexdigest().upper()

ABAQUS_PROBE_SCRIPT = r"""
import sys
import json
import odbAccess

odb_path = sys.argv[-1]
result = {
    "steps": {},
    "error": None
}

try:
    odb = odbAccess.openOdb(path=odb_path, readOnly=True)
    for step_name, step in odb.steps.items():
        step_info = {
            "num_frames": len(step.frames),
            "time_period": getattr(step, "timePeriod", None),
            "procedure": getattr(step, "procedure", str(type(step))),
            "frames": []
        }
        # Check first and last frame fields, plus scan for MISESERI
        for f_idx in [0, len(step.frames) - 1] if len(step.frames) > 1 else [0]:
            if len(step.frames) == 0:
                continue
            frame = step.frames[f_idx]
            field_names = list(frame.fieldOutputs.keys())
            f_data = {
                "frame_id": frame.frameId,
                "frame_value": frame.frameValue,
                "field_outputs": field_names,
                "has_miseseri": "MISESERI" in field_names,
                "has_misesavg": "MISESAVG" in field_names,
                "miseseri_stats": None
            }
            if "MISESERI" in field_names:
                fo = frame.fieldOutputs["MISESERI"]
                vals = [v.data for v in fo.values if hasattr(v, "data") and v.data is not None]
                if vals:
                    f_data["miseseri_stats"] = {
                        "count": len(vals),
                        "min": float(min(vals)),
                        "max": float(max(vals)),
                        "mean": float(sum(vals) / len(vals)),
                        "non_zero_count": sum(1 for v in vals if abs(v) > 1e-12)
                    }
                else:
                    f_data["miseseri_stats"] = {"count": 0, "min": 0, "max": 0, "mean": 0, "non_zero_count": 0}
            step_info["frames"].append(f_data)
        
        # Scan if any frame has non-zero MISESERI
        has_any_nonzero_miseseri = False
        for f in step.frames:
            if "MISESERI" in f.fieldOutputs:
                fo = f.fieldOutputs["MISESERI"]
                for v in fo.values:
                    if hasattr(v, "data") and abs(v.data) > 1e-12:
                        has_any_nonzero_miseseri = True
                        break
            if has_any_nonzero_miseseri:
                break
        step_info["has_any_nonzero_miseseri"] = has_any_nonzero_miseseri
        result["steps"][step_name] = step_info
    odb.close()
except Exception as e:
    result["error"] = str(e)

print("__RESULT_JSON_START__")
print(json.dumps(result))
print("__RESULT_JSON_END__")
"""

def main():
    print("=== Case 2 ODB Candidate Inventory Audit ===")
    results = []

    # Temporary directory for safe copying before Abaqus probe
    scratch_dir = tempfile.mkdtemp(prefix="case2_odb_audit_")

    probe_script_path = os.path.join(scratch_dir, "probe_odb.py")
    with open(probe_script_path, "w") as f:
        f.write(ABAQUS_PROBE_SCRIPT)

    try:
        for rel_path in CANDIDATE_ODBS:
            full_path = os.path.join(REPO_ROOT, rel_path)
            if not os.path.exists(full_path):
                print(f"[MISSING] {rel_path}")
                results.append({
                    "path": rel_path,
                    "exists": False
                })
                continue

            size = os.path.getsize(full_path)
            sha = sha256_file(full_path)
            print(f"[FOUND] {rel_path} ({size:,} bytes, SHA: {sha[:16]}...)")

            # Copy to temp file to prevent header timestamp modification
            temp_odb = os.path.join(scratch_dir, "temp_target.odb")
            shutil.copyfile(full_path, temp_odb)

            cmd = [ABAQUS_BAT, "python", probe_script_path, temp_odb]
            proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True, shell=True)
            if os.path.exists(temp_odb):
                os.remove(temp_odb)

            stdout = proc.stdout
            probe_data = None
            if "__RESULT_JSON_START__" in stdout and "__RESULT_JSON_END__" in stdout:
                start = stdout.index("__RESULT_JSON_START__") + len("__RESULT_JSON_START__")
                end = stdout.index("__RESULT_JSON_END__")
                raw_json = stdout[start:end].strip()
                try:
                    probe_data = json.loads(raw_json)
                except Exception as ex:
                    probe_data = {"error": f"JSON parse error: {ex}"}
            else:
                probe_data = {"error": f"No JSON markers in stdout. Stderr: {proc.stderr[:200]}"}

            item = {
                "path": rel_path,
                "exists": True,
                "size_bytes": size,
                "sha256": sha,
                "probe": probe_data
            }
            results.append(item)

            # Summarize findings
            if probe_data and not probe_data.get("error"):
                for step_name, sinfo in probe_data.get("steps", {}).items():
                    print(f"    Step '{step_name}': {sinfo['num_frames']} frames, has_any_nonzero_miseseri={sinfo.get('has_any_nonzero_miseseri')}")
                    for f in sinfo.get("frames", []):
                        if f.get("has_miseseri"):
                            stats = f.get("miseseri_stats", {})
                            print(f"      Frame {f['frame_id']} (val={f['frame_value']}): MISESERI count={stats.get('count')}, non_zero={stats.get('non_zero_count')}, max={stats.get('max')}")
            elif probe_data and probe_data.get("error"):
                print(f"    Probe error: {probe_data.get('error')}")

    finally:
        shutil.rmtree(scratch_dir, ignore_errors=True)

    out_file = os.path.join(REPO_ROOT, "runs", "case2_odb_audit_results.json")
    os.makedirs(os.path.dirname(out_file), exist_ok=True)
    with open(out_file, "w") as f:
        json.dump(results, f, indent=2)
    print(f"\nAudit complete. Saved to: {out_file}")

if __name__ == "__main__":
    main()
