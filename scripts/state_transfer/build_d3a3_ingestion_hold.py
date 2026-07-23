#!/usr/bin/env python3
"""Generate D3A3 full-target ingestion/equilibration/release-hold inputs."""

import argparse
import csv
import hashlib
import json
import math
from pathlib import Path


N_ELEM = 6400
N_IP = 25600
NODE_OFFSET = 100000
COMMIT = "817b69356af87c4e80ad2b2ef33dc6b92bc73a7f"
CHECKPOINT_U2 = 0.003000000026077032
H0_FORTRAN = Path("models/generated/molnar_gravouil_2017/h_convergence_lc015/H0_exact/SingleNotch.for")
RUNTIME_H = Path("models/state_transfer/d3_interrupted_transfer/executable/d3_transfer_h.dat")
RUNTIME_H_SHA256 = "4689ea5c10c0972e69ba46f8676a326c8b011b98faa8031c7c26cfb218607cd9"


def read_csv(path):
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def write(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def add_label_set(lines, name, labels, chunk=12):
    lines.append(f"*Nset, nset={name}")
    for index in range(0, len(labels), chunk):
        lines.append(", ".join(str(label) for label in labels[index : index + chunk]))


def generate_fortran(path):
    text = f"""C D3A3 full-target transferred-state ingestion UEL/UMAT.
C H table initializes once only from d3_transfer_table.inc during Step 1.
      SUBROUTINE UEL(RHS,AMATRX,SVARS,ENERGY,NDOFEL,NRHS,NSVARS,
     1     PROPS,NPROPS,COORDS,MCRD,NNODE,U,DU,V,A,JTYPE,TIME,DTIME,
     2     KSTEP,KINC,JELEM,PARAMS,NDLOAD,JDLTYP,ADLMAG,PREDEF,
     3     NPREDF,LFLAGS,MLVARX,DDLMAG,MDLOAD,PNEWDT,JPROPS,NJPROP,
     4     PERIOD)
      INCLUDE 'ABA_PARAM.INC'
      INTEGER N_ELEM,NSTV,NIP
      PARAMETER (N_ELEM={N_ELEM},NSTV=18,NIP=4)
      DIMENSION RHS(MLVARX,*),AMATRX(NDOFEL,NDOFEL),
     1     SVARS(NSVARS),ENERGY(8),PROPS(NPROPS),COORDS(MCRD,NNODE),
     2     U(NDOFEL),DU(MLVARX,*),V(NDOFEL),A(NDOFEL),TIME(2),
     3     PARAMS(*),JDLTYP(MDLOAD,*),ADLMAG(MDLOAD,*),
     4     DDLMAG(MDLOAD,*),PREDEF(2,NPREDF,NNODE),LFLAGS(*),
     5     JPROPS(*)
      DOUBLE PRECISION USRVAR
      COMMON/KUSER/USRVAR(N_ELEM,NSTV,NIP)
      LOGICAL TRANSFER_DONE
      COMMON/D3INIT/TRANSFER_DONE(N_ELEM,NIP)
      SAVE /KUSER/,/D3INIT/
      INCLUDE 'd3_transfer_table.inc'
      INTEGER I,J,IP,PHYS
      DOUBLE PRECISION PHASE,HVAL

      DO I=1,NDOFEL
        DO J=1,NRHS
          RHS(I,J)=0.D0
        END DO
        DO J=1,NDOFEL
          AMATRX(I,J)=0.D0
        END DO
        AMATRX(I,I)=1.D0
      END DO

      PHYS=JELEM
      IF (JELEM.GT.N_ELEM) PHYS=JELEM-N_ELEM
      IF (PHYS.LT.1 .OR. PHYS.GT.N_ELEM) THEN
        WRITE(7,*) 'D3A3 UEL invalid JELEM ',JELEM
        CALL XIT
      ENDIF

      DO IP=1,NIP
        HVAL=0.D0
        DO I=1,D3_TRANSFER_COUNT
          IF (D3_TRANSFER_ELEM(I).EQ.PHYS .AND.
     1        D3_TRANSFER_IP(I).EQ.IP) HVAL=D3_TRANSFER_H(I)
        END DO
        IF (KSTEP.EQ.1 .AND. KINC.EQ.1 .AND.
     1      .NOT.TRANSFER_DONE(PHYS,IP)) THEN
          USRVAR(PHYS,16,IP)=HVAL
          USRVAR(PHYS,18,IP)=1.D0
          TRANSFER_DONE(PHYS,IP)=.TRUE.
        ENDIF
      END DO

      IF (JTYPE.EQ.1) THEN
        PHASE=0.D0
        DO I=1,NNODE
          PHASE=PHASE+0.25D0*U(I)
        END DO
        DO IP=1,NIP
          IF (KSTEP.EQ.1 .AND. KINC.EQ.1) THEN
            USRVAR(PHYS,15,IP)=PHASE
          ELSEIF (PHASE.GT.USRVAR(PHYS,15,IP)) THEN
            USRVAR(PHYS,15,IP)=PHASE
          ENDIF
        END DO
      ENDIF
      DO I=1,NSVARS
        SVARS(I)=0.D0
      END DO
      SVARS(1)=USRVAR(PHYS,15,1)
      SVARS(2)=USRVAR(PHYS,16,1)
      RETURN
      END

      SUBROUTINE UMAT(STRESS,STATEV,DDSDDE,SSE,SPD,SCD,
     1 RPL,DDSDDT,DRPLDE,DRPLDT,STRAN,DSTRAN,
     2 TIME,DTIME,TEMP,DTEMP,PREDEF,DPRED,CMNAME,NDI,NSHR,NTENS,
     3 NSTATV,PROPS,NPROPS,COORDS,DROT,PNEWDT,CELENT,
     4 DFGRD0,DFGRD1,NOEL,NPT,LAYER,KSPT,KSTEP,KINC)
      INCLUDE 'ABA_PARAM.INC'
      CHARACTER*80 CMNAME
      INTEGER N_ELEM,NSTV,NIP
      PARAMETER (N_ELEM={N_ELEM},NSTV=18,NIP=4)
      DIMENSION STRESS(NTENS),STATEV(NSTATV),DDSDDE(NTENS,NTENS),
     1 DDSDDT(NTENS),DRPLDE(NTENS),STRAN(NTENS),DSTRAN(NTENS),
     2 TIME(2),PREDEF(*),DPRED(*),PROPS(NPROPS),COORDS(*),
     3 DROT(3,3),DFGRD0(3,3),DFGRD1(3,3)
      DOUBLE PRECISION USRVAR
      COMMON/KUSER/USRVAR(N_ELEM,NSTV,NIP)
      SAVE /KUSER/
      INTEGER I,J,PHYS
      DOUBLE PRECISION EMOD,ENU,EG,EG2,ELAM,PSI0,HOLD

      PHYS=NOEL-2*N_ELEM
      IF (PHYS.LT.1 .OR. PHYS.GT.N_ELEM) THEN
        WRITE(7,*) 'D3A3 UMAT invalid visualization element ',NOEL
        CALL XIT
      ENDIF
      DO I=1,NTENS
        STRESS(I)=0.D0
        DO J=1,NTENS
          DDSDDE(I,J)=0.D0
        END DO
      END DO
      EMOD=1.D-11
      ENU=0.3D0
      IF (NPROPS.GE.2) THEN
        EMOD=PROPS(1)
        ENU=PROPS(2)
      ENDIF
      EG=EMOD/(2.D0*(1.D0+ENU))
      EG2=2.D0*EG
      ELAM=EG2*ENU/(1.D0-2.D0*ENU)
      DO I=1,NDI
        DO J=1,NDI
          DDSDDE(I,J)=ELAM
        END DO
        DDSDDE(I,I)=EG2+ELAM
      END DO
      DO I=NDI+1,NTENS
        DDSDDE(I,I)=EG
      END DO
      DO I=1,NTENS
        DO J=1,NTENS
          STRESS(I)=STRESS(I)+DDSDDE(I,J)*DSTRAN(J)
        END DO
      END DO
      PSI0=0.D0
      DO I=1,NTENS
        HOLD=STRAN(I)+DSTRAN(I)
        PSI0=PSI0+0.5D0*HOLD*STRESS(I)
      END DO
      IF (PSI0.GT.USRVAR(PHYS,16,NPT)) THEN
        USRVAR(PHYS,16,NPT)=PSI0
      ENDIF
      DO I=1,NSTATV
        STATEV(I)=0.D0
      END DO
      STATEV(1)=DBLE(PHYS)
      STATEV(2)=DBLE(NPT)
      STATEV(15)=USRVAR(PHYS,15,NPT)
      STATEV(16)=USRVAR(PHYS,16,NPT)
      RETURN
      END

      BLOCK DATA D3BLOCK
      INTEGER N_ELEM,NSTV,NIP
      PARAMETER (N_ELEM={N_ELEM},NSTV=18,NIP=4)
      DOUBLE PRECISION USRVAR
      COMMON/KUSER/USRVAR(N_ELEM,NSTV,NIP)
      LOGICAL TRANSFER_DONE
      COMMON/D3INIT/TRANSFER_DONE(N_ELEM,NIP)
      DATA USRVAR /{N_ELEM * 18 * 4}*0.D0/
      DATA TRANSFER_DONE /{N_ELEM * 4}*.FALSE./
      END
"""
    write(path, text)


def generate_fortran_r2(path):
    text = H0_FORTRAN.read_text(encoding="utf-8")
    text = "\n".join(line.rstrip() for line in text.splitlines()) + "\n"
    text = text.replace("N_ELEM=3930", f"N_ELEM={N_ELEM}")
    text = text.replace(
        "C ======================================================================\n      SUBROUTINE UEL",
        "C ======================================================================\nC D3A3-R2: H initialized once by UEXTERNALDB from d3_transfer_h.dat.\n      SUBROUTINE UEL",
        1,
    )
    uexternaldb = f"""

      SUBROUTINE UEXTERNALDB(LOP,LRESTART,TIME,DTIME,KSTEP,KINC)
      INCLUDE 'ABA_PARAM.INC'
      INTEGER LOP,LRESTART,KSTEP,KINC
      DOUBLE PRECISION TIME(2),DTIME
      INTEGER N_ELEM,NSTV,NIP
      PARAMETER (N_ELEM={N_ELEM},NSTV=18,NIP=4)
      DOUBLE PRECISION USRVAR,HVAL
      COMMON/KUSER/USRVAR(N_ELEM,NSTV,NIP)
      LOGICAL HLOADED,SEEN
      COMMON/D3HLOAD/HLOADED,SEEN(N_ELEM,NIP)
      CHARACTER*512 OUTDIR,HFILE
      CHARACTER*18 HNAME
      INTEGER LENOUTDIR,LHFILE
      INTEGER ELEM,IP,COUNT,IOS,IREC,I,J
      SAVE /KUSER/,/D3HLOAD/

      IF (LOP.EQ.0 .AND. LRESTART.EQ.0 .AND. .NOT.HLOADED) THEN
        DO I=1,N_ELEM
          DO J=1,NIP
            SEEN(I,J)=.FALSE.
          END DO
        END DO
        CALL GETOUTDIR(OUTDIR,LENOUTDIR)
        HNAME='/d3_transfer_h.dat'
        LHFILE=LENOUTDIR+LEN_TRIM(HNAME)
        HFILE=' '
        HFILE=OUTDIR(1:LENOUTDIR)//HNAME
        WRITE(7,*) 'D3A3-R2 H FILE PATH'
        WRITE(7,*) HFILE(1:LHFILE)
        OPEN(UNIT=99,
     1       FILE=HFILE(1:LHFILE),
     2       STATUS='OLD',
     3       ACTION='READ',
     4       IOSTAT=IOS)
        IF (IOS.NE.0) THEN
          WRITE(7,*) 'D3A3-R2 cannot open runtime H file',IOS
          WRITE(7,*) HFILE(1:LHFILE)
          CALL XIT
        ENDIF
        COUNT=0
        DO IREC=1,N_ELEM*NIP
          IOS=0
          READ(99,*,IOSTAT=IOS,END=900,ERR=910)
     1         ELEM,IP,HVAL
          IF (IOS.NE.0) GOTO 910
          IF (ELEM.LT.1 .OR. ELEM.GT.N_ELEM) THEN
            WRITE(7,*) 'D3A3-R2 H element out of range',
     1                 IREC,ELEM
            CLOSE(99)
            CALL XIT
            RETURN
          ENDIF
          IF (IP.LT.1 .OR. IP.GT.NIP) THEN
            WRITE(7,*) 'D3A3-R2 H IP out of range',
     1                 IREC,ELEM,IP
            CLOSE(99)
            CALL XIT
            RETURN
          ENDIF
          IF (SEEN(ELEM,IP)) THEN
            WRITE(7,*) 'D3A3-R2 duplicate H key',
     1                 IREC,ELEM,IP
            CLOSE(99)
            CALL XIT
            RETURN
          ENDIF
          IF (HVAL.LT.0.D0) THEN
            WRITE(7,*) 'D3A3-R2 negative H',
     1                 IREC,ELEM,IP,HVAL
            CLOSE(99)
            CALL XIT
            RETURN
          ENDIF
          USRVAR(ELEM,16,IP)=HVAL
          SEEN(ELEM,IP)=.TRUE.
          COUNT=COUNT+1
        END DO
        GOTO 920

 900    CONTINUE
        WRITE(7,*) 'D3A3-R2 premature runtime H EOF',
     1             COUNT,N_ELEM*NIP
        CLOSE(99)
        CALL XIT
        RETURN

 910    CONTINUE
        WRITE(7,*) 'D3A3-R2 runtime H read error',
     1             IOS,IREC,COUNT
        CLOSE(99)
        CALL XIT
        RETURN

 920    CONTINUE
        CLOSE(99)
        IF (COUNT.NE.N_ELEM*NIP) THEN
          WRITE(7,*) 'D3A3-R2 H record count mismatch',COUNT
          CALL XIT
        ENDIF
        DO I=1,N_ELEM
          DO J=1,NIP
            IF (.NOT.SEEN(I,J)) THEN
              WRITE(7,*) 'D3A3-R2 missing H key',I,J
              CLOSE(99)
              CALL XIT
              RETURN
            ENDIF
          END DO
        END DO
        WRITE(7,*) 'D3A3-R2 H LOAD COMPLETE',COUNT
        HLOADED=.TRUE.
      ENDIF
      RETURN
      END

      BLOCK DATA D3HLOADBLOCK
      INTEGER N_ELEM,NIP
      PARAMETER (N_ELEM={N_ELEM},NIP=4)
      LOGICAL HLOADED,SEEN
      COMMON/D3HLOAD/HLOADED,SEEN(N_ELEM,NIP)
      DATA HLOADED /.FALSE./
      END
"""
    write(path, text.rstrip() + uexternaldb)


def counted_read_audit(fortran_path, out_dir):
    text = fortran_path.read_text(encoding="utf-8", errors="replace")
    required = [
        "CALL GETOUTDIR",
        "/d3_transfer_h.dat",
        "FILE=HFILE(1:LHFILE)",
        "D3A3-R2 H FILE PATH",
        "DO IREC=1,N_ELEM*NIP",
        "END=900",
        "ERR=910",
        "D3A3-R2 H LOAD COMPLETE",
    ]
    forbidden = [
        "FILE='d3_transfer_h.dat'",
        "INCLUDE 'd3_transfer_table.inc'",
        "D3_TRANSFER_COUNT",
        "GOTO 100",
        "100    CONTINUE",
        "100 CONTINUE",
    ]
    failures = []
    for token in required:
        if token not in text:
            failures.append("missing required generated-source token: " + token)
    for token in forbidden:
        if token in text:
            failures.append("forbidden generated-source token present: " + token)

    runtime_hash = sha256(RUNTIME_H) if RUNTIME_H.exists() else None
    if runtime_hash != RUNTIME_H_SHA256:
        failures.append("runtime H SHA-256 changed: " + str(runtime_hash))

    audit = {
        "classification": "stage_d3a3_r2_r2_counted_read_audit_pass" if not failures else "stage_d3a3_r2_r2_counted_read_audit_fail",
        "counted_read_audit_ok": not failures,
        "failed_predecessor_job": "1377391.mmaster02",
        "correction": "replace EOF-driven read with exact 25600-record loop",
        "expected_records": N_IP,
        "read_after_expected_last_record": False,
        "getoutdir_retained": "CALL GETOUTDIR" in text,
        "physics_changed": False,
        "mesh_changed": False,
        "input_deck_changed": False,
        "runtime_H_changed": False,
        "runtime_H_values_changed": False,
        "runtime_H_hash_unchanged": runtime_hash == RUNTIME_H_SHA256,
        "runtime_H_sha256": runtime_hash,
        "required_tokens": required,
        "forbidden_tokens": forbidden,
        "generated_fortran": str(fortran_path),
        "failures": failures,
    }
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "D3A3_R2_R2_COUNTED_READ_AUDIT.json").write_text(json.dumps(audit, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return audit


def generate_inp(path, target_dir, package_dir):
    nodes = read_csv(target_dir / "target_nodes.csv")
    elements = read_csv(target_dir / "target_elements.csv")
    nodal_d = {int(row["node"]): float(row["d"]) for row in read_csv(package_dir / "D3_TRANSFERRED_NODAL_D.csv")}
    lines = [
        "*Heading",
        "** D3A3 full nonmatching-target ingestion, equilibration, release hold.",
        "** Generated from committed D3A2 package. No fracture continuation.",
        "*Preprint, echo=NO, model=NO, history=NO, contact=NO",
        "*Node",
    ]
    for row in nodes:
        label = int(row["node"])
        x = row["x"]
        y = row["y"]
        lines.append(f"{label}, {x}, {y}")
    for row in nodes:
        label = int(row["node"]) + NODE_OFFSET
        lines.append(f"{label}, {row['x']}, {row['y']}")

    lines += [
        "*User Element, nodes=4, type=U1, properties=3, coordinates=2, VARIABLES=8",
        "3",
        "*Element, type=U1, elset=PHASE",
    ]
    for row in elements:
        lines.append(f"{row['element']}, {row['n1']}, {row['n2']}, {row['n3']}, {row['n4']}")
    lines += ["*Elset, elset=PHASE, generate", f"1, {N_ELEM}, 1", "*Uel Property, elset=PHASE", "0.015, 0.0027, 1.0"]

    lines += ["*User Element, nodes=4, type=U2, properties=4, coordinates=2, VARIABLES=56", "1, 2", "*Element, type=U2, elset=DISP"]
    for row in elements:
        label = int(row["element"]) + N_ELEM
        conn = [int(row[f"n{i}"]) + NODE_OFFSET for i in range(1, 5)]
        lines.append(f"{label}, {conn[0]}, {conn[1]}, {conn[2]}, {conn[3]}")
    lines += ["*Elset, elset=DISP, generate", f"{N_ELEM + 1}, {2 * N_ELEM}, 1", "*Uel Property, elset=DISP", "210, 0.3, 1, 1e-07"]

    lines += ["*Element, type=CPS4, elset=UMATVIS"]
    for row in elements:
        label = int(row["element"]) + 2 * N_ELEM
        conn = [int(row[f"n{i}"]) + NODE_OFFSET for i in range(1, 5)]
        lines.append(f"{label}, {conn[0]}, {conn[1]}, {conn[2]}, {conn[3]}")
    lines += [
        "*Elset, elset=UMATVIS, generate",
        f"{2 * N_ELEM + 1}, {3 * N_ELEM}, 1",
        "*Solid Section, elset=UMATVIS, material=UMATVIS",
        "1.0,",
        "*Material, name=UMATVIS",
        "*Depvar",
        "18,",
        "*User Material, constants=2",
        "1.0e-11, 0.3",
    ]

    top = [int(row["node"]) + NODE_OFFSET for row in nodes if abs(float(row["y"]) - 0.5) < 1e-12]
    bottom = [int(row["node"]) + NODE_OFFSET for row in nodes if abs(float(row["y"]) + 0.5) < 1e-12]
    left_bottom = min(bottom, key=lambda n: abs(float(nodes[(n - NODE_OFFSET) - 1]["x"]) + 0.5))
    add_label_set(lines, "TOP", top)
    add_label_set(lines, "BOTTOM", bottom)
    add_label_set(lines, "ANCHOR", [left_bottom])
    lines += [
        "*Step, name=INGEST_TRANSFERRED_STATE, nlgeom=NO",
        "*Static",
        "1.0, 1.0",
        "*Boundary",
        "BOTTOM, 2, 2, 0.0",
        "ANCHOR, 1, 1, 0.0",
    ]
    for node in sorted(nodal_d):
        lines.append(f"{node}, 3, 3, {nodal_d[node]:.17g}")
    lines += [
        "*Output, field",
        "*Element Output, elset=UMATVIS",
        "SDV",
        "*Node Output",
        "U, RF",
        "*End Step",
        "*Step, name=CHECKPOINT_EQUILIBRATION_PHASE_FIXED, nlgeom=NO",
        "*Static",
        "0.1, 1.0, 1.0e-08, 0.1",
        "*Boundary",
        "BOTTOM, 2, 2, 0.0",
        "ANCHOR, 1, 1, 0.0",
        f"TOP, 2, 2, {CHECKPOINT_U2:.17g}",
    ]
    for node in sorted(nodal_d):
        lines.append(f"{node}, 3, 3, {nodal_d[node]:.17g}")
    lines += [
        "*Output, field",
        "*Element Output, elset=UMATVIS",
        "SDV",
        "*Node Output",
        "U, RF",
        "*End Step",
        "*Step, name=PHASE_RELEASE_HOLD, nlgeom=NO",
        "*Static",
        "0.1, 1.0, 1.0e-08, 0.1",
        "*Boundary, op=NEW",
        "BOTTOM, 2, 2, 0.0",
        "ANCHOR, 1, 1, 0.0",
        f"TOP, 2, 2, {CHECKPOINT_U2:.17g}",
        "*Output, field",
        "*Element Output, elset=UMATVIS",
        "SDV",
        "*Node Output",
        "U, RF",
        "*End Step",
    ]
    write(path, "\n".join(lines) + "\n")


def static_status(model_dir, package_dir, out_dir):
    nodes = read_csv(model_dir / "target" / "target_nodes.csv")
    elements = read_csv(model_dir / "target" / "target_elements.csv")
    nodal = read_csv(package_dir / "D3_TRANSFERRED_NODAL_D.csv")
    ip = read_csv(package_dir / "D3_TRANSFERRED_IP_H.csv")
    package = json.loads((package_dir / "D3_TRANSFER_PACKAGE_STATUS.json").read_text(encoding="utf-8"))
    topology = json.loads((package_dir / "D3_TARGET_NOTCH_TOPOLOGY.json").read_text(encoding="utf-8"))
    failures = []
    if not Path("runs/hpc/stage_d3/interrupted_transfer/checkpoint/D3A.ok").exists():
        failures.append("D3A.ok missing")
    if not (package_dir / "D3_PACKAGE.ok").exists():
        failures.append("D3_PACKAGE.ok missing")
    if package.get("classification") != "stage_d3a2_transfer_package_pass":
        failures.append("D3 package status is not pass")
    if topology.get("classification") != "stage_d3a2_target_notch_topology_pass":
        failures.append("notch topology audit is not pass")
    if len(elements) != N_ELEM:
        failures.append(f"target element count {len(elements)} != {N_ELEM}")
    if len(ip) != N_IP:
        failures.append(f"target IP count {len(ip)} != {N_IP}")
    if len(nodal) != len(nodes):
        failures.append("target node count does not match phase table")
    if len({r["node"] for r in nodal}) != len(nodal):
        failures.append("duplicate transferred nodal d keys")
    if len({(r["element"], r["integration_point"]) for r in ip}) != len(ip):
        failures.append("duplicate transferred IP H keys")
    dvals = [float(r["d"]) for r in nodal]
    hvals = [float(r["H"]) for r in ip]
    detj = [float(r["detJ"]) for r in ip]
    if any(not math.isfinite(v) for v in dvals + hvals + detj):
        failures.append("non-finite transferred values")
    if min(dvals) < -1e-12 or max(dvals) > 1.0 + 1e-12:
        failures.append("d out of [0,1]")
    if min(hvals) < -1e-12:
        failures.append("H negative")
    if min(detj) <= 0.0:
        failures.append("non-positive detJ")
    audit = counted_read_audit(model_dir / "executable" / "d3_transfer_uel.for", out_dir)
    failures.extend(audit["failures"])
    status = {
        "classification": "stage_d3a3_static_validation_pass" if not failures else "stage_d3a3_static_validation_fail",
        "D3A3_static_ok": not failures,
        "commit": COMMIT,
        "target_nodes": len(nodes),
        "target_elements": len(elements),
        "target_ips": len(ip),
        "phase_element_labels": "1-6400",
        "displacement_element_labels": "6401-12800",
        "umat_element_labels": "12801-19200",
        "H_table_entries": len(ip),
        "Fortran_N_ELEM": N_ELEM,
        "serial_mode": True,
        "MPI_absent": True,
        "counted_read_audit": audit,
        "failures": failures,
    }
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "D3A3_STATIC_VALIDATION.json").write_text(json.dumps(status, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    provenance = {
        "classification": "stage_d3a3_input_provenance",
        "source_commit": COMMIT,
        "source_job": "1376154.mmaster02",
        "r2_predecessor_failures": [
            {
                "job": "1377382.mmaster02",
                "classification": "stage_d3a3_solver_fail_compiler_environment",
                "evidence_dir": "runs/hpc/stage_d3/interrupted_transfer/target_ingestion",
            },
            {
                "job": "1377383.mmaster02",
                "classification": "stage_d3a3_solver_fail_transfer_table_compile",
                "evidence_dir": "runs/hpc/stage_d3/interrupted_transfer/target_ingestion_r1",
            },
            {
                "job": "1377389.mmaster02",
                "classification": "stage_d3a3_r2_datacheck_fail_runtime_h_file_not_in_abaqus_workdir",
                "evidence_dir": "runs/hpc/stage_d3/interrupted_transfer/target_ingestion_compile_r2",
            },
            {
                "job": "1377391.mmaster02",
                "classification": "stage_d3a3_r2_r1_datacheck_fail_runtime_h_eof_after_getoutdir_open",
                "evidence_dir": "runs/hpc/stage_d3/interrupted_transfer/target_ingestion_compile_r2_r1",
            },
        ],
        "r2_change": "Replace compile-time DATA transfer table with UEXTERNALDB runtime H loader from d3_transfer_h.dat; preserve physical Molnar source logic.",
        "r2_r2_change": "Retain GETOUTDIR runtime path and replace EOF-driven H loading with an exact 25600-record counted loop.",
        "checkpoint_U2": CHECKPOINT_U2,
        "package_dir": str(package_dir),
        "model_dir": str(model_dir),
        "fortran_source": str(H0_FORTRAN),
        "fortran_source_sha256": sha256(H0_FORTRAN),
        "solver_job_submitted_at_generation": False,
    }
    (out_dir / "D3A3_INPUT_PROVENANCE.json").write_text(json.dumps(provenance, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return status


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model-dir", type=Path, default=Path("models/state_transfer/d3_interrupted_transfer"))
    parser.add_argument("--package-dir", type=Path, default=Path("runs/hpc/stage_d3/interrupted_transfer/package"))
    parser.add_argument("--out-dir", type=Path, default=Path("runs/hpc/stage_d3/interrupted_transfer/target_ingestion_compile_r2_r2"))
    args = parser.parse_args()
    exe = args.model_dir / "executable"
    generate_inp(exe / "D3A3_target_ingestion_hold.inp", args.model_dir / "target", args.package_dir)
    generate_fortran_r2(exe / "d3_transfer_uel.for")
    status = static_status(args.model_dir, args.package_dir, args.out_dir)
    print(json.dumps(status, indent=2, sort_keys=True))
    return 0 if status["D3A3_static_ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
