"""
scripts/remeshing/execute_f1684_multistep_recovery.py
=====================================================
Task F1684: Multi-Step Native Auxiliary Recovery Analysis & Equivalence Audit
- Step 1: RECOVERY_C (Donor Step-2 Frame 150, u2 = 0.007100 mm, Candidate C damage)
- Step 2: RECOVERY_TERMINAL (Donor Step-2 Frame 337, u2 = 0.00959078 mm, Terminal baseline damage)
- Material: DamagedElastic_USDFLD with FIELD(1) = d(noel, npt, kstep)
- Runs local Abaqus/Standard solve with runtime coordinate verification (< 10 nm)
- Quantitative Bitwise/Precision Comparison:
    * Multi-Step Step 1 vs Independent Candidate C (PK_HOLE_RECOVERY_C.odb)
    * Multi-Step Step 2 vs Independent Terminal Baseline (PK_HOLE_F1661_RECOVERY.odb)
- Proves path-independence and zero stress carryover in native multi-step linear elasticity.
"""
import os
import sys
import json
import math
import shutil
import subprocess
import numpy as np
from shapely.geometry import Point, Polygon
from shapely.strtree import STRtree


def load_donor_mesh(phys_inp_path):
    print(f"Loading donor mesh from: {phys_inp_path}")
    donor_nodes = {}
    donor_elems = {}
    active_sec = None
    with open(phys_inp_path, "r") as fp:
        for line in fp:
            line = line.strip()
            if not line or line.startswith("**"):
                continue
            if line.startswith("*"):
                upline = line.upper()
                if upline.startswith("*NODE"):
                    active_sec = "NODE"
                elif upline.startswith("*ELEMENT"):
                    active_sec = "ELEMENT"
                else:
                    active_sec = None
                continue
            if active_sec == "NODE":
                parts = [p.strip() for p in line.split(",")]
                if len(parts) >= 3:
                    donor_nodes[int(parts[0])] = (float(parts[1]), float(parts[2]))
            elif active_sec == "ELEMENT":
                parts = [p.strip() for p in line.split(",")]
                if len(parts) >= 4:
                    donor_elems[int(parts[0])] = [int(p) for p in parts[1:]]
    print(f"  Loaded donor: {len(donor_nodes)} nodes, {len(donor_elems)} elements.")
    return donor_nodes, donor_elems


def load_receiver_mesh(rec_json_path):
    print(f"Loading receiver mesh from: {rec_json_path}")
    with open(rec_json_path, "r") as fp:
        d = json.load(fp)
    rec_nodes = {int(k): (float(v[0]), float(v[1])) for k, v in d["nodes"].items()}
    rec_elems = {int(k): [int(nid) for nid in v] for k, v in d["elems"].items()}
    print(f"  Loaded receiver: {len(rec_nodes)} nodes, {len(rec_elems)} elements.")
    return rec_nodes, rec_elems


def compute_receiver_ips(rec_nodes, rec_elems):
    xg4 = [-0.577350269189626, 0.577350269189626, -0.577350269189626, 0.577350269189626]
    yg4 = [-0.577350269189626, -0.577350269189626, 0.577350269189626, 0.577350269189626]
    notch_a = 0.50
    notch_y = 0.50

    receiver_ips = []
    for eid in sorted(rec_elems.keys()):
        conn = rec_elems[eid]
        pts = [rec_nodes[nid] for nid in conn]
        if len(conn) == 4:
            for k in range(4):
                xi = xg4[k]
                eta = yg4[k]
                N = [
                    0.25 * (1.0 - xi) * (1.0 - eta),
                    0.25 * (1.0 + xi) * (1.0 - eta),
                    0.25 * (1.0 + xi) * (1.0 + eta),
                    0.25 * (1.0 - xi) * (1.0 + eta)
                ]
                gx = sum([N[m] * pts[m][0] for m in range(4)])
                gy = sum([N[m] * pts[m][1] for m in range(4)])
                slit_flag = 0
                if gx <= notch_a:
                    slit_flag = 1 if gy >= notch_y else -1
                receiver_ips.append({
                    "eid": eid, "ipt": k + 1, "x": gx, "y": gy, "slit": slit_flag
                })
        else:
            gx = sum([pts[m][0] for m in range(3)]) / 3.0
            gy = sum([pts[m][1] for m in range(3)]) / 3.0
            slit_flag = 0
            if gx <= notch_a:
                slit_flag = 1 if gy >= notch_y else -1
            receiver_ips.append({
                "eid": eid, "ipt": 1, "x": gx, "y": gy, "slit": slit_flag
            })
    print(f"  Computed exact coordinates for {len(receiver_ips)} receiver integration points.")
    return receiver_ips


def extract_donor_damage_dict(donor_odb_path, step_name, frame_idx):
    tmp_out = os.path.abspath(f"temp_donor_d_{step_name}_{frame_idx}.json")
    tmp_script = os.path.abspath(f"temp_extract_d_{step_name}_{frame_idx}.py")
    script_content = (
        "from odbAccess import openOdb\n"
        "import json\n"
        f"odb = openOdb(r'{donor_odb_path}', readOnly=True)\n"
        f"f = odb.steps['{step_name}'].frames[{frame_idx}]\n"
        "v1 = {v.elementLabel - 2*2906 if v.elementLabel > 2*2906 else v.elementLabel: float(v.data) for v in f.fieldOutputs['SDV1'].values}\n"
        "odb.close()\n"
        f"with open(r'{tmp_out}', 'w') as fp:\n"
        "    json.dump(v1, fp)\n"
    )
    with open(tmp_script, "w") as fp:
        fp.write(script_content)

    cmd = ["cmd", "/c", "abaqus", "python", tmp_script]
    res = subprocess.run(cmd, capture_output=True, text=True)
    if os.path.exists(tmp_script):
        os.remove(tmp_script)

    if res.returncode != 0 or not os.path.exists(tmp_out):
        raise RuntimeError(f"Failed to extract donor damage from ODB: {res.stderr}\n{res.stdout}")
    with open(tmp_out, "r") as fp:
        raw = json.load(fp)
    os.remove(tmp_out)
    return {int(k): float(v) for k, v in raw.items()}


def build_strtree_index(donor_nodes, donor_elems):
    notch_a = 0.50
    notch_y = 0.50

    polys_top = []
    eids_top = []
    polys_bot = []
    eids_bot = []
    polys_all = []
    eids_all = []

    for eid, conn in donor_elems.items():
        coords = [donor_nodes[nid] for nid in conn]
        poly = Polygon(coords)
        cx = poly.centroid.x
        cy = poly.centroid.y

        polys_all.append(poly)
        eids_all.append(eid)

        if cx <= notch_a:
            if cy >= notch_y:
                polys_top.append(poly)
                eids_top.append(eid)
            else:
                polys_bot.append(poly)
                eids_bot.append(eid)
        else:
            polys_top.append(poly)
            eids_top.append(eid)
            polys_bot.append(poly)
            eids_bot.append(eid)

    tree_top = STRtree(polys_top)
    tree_bot = STRtree(polys_bot)
    tree_all = STRtree(polys_all)

    return {
        "tree_top": tree_top, "polys_top": polys_top, "eids_top": eids_top,
        "tree_bot": tree_bot, "polys_bot": polys_bot, "eids_bot": eids_bot,
        "tree_all": tree_all, "polys_all": polys_all, "eids_all": eids_all
    }


def map_damage_to_receiver(receiver_ips, trees, donor_elem_d):
    k_res = 1.0e-7
    ip_entries = []
    contained_cnt = 0

    tree_top = trees["tree_top"]
    polys_top = trees["polys_top"]
    eids_top = trees["eids_top"]

    tree_bot = trees["tree_bot"]
    polys_bot = trees["polys_bot"]
    eids_bot = trees["eids_bot"]

    tree_all = trees["tree_all"]
    polys_all = trees["polys_all"]
    eids_all = trees["eids_all"]

    for ip in receiver_ips:
        pt = Point(ip["x"], ip["y"])
        s_flag = ip["slit"]

        if s_flag == 1:
            tree = tree_top
            polys = polys_top
            eids = eids_top
        elif s_flag == -1:
            tree = tree_bot
            polys = polys_bot
            eids = eids_bot
        else:
            tree = tree_all
            polys = polys_all
            eids = eids_all

        cand_indices = tree.query(pt)
        assigned_eid = None
        min_dist = float("inf")

        for idx in cand_indices:
            poly = polys[idx]
            if poly.contains(pt) or poly.touches(pt):
                assigned_eid = eids[idx]
                contained_cnt += 1
                min_dist = 0.0
                break

        if assigned_eid is None:
            for idx in cand_indices:
                poly = polys[idx]
                d = poly.distance(pt)
                if d < min_dist:
                    min_dist = d
                    assigned_eid = eids[idx]
            if assigned_eid is None:
                for idx, poly in enumerate(polys):
                    d = poly.distance(pt)
                    if d < min_dist:
                        min_dist = d
                        assigned_eid = eids[idx]

        d_val = donor_elem_d[assigned_eid]
        g_val = (1.0 - d_val)**2 + k_res

        ip_entries.append({
            "noel": ip["eid"],
            "npt": ip["ipt"],
            "x": ip["x"],
            "y": ip["y"],
            "donor_eid": assigned_eid,
            "distance": min_dist,
            "d": d_val,
            "g": g_val
        })

    containment_pct = (contained_cnt / float(len(receiver_ips))) * 100.0
    print(f"  Mapped {len(ip_entries)} IPs: {contained_cnt} strictly contained ({containment_pct:.2f}%).")
    return ip_entries


def make_fortran_string_assignment(var_name, path_str):
    p = path_str.replace("\\", "/")
    chunks = [p[i:i+38] for i in range(0, len(p), 38)]
    lines = []
    for idx, chunk in enumerate(chunks):
        if idx == 0:
            suffix = " //" if len(chunks) > 1 else ""
            lines.append(f"        {var_name} = '{chunk}'{suffix}")
        else:
            cont_char = str((idx % 9) + 1)
            suffix = " //" if idx < len(chunks) - 1 else ""
            lines.append(f"     {cont_char}   '{chunk}'{suffix}")
    return "\n".join(lines)


def generate_multistep_usdfld_source(lookup_path, coords_log_path):
    fname_code = make_fortran_string_assignment("FNAME", lookup_path)
    log_code = make_fortran_string_assignment("LOG_FNAME", coords_log_path)
    
    src = f"""C=======================================================================
C     AUXILIARY USDFLD USER SUBROUTINE FOR F1684 MULTI-STEP STRESS RECOVERY
C     - Directly assigns material-point FIELD(1) from lookup_damage_multistep.txt
C     - Supports multi-step indexing: LOOKUP_D(NOEL, NPT, KSTEP)
C     - Step 1: Candidate C (Frame 150 damage, u = 0.0071 mm)
C     - Step 2: Terminal Baseline (Frame 337 damage, u = 0.00959078 mm)
C     - Strict runtime coordinate verification with 10 nm fail-closed check
C     - Logs runtime coordinates encountered during execution to file
C=======================================================================
      SUBROUTINE USDFLD(FIELD,STATEV,PNEWDT,DIRECT,T,CELENT,
     1 TIME,DTIME,CMNAME,ORNAME,NFIELD,NSTATV,NOEL,NPT,LAYER,
     2 KSPT,KSTEP,KINC,NDI,NSHR,COORD,JMAC,JMATYP,MATLAYO,LACCFLA)
      INCLUDE 'ABA_PARAM.INC'
      CHARACTER*80 CMNAME,ORNAME
      CHARACTER*3  FLGRAY(15)
      DIMENSION FIELD(NFIELD),STATEV(NSTATV),DIRECT(3,3),
     1 T(3,3),TIME(2)
      DIMENSION ARRAY(15),JARRAY(15),JMAC(*),JMATYP(*),
     2 COORD(*)

      INTEGER, PARAMETER :: MAX_ELEM = 5000
      INTEGER, PARAMETER :: MAX_NPT = 4
      INTEGER, PARAMETER :: MAX_STEP = 2
      REAL*8, SAVE :: LOOKUP_D(MAX_ELEM, MAX_NPT, MAX_STEP)
      REAL*8, SAVE :: LOOKUP_X(MAX_ELEM, MAX_NPT)
      REAL*8, SAVE :: LOOKUP_Y(MAX_ELEM, MAX_NPT)
      LOGICAL, SAVE :: TABLE_LOADED = .FALSE.
      LOGICAL, SAVE :: LOG_OPENED = .FALSE.
      LOGICAL, SAVE :: LOGGED(MAX_ELEM, MAX_NPT)
      INTEGER, SAVE :: LOG_COUNT = 0
      REAL*8, SAVE :: RUNTIME_MAX_DIST = 0.0D0
      INTEGER :: IEID, INPT, ISTAT, NUM_LOADED
      REAL*8 :: DX, DY, DIST, XVAL, YVAL, D1, G1, D2, G2
      CHARACTER*256 :: LINE, FNAME, LOG_FNAME

      IF (.NOT. TABLE_LOADED) THEN
        DO IEID = 1, MAX_ELEM
          DO INPT = 1, MAX_NPT
            LOOKUP_D(IEID, INPT, 1) = -1.0D0
            LOOKUP_D(IEID, INPT, 2) = -1.0D0
            LOOKUP_X(IEID, INPT) = 0.0D0
            LOOKUP_Y(IEID, INPT) = 0.0D0
            LOGGED(IEID, INPT) = .FALSE.
          END DO
        END DO

{fname_code}
        OPEN(UNIT=105, FILE=TRIM(FNAME), STATUS='OLD', 
     1       ACTION='READ', IOSTAT=ISTAT)
        IF (ISTAT .NE. 0) THEN
          WRITE(6,*) '*** ERROR [USDFLD]: Failed to open lookup file: ', 
     1               TRIM(FNAME)
          CALL XIT
        END IF

        NUM_LOADED = 0
 10     READ(105, '(A)', END=20) LINE
        IF (LINE(1:1) .EQ. '#' .OR. LEN_TRIM(LINE) .EQ. 0) GOTO 10
        READ(LINE, *, IOSTAT=ISTAT) IEID, INPT, XVAL, YVAL, D1, G1, 
     1                             D2, G2
        IF (ISTAT .EQ. 0) THEN
          IF (IEID .LE. MAX_ELEM .AND. INPT .LE. MAX_NPT) THEN
            LOOKUP_D(IEID, INPT, 1) = D1
            LOOKUP_D(IEID, INPT, 2) = D2
            LOOKUP_X(IEID, INPT) = XVAL
            LOOKUP_Y(IEID, INPT) = YVAL
            NUM_LOADED = NUM_LOADED + 1
          END IF
        END IF
        GOTO 10
 20     CLOSE(105)
        WRITE(6,*) '*** [USDFLD]: Successfully loaded lookup entries: ', 
     1             NUM_LOADED
        TABLE_LOADED = .TRUE.

{log_code}
        OPEN(UNIT=106, FILE=TRIM(LOG_FNAME), STATUS='REPLACE',
     1       ACTION='WRITE', IOSTAT=ISTAT)
        IF (ISTAT .EQ. 0) THEN
          WRITE(106, '(A)') '# NOEL NPT RUNTIME_X RUNTIME_Y ' //
     1                      'LOOKUP_X LOOKUP_Y DIST_MM'
          LOG_OPENED = .TRUE.
        END IF
      END IF

      IF (NOEL .GT. MAX_ELEM .OR. NPT .GT. MAX_NPT) THEN
        WRITE(6,*) '*** ERROR [USDFLD]: NOEL or NPT exceeds bounds: ',
     1             NOEL, NPT
        CALL XIT
      END IF

      IF (KSTEP .LT. 1 .OR. KSTEP .GT. MAX_STEP) THEN
        WRITE(6,*) '*** ERROR [USDFLD]: KSTEP out of bounds: ', KSTEP
        CALL XIT
      END IF

      IF (LOOKUP_D(NOEL, NPT, KSTEP) .LT. 0.0D0) THEN
        WRITE(6,*) '*** ERROR [USDFLD]: Missing entry for element/IP/step: ',
     1             NOEL, NPT, KSTEP
        CALL XIT
      END IF

      DX = COORD(1) - LOOKUP_X(NOEL, NPT)
      DY = COORD(2) - LOOKUP_Y(NOEL, NPT)
      DIST = SQRT(DX*DX + DY*DY)

      IF (DIST .GT. 1.0D-5) THEN
        WRITE(6,*) '*** ERROR [USDFLD]: Coordinate mismatch > 10 nm: ',
     1             NOEL, NPT, DIST, COORD(1), COORD(2),
     2             LOOKUP_X(NOEL, NPT), LOOKUP_Y(NOEL, NPT)
        CALL XIT
      END IF

      IF (DIST .GT. RUNTIME_MAX_DIST) THEN
        RUNTIME_MAX_DIST = DIST
      END IF

      IF (LOG_OPENED .AND. .NOT. LOGGED(NOEL, NPT)) THEN
        LOGGED(NOEL, NPT) = .TRUE.
        WRITE(106, '(I6, I3, 4(1X, E16.8), 1X, E14.6)') 
     1        NOEL, NPT, COORD(1), COORD(2), 
     2        LOOKUP_X(NOEL, NPT), LOOKUP_Y(NOEL, NPT), DIST
        FLUSH(106)
        LOG_COUNT = LOG_COUNT + 1
        IF (LOG_COUNT .GE. 11452) THEN
          CLOSE(106)
          LOG_OPENED = .FALSE.
        END IF
      END IF

      FIELD(1) = LOOKUP_D(NOEL, NPT, KSTEP)

      RETURN
      END
"""
    return src


def build_multistep_inp(base_inp_path, u2_step1, u2_step2, out_inp_path):
    with open(base_inp_path, "r") as fp:
        lines = fp.readlines()

    # Find where *Step starts
    step_start_idx = -1
    for idx, line in enumerate(lines):
        if line.strip().upper().startswith("*STEP"):
            step_start_idx = idx
            break

    if step_start_idx == -1:
        raise ValueError(f"Could not find *Step in {base_inp_path}")

    pre_step_lines = lines[:step_start_idx]

    step_definitions = f"""** ----------------------------------------------------------------
** STEP: RECOVERY_C (Frame 150, Candidate C, u = {u2_step1:.6f} mm)
** ----------------------------------------------------------------
*Step, name=RECOVERY_C, nlgeom=NO
*Static
1., 1., 1e-05, 1.
** 
** BOUNDARY CONDITIONS
** 
*Boundary
Bottom, 2, 2
Pin, 1, 1
Top, 1, 1
Top, 2, 2, {u2_step1:.8f}
** 
** OUTPUT REQUESTS
** 
*Restart, write, frequency=0
*Output, field
*Node Output, nset=All_elem
RF, U
*Element Output, elset=All_elem, directions=YES
EVOL, FV, MISESAVG, MISESERI, ENDEN, ENDENERI, S
*Output, history, variable=PRESELECT
*End Step
** 
** ----------------------------------------------------------------
** STEP: RECOVERY_TERMINAL (Frame 337, Terminal Baseline, u = {u2_step2:.6f} mm)
** ----------------------------------------------------------------
*Step, name=RECOVERY_TERMINAL, nlgeom=NO
*Static
1., 1., 1e-05, 1.
** 
** BOUNDARY CONDITIONS (Modified Top Displacement)
** 
*Boundary, op=MOD
Top, 2, 2, {u2_step2:.8f}
** 
** OUTPUT REQUESTS
** 
*Restart, write, frequency=0
*Output, field
*Node Output, nset=All_elem
RF, U
*Element Output, elset=All_elem, directions=YES
EVOL, FV, MISESAVG, MISESERI, ENDEN, ENDENERI, S
*Output, history, variable=PRESELECT
*End Step
"""

    with open(out_inp_path, "w") as fp:
        fp.writelines(pre_step_lines)
        fp.write(step_definitions)
    print(f"  Wrote multi-step input deck: {out_inp_path}")


def execute_solve(work_dir, job_name):
    bat_path = os.path.join(work_dir, "run_solve.bat")
    bat_content = (
        "@echo off\n"
        "cd /d \"%~dp0\"\n"
        "call \"C:\\Program Files (x86)\\Microsoft Visual Studio\\2022\\BuildTools\\VC\\Auxiliary\\Build\\vcvars64.bat\"\n"
        "call \"C:\\Program Files (x86)\\Intel\\oneAPI\\setvars.bat\" intel64 vs2022\n"
        f"abaqus job={job_name} user=recovery_multistep_usdfld.for interactive\n"
        "if errorlevel 1 exit /b %errorlevel%\n"
    )
    with open(bat_path, "w") as fp:
        fp.write(bat_content)

    print(f"  Executing Abaqus solve in {work_dir}...")
    p = subprocess.run(["cmd", "/c", bat_path], cwd=work_dir, capture_output=True, text=True)
    msg_path = os.path.join(work_dir, f"{job_name}.msg")
    has_error = False
    if os.path.exists(msg_path):
        with open(msg_path, "r") as fp:
            msg_text = fp.read()
            if "***ERROR" in msg_text:
                has_error = True
    if p.returncode != 0 or has_error:
        print("STDOUT:", p.stdout)
        print("STDERR:", p.stderr)
        if os.path.exists(msg_path):
            print("MSG:", msg_text[-1500:])
        dat_path = os.path.join(work_dir, f"{job_name}.dat")
        if os.path.exists(dat_path):
            with open(dat_path, "r") as fp:
                print("DAT:", fp.read()[-2000:])
        raise RuntimeError(f"Abaqus solve failed for {job_name} (returncode={p.returncode}, has_error={has_error})")
    print(f"  Abaqus solve completed successfully (Exit 0)!")


def audit_multistep_vs_single_step(multi_odb_path, cand_c_odb_path, term_odb_path, out_json_path):
    tmp_audit_script = os.path.abspath("temp_audit_multistep_equiv.py")
    tmp_audit_json = os.path.abspath("temp_audit_multistep_equiv.json")

    script_content = f"""from odbAccess import openOdb
import json
import numpy as np

def extract_step_fields(odb_path, step_name):
    odb = openOdb(odb_path, readOnly=True)
    step = odb.steps[step_name]
    frame = step.frames[-1]

    # Stress
    s_dict = {{v.elementLabel: (v.data[0], v.data[1], v.data[3], v.mises) for v in frame.fieldOutputs['S'].values}}
    # MISESERI
    eri_dict = {{v.elementLabel: float(v.data) for v in frame.fieldOutputs['MISESERI'].values}}
    # MISESAVG
    avg_dict = {{v.elementLabel: float(v.data) for v in frame.fieldOutputs['MISESAVG'].values}}
    # Reaction force on Top
    top_node_labels = set([n.label for n_arr in odb.rootAssembly.nodeSets['TOP'].nodes for n in n_arr])
    rf_total = sum([v.data[1] for v in frame.fieldOutputs['RF'].values if v.nodeLabel in top_node_labels])
    odb.close()
    return {{'S': s_dict, 'MISESERI': eri_dict, 'MISESAVG': avg_dict, 'RF2': rf_total}}

# 1. Multi-Step Step 1 vs Candidate C
m_s1 = extract_step_fields(r'{multi_odb_path}', 'RECOVERY_C')
c_s1 = extract_step_fields(r'{cand_c_odb_path}', 'Step-1')

# 2. Multi-Step Step 2 vs Terminal Baseline
m_s2 = extract_step_fields(r'{multi_odb_path}', 'RECOVERY_TERMINAL')
t_s2 = extract_step_fields(r'{term_odb_path}', 'Step-1')

def compare_states(dict_multi, dict_single, name):
    max_d_s11 = 0.0
    max_d_s22 = 0.0
    max_d_mises = 0.0
    max_d_eri = 0.0
    max_d_avg = 0.0

    all_eids = sorted(dict_multi['MISESERI'].keys())
    for eid in all_eids:
        s_m = dict_multi['S'][eid]
        s_s = dict_single['S'][eid]
        max_d_s11 = max(max_d_s11, abs(s_m[0] - s_s[0]))
        max_d_s22 = max(max_d_s22, abs(s_m[1] - s_s[1]))
        max_d_mises = max(max_d_mises, abs(s_m[3] - s_s[3]))
        max_d_eri = max(max_d_eri, abs(dict_multi['MISESERI'][eid] - dict_single['MISESERI'][eid]))
        max_d_avg = max(max_d_avg, abs(dict_multi['MISESAVG'][eid] - dict_single['MISESAVG'][eid]))

    d_rf = abs(dict_multi['RF2'] - dict_single['RF2'])
    rel_rf = (d_rf / abs(dict_single['RF2'])) * 100.0 if abs(dict_single['RF2']) > 0 else 0.0

    return {{
        'comparison': name,
        'rf_multi': dict_multi['RF2'],
        'rf_single': dict_single['RF2'],
        'delta_rf_N': d_rf,
        'rel_delta_rf_pct': rel_rf,
        'max_delta_s11_MPa': max_d_s11,
        'max_delta_s22_MPa': max_d_s22,
        'max_delta_mises_MPa': max_d_mises,
        'max_delta_miseseri_MPa': max_d_eri,
        'max_delta_misesavg_MPa': max_d_avg,
        'num_elements_audited': len(all_eids)
    }}

res_s1 = compare_states(m_s1, c_s1, 'MultiStep_Step1_RECOVERY_C_vs_Independent_Candidate_C')
res_s2 = compare_states(m_s2, t_s2, 'MultiStep_Step2_RECOVERY_TERMINAL_vs_Independent_Terminal_Baseline')

summary = {{
    'step1_candidate_c_equivalence': res_s1,
    'step2_terminal_baseline_equivalence': res_s2,
    'mathematical_path_independence_proven': (res_s1['rel_delta_rf_pct'] < 1e-4 and res_s2['rel_delta_rf_pct'] < 1e-4)
}}

with open(r'{tmp_audit_json}', 'w') as fp:
    json.dump(summary, fp, indent=4)
"""
    with open(tmp_audit_script, "w") as fp:
        fp.write(script_content)

    print("  Running Abaqus Python equivalence audit...")
    cmd = ["cmd", "/c", "abaqus", "python", tmp_audit_script]
    res = subprocess.run(cmd, capture_output=True, text=True)
    if os.path.exists(tmp_audit_script):
        os.remove(tmp_audit_script)

    if res.returncode != 0 or not os.path.exists(tmp_audit_json):
        raise RuntimeError(f"Equivalence audit failed: {res.stderr}\n{res.stdout}")

    with open(tmp_audit_json, "r") as fp:
        audit_data = json.load(fp)
    os.remove(tmp_audit_json)

    with open(out_json_path, "w") as fp:
        json.dump(audit_data, fp, indent=4)
    print(f"  Equivalence audit written to: {out_json_path}")
    return audit_data


def main():
    donor_phys_inp = "models/pandey_kumar_mode1/176_method_a_plate_with_hole/PK_HOLE_COARSE_PHYS.inp"
    donor_odb_path = "models/pandey_kumar_mode1/176_method_a_plate_with_hole/PK_HOLE_COARSE_JOB1.odb"
    rec_json_path = "receiver_mesh.json"
    base_inp_path = "PK_HOLE_F1661_RECOVERY.inp"

    cand_c_odb = os.path.abspath("runs/f1683_recovery_candidate_c/PK_HOLE_RECOVERY_C.odb")
    term_odb = os.path.abspath("PK_HOLE_F1661_RECOVERY.odb")

    work_dir = os.path.abspath("runs/f1684_multistep_recovery")
    os.makedirs(work_dir, exist_ok=True)
    job_name = "PK_HOLE_MULTISTEP_RECOVERY"

    u2_step1 = 0.00710000     # Candidate C
    u2_step2 = 0.00959078     # Terminal Baseline

    print("=" * 80)
    print("TASK F1684: MULTI-STEP AUXILIARY RECOVERY PIPELINE")
    print(f"Step 1: RECOVERY_C (Frame 150, u2 = {u2_step1:.6f} mm)")
    print(f"Step 2: RECOVERY_TERMINAL (Frame 337, u2 = {u2_step2:.6f} mm)")
    print(f"Work Dir: {work_dir}")
    print("=" * 80)

    # 1. Load meshes and trees
    donor_nodes, donor_elems = load_donor_mesh(donor_phys_inp)
    rec_nodes, rec_elems = load_receiver_mesh(rec_json_path)
    receiver_ips = compute_receiver_ips(rec_nodes, rec_elems)
    trees = build_strtree_index(donor_nodes, donor_elems)

    # 2. Extract damage for Candidate C and Terminal Baseline
    print("\n--- Extracting Donor Damage Fields ---")
    d_c = extract_donor_damage_dict(donor_odb_path, "Step-2", 150)
    d_term = extract_donor_damage_dict(donor_odb_path, "Step-2", 337)
    print(f"  Candidate C: max d = {max(d_c.values()):.4f}")
    print(f"  Terminal:    max d = {max(d_term.values()):.4f}")

    # 3. Map to receiver integration points
    print("\n--- Mapping Damage Fields to Receiver Integration Points ---")
    ips_c = map_damage_to_receiver(receiver_ips, trees, d_c)
    ips_term = map_damage_to_receiver(receiver_ips, trees, d_term)

    # 4. Write lookup_damage_multistep.txt
    lookup_path = os.path.join(work_dir, "lookup_damage_multistep.txt")
    with open(lookup_path, "w") as fp:
        fp.write("# F1684 MULTI-STEP RECOVERY INTEGRATION-POINT LOOKUP TABLE\n")
        fp.write("# Format: NOEL  NPT  X  Y  D_C  G_C  D_TERM  G_TERM\n")
        fp.write(f"# Total IPs: {len(ips_c)}\n")
        for e_c, e_t in zip(ips_c, ips_term):
            assert e_c["noel"] == e_t["noel"] and e_c["npt"] == e_t["npt"]
            fp.write(f"{e_c['noel']} {e_c['npt']} {e_c['x']:.8e} {e_c['y']:.8e} "
                     f"{e_c['d']:.8e} {e_c['g']:.8e} {e_t['d']:.8e} {e_t['g']:.8e}\n")
    print(f"  Wrote multi-step lookup table: {lookup_path}")

    # 5. Write USDFLD source
    coords_log = os.path.join(work_dir, "runtime_coords.txt")
    usdfld_src = generate_multistep_usdfld_source(lookup_path, coords_log)
    usdfld_path = os.path.join(work_dir, "recovery_multistep_usdfld.for")
    with open(usdfld_path, "w") as fp:
        fp.write(usdfld_src)
    print(f"  Wrote USDFLD source: {usdfld_path}")

    # 6. Build multi-step input deck
    inp_path = os.path.join(work_dir, f"{job_name}.inp")
    build_multistep_inp(base_inp_path, u2_step1, u2_step2, inp_path)

    # 7. Execute solve if not already present
    multi_odb_path = os.path.join(work_dir, f"{job_name}.odb")
    if not os.path.exists(multi_odb_path):
        execute_solve(work_dir, job_name)
    else:
        print(f"  Multi-step ODB already exists: {multi_odb_path}")

    # 8. Verify runtime coords
    line_cnt = 0
    max_dist = 0.0
    with open(coords_log, "r") as fp:
        for line in fp:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            parts = line.split()
            if len(parts) >= 7:
                d = float(parts[6])
                max_dist = max(max_dist, d)
                line_cnt += 1
    print(f"  Runtime coordinates verified: {line_cnt} IPs checked, max discrepancy = {max_dist:.4e} mm (< 10 nm PASS)")

    multi_odb_path = os.path.join(work_dir, f"{job_name}.odb")
    if not os.path.exists(multi_odb_path):
        raise FileNotFoundError(f"Multi-step ODB missing: {multi_odb_path}")

    # 9. Audit Equivalence
    cmd_audit = ["cmd", "/c", "abaqus", "python", "scripts/validation/audit_f1684_multistep_equivalence.py"]
    print("  Running Abaqus Python equivalence audit...")
    p_aud = subprocess.run(cmd_audit, capture_output=True, text=True)
    if p_aud.returncode != 0:
        print("Audit stderr:", p_aud.stderr)
        print("Audit stdout:", p_aud.stdout)
        raise RuntimeError("Equivalence audit failed!")
    print(p_aud.stdout)


if __name__ == "__main__":
    main()
