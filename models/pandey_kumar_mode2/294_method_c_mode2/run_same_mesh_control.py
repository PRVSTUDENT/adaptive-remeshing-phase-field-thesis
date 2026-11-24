# -*- coding: utf-8 -*-
"""Execute the prepared same-mesh hold-only control for Mode-II Cycle 1 failure diagnosis.

Manifest: models/pandey_kumar_mode2/294_method_c_mode2/local_windows_full_run/same_mesh_control_manifest.json
Run dir:  D:/mc3_local/mode2_same_mesh_control_prepared_20261124_1616
Job:      PK_METHOD_C_MODE2_SAME_MESH_HOLD_CONTROL
"""
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
RUN_DIR = Path(r"D:\mc3_local\mode2_same_mesh_control_prepared_20261124_1616").resolve()

sys.path.insert(0, str(HERE))
import mode2_single_job_orchestrator as api
from mode2_runtime import validate_uel_properties, write_json
from stall_watchdog import StallWatchdog

JOB = "PK_METHOD_C_MODE2_SAME_MESH_HOLD_CONTROL"
MANIFEST_PATH = HERE / "local_windows_full_run" / "same_mesh_control_manifest.json"


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest().upper()


def main():
    print("=== Starting Same-Mesh Hold-Only Control Execution ===")
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))

    inp_path = RUN_DIR / f"{JOB}.inp"
    phys_path = RUN_DIR / f"{JOB}_PHYS.inp"
    source_path = RUN_DIR / "f42_mixed_uel.for"

    if not source_path.exists():
        canon_source = ROOT / "models/pandey_kumar_mode1/f42_mixed_uel.for"
        shutil.copy2(canon_source, source_path)

    # 1. Verify exact hashes against manifest
    assert sha256(inp_path) == manifest["input_sha256"], f"Input hash mismatch: {sha256(inp_path)} != {manifest['input_sha256']}"
    assert sha256(phys_path) == manifest["mesh_sha256"], f"Mesh hash mismatch: {sha256(phys_path)} != {manifest['mesh_sha256']}"
    assert sha256(source_path) == manifest["source_sha256"], f"Source hash mismatch: {sha256(source_path)} != {manifest['source_sha256']}"
    print("Preflight verification: All hashes match manifest bitwise.")

    mesh = api.parse_physical_mesh(str(phys_path))
    nodes, quads, tris, _ = mesh
    num_phys = len(quads) + len(tris)
    validate_uel_properties(inp_path, num_phys)
    print(f"UEL property card validated ({num_phys} elements).")

    abaqus = shutil.which("abaqus") or r"C:\SIMULIA\Commands\abaqus.bat"
    watchdog = StallWatchdog()

    # 2. Datacheck
    dc_job = f"{JOB}_DATACHECK"
    dc_log = RUN_DIR / f"{dc_job}_command.log"
    print(f"Running datacheck ({dc_job})...")
    with dc_log.open("w") as stream:
        p = subprocess.Popen(
            [abaqus, f"job={dc_job}", f"input={JOB}", f"user={source_path.name}", "cpus=1", "datacheck", "interactive"],
            cwd=RUN_DIR, stdin=subprocess.DEVNULL, stdout=stream, stderr=subprocess.STDOUT
        )
        p.wait()
    if p.returncode != 0:
        raise RuntimeError(f"Datacheck failed with code {p.returncode}. See {dc_log}")
    print("Datacheck completed successfully (Exit 0).")

    # 3. Solver execution
    solve_log = RUN_DIR / f"{JOB}_command.log"
    print(f"Running solver ({JOB}) on 1 CPU...")
    watchdog.start_cycle()
    start_time = time.time()
    with solve_log.open("w") as stream:
        p = subprocess.Popen(
            [abaqus, f"job={JOB}", f"input={JOB}", f"user={source_path.name}", "cpus=1", "interactive"],
            cwd=RUN_DIR, stdin=subprocess.DEVNULL, stdout=stream, stderr=subprocess.STDOUT
        )
        while p.poll() is None:
            time.sleep(5)
            stalled, reason, details = watchdog.check_simulation_stall(str(RUN_DIR / f"{JOB}.sta"))
            if stalled:
                subprocess.run([abaqus, "terminate", f"job={JOB}"], cwd=RUN_DIR, stdin=subprocess.DEVNULL, timeout=30)
                raise RuntimeError(f"Simulation stalled: {reason} - {details}")

    elapsed = time.time() - start_time
    print(f"Solver process exited with code {p.returncode} in {elapsed:.2f} s.")
    if p.returncode != 0:
        raise RuntimeError(f"Solver failed with code {p.returncode}. See {solve_log}")

    sta_path = RUN_DIR / f"{JOB}.sta"
    if not sta_path.exists() or "THE ANALYSIS HAS COMPLETED SUCCESSFULLY" not in sta_path.read_text(errors="replace"):
        raise RuntimeError("Analysis .sta did not report successful completion.")
    print("Solver reported analysis completion.")

    # 4. Extract results
    extract_script = RUN_DIR / f"{JOB}_extract.py"
    target_json = RUN_DIR / f"{JOB}_fields.json"
    code = """import odbAccess, json, sys
odb = odbAccess.openOdb(sys.argv[1], readOnly=True)
inst = list(odb.rootAssembly.instances.values())[0]
nphys = len(inst.elements) // 3
def state(frame):
    dgp = {}; hgp = {}; energies = {}
    for v in frame.fieldOutputs['SDV1'].values:
        dgp.setdefault((v.elementLabel - 1) % nphys + 1, []).append(float(v.data))
    for v in frame.fieldOutputs['SDV2'].values:
        hgp[str((v.elementLabel - 1) % nphys + 1) + '_' + str(v.integrationPoint)] = float(v.data)
    for key in ['SDV17', 'SDV18']:
        if key in frame.fieldOutputs:
            by = {}
            for v in frame.fieldOutputs[key].values: by[v.elementLabel] = float(v.data)
            energies[key] = sum(by.values())
    nd = {}
    for e in inst.elements:
        eid = (e.label - 1) % nphys + 1
        if eid in dgp:
            d = sum(dgp[eid]) / len(dgp[eid])
            for n in e.connectivity: nd.setdefault(n, []).append(d)
    damage = {str(n): sum(v) / len(v) for n, v in nd.items()}
    def rp(key):
        vals = [v for v in frame.fieldOutputs[key].values if v.nodeLabel == 999999]
        if len(vals) != 1: raise ValueError('Missing or ambiguous RP ' + key)
        return float(vals[0].data[0])
    return dict(damage=damage, history=hgp, u1=rp('U'), rf1=rp('RF'), energies=energies,
                step_frame=frame.incrementNumber, frame_time=frame.frameValue)
steps = list(odb.steps.values())
result = {'hold': state(steps[0].frames[-1]), 'terminal': state(steps[-1].frames[-1]),
          'steps': [s.name for s in steps]}
result['peak_rf1'] = max(abs(float(v.data[0])) for s in steps for f in s.frames
                         for v in f.fieldOutputs['RF'].values if v.nodeLabel == 999999 and f.incrementNumber > 0)
with open(sys.argv[2], 'w') as f: json.dump(result, f)
odb.close()
"""
    extract_script.write_text(code, encoding="utf-8")
    subprocess.run(
        [abaqus, "python", str(extract_script), str(RUN_DIR / f"{JOB}.odb"), str(target_json)],
        cwd=RUN_DIR, check=True
    )
    fields = json.loads(target_json.read_text(encoding="utf-8"))

    # 5. Gate evaluation
    donor_u1 = manifest["donor_u1_mm"]  # 0.009499999694526196
    donor_checkpoint = json.loads((HERE / "local_windows_full_run" / "PK_METHOD_C_MODE2_COARSE_JOB1_checkpoint.json").read_text(encoding="utf-8"))
    donor_rf1 = donor_checkpoint["summary"]["terminal_rf1_kn"]  # 0.3980390131473541
    donor_max_d = donor_checkpoint["summary"]["max_damage"]     # 0.35076945275068283

    hold_u1 = fields["hold"]["u1"]
    hold_rf1 = fields["hold"]["rf1"]
    hold_max_d = max(fields["hold"]["damage"].values())

    delta_rf1_pct = 100.0 * (abs(hold_rf1) - abs(donor_rf1)) / abs(donor_rf1)
    force_pass = abs(delta_rf1_pct) <= manifest["acceptance_force_continuity_pct"]
    damage_nonhealing_pass = hold_max_d >= (donor_max_d - 1e-4)
    # Check if damage jumped artificially during the hold
    damage_jump = hold_max_d - donor_max_d

    print(f"Results summary:")
    print(f"  Donor u1:      {donor_u1:.8e} mm")
    print(f"  Hold u1:       {hold_u1:.8e} mm")
    print(f"  Donor RF1:     {donor_rf1:.8e} kN")
    print(f"  Hold RF1:      {hold_rf1:.8e} kN")
    print(f"  Delta RF1:     {delta_rf1_pct:+.4f}% (Gate: +/-5.0%) -> PASS: {force_pass}")
    print(f"  Donor max d:   {donor_max_d:.6f}")
    print(f"  Hold max d:    {hold_max_d:.6f} (Jump: {damage_jump:+.6f}) -> Nonhealing: {damage_nonhealing_pass}")

    status = "PASS" if (force_pass and damage_nonhealing_pass and abs(damage_jump) < 0.05) else "FAIL"

    interpretation = ""
    if status == "PASS":
        interpretation = "Same-mesh control PASSED (force within 5%, no damage jump). The failure in Cycle 1 was caused by the mesh change (nonmatching remesh / spatial interpolation), not by the state-transfer initialization."
    else:
        interpretation = f"Same-mesh control FAILED (Delta RF1 = {delta_rf1_pct:.2f}%, hold max damage = {hold_max_d:.6f} vs donor {donor_max_d:.6f}). The failure occurs even on the IDENTICAL mesh, proving the root cause is the state-transfer / initialization gap (lack of interior displacement field and/or phase DOF 3 initialization), not the remesh."

    print(f"Outcome: {status}")
    print(f"Interpretation: {interpretation}")

    summary = {
        "job": JOB,
        "control_status": status,
        "interpretation": interpretation,
        "donor_u1_mm": donor_u1,
        "hold_u1_mm": hold_u1,
        "donor_rf1_kn": donor_rf1,
        "hold_rf1_kn": hold_rf1,
        "force_continuity_delta_pct": delta_rf1_pct,
        "force_continuity_pass": force_pass,
        "donor_max_damage": donor_max_d,
        "hold_max_damage": hold_max_d,
        "damage_jump": damage_jump,
        "damage_nonhealing_pass": damage_nonhealing_pass,
        "hold_energies": fields["hold"]["energies"],
        "donor_energies": donor_checkpoint["fields"]["terminal"]["energies"],
        "elapsed_seconds": elapsed,
        "mesh_elements": len(quads) + len(tris),
        "mesh_nodes": len(nodes),
        "input_sha256": sha256(inp_path),
        "mesh_sha256": sha256(phys_path),
        "source_sha256": sha256(source_path),
        "donor_checkpoint_sha256": manifest["donor_checkpoint_sha256"],
        "pbs_submissions": 0,
        "cumulative_pbs_submissions": 73
    }

    summary_path = RUN_DIR / f"{JOB}_SUMMARY.json"
    write_json(summary_path, summary)

    # 6. Copy published files to local_windows_full_run
    dest_dir = HERE / "local_windows_full_run"
    dest_dir.mkdir(exist_ok=True)
    shutil.copy2(summary_path, dest_dir / f"{JOB}_SUMMARY.json")
    shutil.copy2(sta_path, dest_dir / f"{JOB}.sta")
    shutil.copy2(RUN_DIR / f"{JOB}.dat", dest_dir / f"{JOB}.dat")
    print(f"Published control summary, .sta, and .dat to {dest_dir}.")


if __name__ == "__main__":
    main()
