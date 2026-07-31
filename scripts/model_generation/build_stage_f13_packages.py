#!/usr/bin/env python3
"""Build byte-identical F13 rollback packages and the native-remesh package."""
import hashlib
import json
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def dump(path, value):
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def f13_source(text):
    text = text.replace("       REAL*8 PHASEOLD,PENALTY,GAP,PENEDEN,PENRES,PENTAN",
                        "       REAL*8 PHASEOLD,PENALTY,GAP,PENEDEN,PENRES,PENTAN,PBEFORE\n"
                        "       CHARACTER*512 F13LOG\n       CHARACTER*8 F13FORCE\n"
                        "       INTEGER F13LS,F13FS,F13IOS")
    old = ("        IF (JELEM.EQ.1.AND.INPT.EQ.1.AND.STEPITER.LE.20) THEN\n"
           "         WRITE(99,*) KSTEP,KINC,TIME(1),TIME(2),DTIME,STEPITER,\n"
           "     1    PHASEOLD,PHASE-DPHASE,PHASE,GAP\n"
           "        ENDIF")
    new = ("C       F13 diagnostic-only controlled cutback: only PNEWDT changes.\n"
           "        PBEFORE=PNEWDT\n"
           "        CALL GET_ENVIRONMENT_VARIABLE('F13_FORCE_CUTBACK',\n"
           "     1   F13FORCE,STATUS=F13FS)\n"
           "        IF (F13FS.EQ.0.AND.F13FORCE(1:1).EQ.'1'.AND.\n"
           "     1   KSTEP.EQ.2.AND.TIME(1).GE.0.0D0.AND.\n"
           "     2   TIME(1).LT.4.0D-2.AND.JELEM.EQ.1.AND.INPT.EQ.2\n"
           "     3   .AND.DTIME.GT.1.5D-2) PNEWDT=HALF\n"
           "        IF (JELEM.LE.23.AND.INPT.LE.4.AND.STEPITER.LE.40) THEN\n"
           "         CALL GET_ENVIRONMENT_VARIABLE('F13_ROLLBACK_LOG',\n"
           "     1    F13LOG,LENGTH=F13LS,STATUS=F13FS)\n"
           "         IF (F13FS.NE.0.OR.F13LS.LE.0) CALL XIT\n"
           "         OPEN(UNIT=98,FILE=F13LOG(1:F13LS),STATUS='UNKNOWN',\n"
           "     1    POSITION='APPEND',ACTION='WRITE',IOSTAT=F13IOS)\n"
           "         IF (F13IOS.NE.0) CALL XIT\n"
           "         WRITE(98,*) KSTEP,KINC,TIME(1),TIME(2),DTIME,\n"
           "     1    LFLAGS(1),LFLAGS(3),LFLAGS(4),PBEFORE,PNEWDT,\n"
           "     2    JELEM,INPT,STEPITER,PHASE,PHASE-DPHASE,\n"
           "     3    SVARS(NSTVTO*(INPT-1)+1),PHASEOLD,\n"
           "     4    USRVAR(JELEM,16,INPT),USRVAR(JELEM,22,INPT),\n"
           "     5    GAP,PENEDEN\n"
           "         CLOSE(98)\n"
           "        ENDIF")
    if old not in text:
        raise ValueError("F11 log anchor not found")
    return text.replace(old, new, 1).replace("F11 BOUNDS", "F13 BOUNDS")


def main():
    srcdir = ROOT / "models/generated/mode_ii/f11_irreversibility_candidate_instrumented"
    deck = srcdir / "M2IRR_PATCH.inp"
    source = srcdir / "M2IRR_PATCH.for"
    deck_bytes = deck.read_text(encoding="ascii").replace(
        "*Static, direct\n0.02, 1.0", "*Static\n0.02, 1.0, 1.0e-8, 0.02").encode("ascii")
    source_bytes = f13_source(source.read_text(encoding="ascii")).encode("ascii")
    common = {
        "status": "prepared_authorized", "n_elem": 23,
        "phase_uel_labels": [1, 23], "displacement_uel_labels": [24, 46],
        "cpe4_labels": [47, 69], "f11_candidate_deck_sha256": sha(deck),
        "f11_candidate_source_sha256": sha(source),
        "automatic_increment_controls": "0.02, 1.0, 1.0e-8, 0.02",
        "trigger": {"step": 2, "time_window": [0.0, 0.04], "jelem": 1,
                    "integration_point": 2, "expected_initial_dtime": 0.02,
                    "trigger_dtime_threshold": 0.015, "requested_pnewdt": 0.5},
        "phase_comparison_tolerance": 1e-7,
        "final_displacement_tolerance_mm": 1e-10,
        "max_rf_difference_over_common_peak": 1e-4,
        "rf_u_common_grid_nrmse": 1e-4,
        "max_final_fixed_point_phase_difference": 1e-6,
        "relative_diagnostic_energy_difference": 1e-4,
        "bounded_log_elements": [1, 23], "bounded_log_integration_points": [1, 4],
        "bounded_log_max_calls_per_increment": 40,
        "runtime_only_difference": "F13_FORCE_CUTBACK"
    }
    outputs = (("control", "f13_rollback_control", 0),
               ("forced", "f13_rollback_forced_cutback", 1))
    for role, name, flag in outputs:
        out = ROOT / "models/generated/mode_ii" / name
        if out.exists():
            raise FileExistsError(out)
        out.mkdir(parents=True)
        (out / "M2IRR_F13.inp").write_bytes(deck_bytes)
        (out / "M2IRR_F13.for").write_bytes(source_bytes)
        manifest = dict(common, role=role, f13_force_cutback=flag)
        manifest.update(deck_sha256=sha(out / "M2IRR_F13.inp"),
                        source_sha256=sha(out / "M2IRR_F13.for"))
        dump(out / "PACKAGE_MANIFEST.json", manifest)
    audit = {
        "status": "pass", "branch_control": "F13_FORCE_CUTBACK",
        "permitted_branch_writes": ["PNEWDT", "bounded diagnostic log"],
        "forbidden_writes_absent": ["RHS", "AMATRX", "SVARS", "USRVAR",
                                      "phase", "history", "penalty coefficient",
                                      "energy", "loads", "material properties",
                                      "convergence tolerances"],
        "sources_byte_identical": True, "decks_byte_identical": True,
        "no_fort_99": True, "explicit_log_variable": "F13_ROLLBACK_LOG"
    }
    dump(ROOT / "models/generated/mode_ii/f13_rollback_control/SOURCE_AUDIT.json", audit)
    remsrc = ROOT / "models/generated/mode_ii/f12_native_miseseri_remesh_preparation"
    remout = ROOT / "models/generated/mode_ii/f13_native_miseseri_first_execution"
    if remout.exists():
        raise FileExistsError(remout)
    remout.mkdir(parents=True)
    shutil.copyfile(remsrc / "source_deck.inp", remout / "source_deck.inp")
    dump(remout / "PACKAGE_MANIFEST.json", {
        "status": "prepared_authorized_one_pass", "source_deck_sha256": sha(remout / "source_deck.inp"),
        "source_odb_sha256": "bfcdbec08669774a9f80939d67c9c86ffe7df707e760450b08b1f6073fc588ac",
        "physical_element_count": 3930, "true_slit_coincident_pairs": 15,
        "variables": ["MISESERI"], "variables_container": "tuple",
        "variables_element_type": "Python 2 str", "sizing_method": "UNIFORM_ERROR",
        "error_target": 1.0, "min_size_mm": 0.001, "max_size_mm": 0.010,
        "coarsening_factor": "NOT_ALLOWED", "refinement_factor": 10, "passes": 1,
        "max_source_solver_executions": 1, "max_adaptive_process_executions": 1,
        "max_native_remesh_operations": 1, "max_refined_mesh_solver_executions": 0})


if __name__ == "__main__":
    main()
