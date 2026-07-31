#!/usr/bin/env python3
"""Build the F12 rollback pair and preparation-only H1 pair."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write(path, data):
    path.parent.mkdir(parents=True, exist_ok=False)
    path.write_text(data, encoding="ascii", newline="\n")


def write_json(path, data):
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def automatic_deck(text, controls):
    text = text.replace("*Static, direct\n0.02, 1.0", "*Static\n%s" % controls)
    if text.count("*Static\n%s" % controls) != 2:
        raise ValueError("expected two direct static controls")
    return text


def rollback_source(text):
    old = ("        IF (JELEM.EQ.1.AND.INPT.EQ.1.AND.STEPITER.LE.20) THEN\n"
           "         WRITE(99,*) KSTEP,KINC,TIME(1),TIME(2),DTIME,STEPITER,\n"
           "     1    PHASEOLD,PHASE-DPHASE,PHASE,GAP\n"
           "        ENDIF")
    new = ("        IF (JELEM.LE.2.AND.INPT.LE.2.AND.STEPITER.LE.40) THEN\n"
           "         WRITE(99,*) KSTEP,KINC,TIME(1),TIME(2),DTIME,STEPITER,\n"
           "     1    JELEM,INPT,LFLAGS(1),LFLAGS(3),LFLAGS(4),\n"
           "     2    PHASE-DPHASE,SVARS(NSTVTO*(INPT-1)+1),PHASEOLD,\n"
           "     3    PHASE,GAP,USRVAR(JELEM,16,INPT),PENEDEN,PENRES,\n"
           "     4    PENTAN,PNEWDT\n"
           "        ENDIF")
    if old not in text:
        raise ValueError("F11 bounded log anchor missing")
    return text.replace(old, new, 1).replace("F11 BOUNDS", "F12 BOUNDS")


def h1_source(text, candidate):
    text = text.replace("N_ELEM=12064,NSTVTO=2,NSTVTT=14,NSTV=18)",
                        "N_ELEM=12064,NSTVTO=2,NSTVTT=14,NSTV=28)")
    text = text.replace("N_ELEM=12064,NSTV=18)", "N_ELEM=12064,NSTV=28)")
    text = text.replace("COMMON/KUSER/USRVAR(N_ELEM,NSTV,4)",
                        "COMMON/KUSER/USRVAR(N_ELEM,NSTV,4)")
    text = text.replace("       REAL*8 PHASEOLD", "       REAL*8 PHASEOLD,PENALTY,GAP,PENEDEN,PENRES,PENTAN")
    marker = ("        DO I=1,NSTVTO\n"
              "          SDV(I)=SVARS(NSTVTO*(INPT-1)+I)\n"
              "        END DO\n")
    init = (marker + "        PHASEOLD=SDV(1)\n"
            "        PENALTY=1.0D6*GCPAR/CLPAR\n"
            "        GAP=PHASE-PHASEOLD\n        PENEDEN=ZERO\n"
            "        PENRES=ZERO\n        PENTAN=ZERO\n")
    if marker not in text:
        raise ValueError("H1 phase anchor missing")
    text = text.replace(marker, init, 1)
    upload = "C     Uploading solution dep. variables"
    diag = ("        USRVAR(JELEM,19,INPT)=PHASE\n"
            "        USRVAR(JELEM,20,INPT)=PHASEOLD\n"
            "        USRVAR(JELEM,21,INPT)=GAP\n"
            "        USRVAR(JELEM,22,INPT)=ZERO\n"
            "        USRVAR(JELEM,23,INPT)=PENEDEN\n"
            "        USRVAR(JELEM,24,INPT)=PENRES\n"
            "        USRVAR(JELEM,25,INPT)=PENTAN\n"
            "        USRVAR(JELEM,26,INPT)=HALF*GCPAR/CLPAR*PHASE*PHASE\n"
            "        USRVAR(JELEM,27,INPT)=HALF*GCPAR*CLPAR*\n"
            "     1   (DP(1)*DP(1)+DP(2)*DP(2))\n"
            "        USRVAR(JELEM,28,INPT)=HIST*(ONE-PHASE)*(ONE-PHASE)\nC\n")
    text = text.replace(upload, diag + upload, 1)
    if candidate:
        branch = ("        IF (GAP.LT.ZERO) THEN\n"
                  "         PENEDEN=HALF*PENALTY*GAP*GAP\n"
                  "         PENRES=PENALTY*(-GAP)\n"
                  "         PENTAN=PENALTY\n"
                  "         USRVAR(JELEM,22,INPT)=ONE\n"
                  "         DO I=1,NDOFEL\n"
                  "          DO J=1,NDOFEL\n"
                  "           AMATRX(I,J)=AMATRX(I,J)+AN(I)*AN(J)*\n"
                  "     1      AINTW(INPT)*DTM*THCK*PENALTY\n"
                  "          END DO\n"
                  "          RHS(I,1)=RHS(I,1)-AN(I)*AINTW(INPT)*DTM*THCK*\n"
                  "     1      PENALTY*GAP\n"
                  "         END DO\n"
                  "        ENDIF\n")
        text = text.replace(diag, branch + diag, 1)
    guards = (("       IF (JTYPE.EQ.ONE) THEN\n",
               "       IF (JTYPE.EQ.ONE) THEN\n       IF (JELEM.LT.1.OR.JELEM.GT.N_ELEM) THEN\n        WRITE(7,*) 'F12 H1 BOUNDS PHASE',JELEM,N_ELEM\n        CALL XIT\n       ENDIF\n"),
              ("      STEPITER=USRVAR(JELEM-N_ELEM,18,1)\n",
               "      NELEMAN=JELEM-N_ELEM\n      IF (NELEMAN.LT.1.OR.NELEMAN.GT.N_ELEM) THEN\n       WRITE(7,*) 'F12 H1 BOUNDS DISP',JELEM,NELEMAN,N_ELEM\n       CALL XIT\n      ENDIF\n      STEPITER=USRVAR(NELEMAN,18,1)\n"),
              ("       NELEMAN=NOEL-TWO*N_ELEM\n",
               "       NELEMAN=NOEL-TWO*N_ELEM\n       IF (NELEMAN.LT.1.OR.NELEMAN.GT.N_ELEM) THEN\n        WRITE(7,*) 'F12 H1 BOUNDS UMAT',NOEL,NELEMAN,N_ELEM\n        CALL XIT\n       ENDIF\n"))
    for old, new in guards:
        if old not in text:
            raise ValueError("H1 guard anchor missing")
        text = text.replace(old, new, 1)
    return text


def main():
    f11 = ROOT / "models/generated/mode_ii/f11_irreversibility_candidate_instrumented"
    f11_deck = f11 / "M2IRR_PATCH.inp"
    f11_src = f11 / "M2IRR_PATCH.for"
    controls = {"reference": "0.005, 1.0, 1.0e-8, 0.02",
                "cutback": "1.0, 1.0, 1.0e-8, 1.0"}
    for role, dirname in (("reference", "f12_irreversibility_rollback_reference"),
                          ("cutback", "f12_irreversibility_rollback_cutback")):
        out = ROOT / "models/generated/mode_ii" / dirname
        if out.exists():
            continue
        out.mkdir(parents=True, exist_ok=False)
        deck = automatic_deck(f11_deck.read_text(encoding="ascii"), controls[role])
        source = rollback_source(f11_src.read_text(encoding="ascii"))
        (out / "M2IRR_ROLL.inp").write_text(deck, encoding="ascii", newline="\n")
        (out / "M2IRR_ROLL.for").write_text(source, encoding="ascii", newline="\n")
        write_json(out / "PACKAGE_MANIFEST.json", {
            "status": "prepared_authorized", "role": role, "n_elem": 23,
            "f11_candidate_deck_sha256": sha(f11_deck),
            "f11_candidate_source_sha256": sha(f11_src),
            "deck_sha256": sha(out / "M2IRR_ROLL.inp"),
            "source_sha256": sha(out / "M2IRR_ROLL.for"),
            "automatic_increment_controls": controls[role],
            "bounded_log_elements": [1, 2], "bounded_log_integration_points": [1, 2],
            "bounded_log_max_calls_per_increment": 40})
    diff = ROOT / "models/generated/mode_ii/f12_irreversibility_rollback_reference/INCREMENT_CONTROL_DIFF.json"
    if not diff.exists():
        write_json(diff, {"only_permitted_difference": "automatic_time_incrementation",
                          "reference": controls["reference"], "cutback": controls["cutback"],
                          "same_total_step_time": True, "same_final_endpoint": True})

    h1 = ROOT / "models/generated/mode_ii/h1_endpoint_sweep/u020"
    for role, dirname in (("baseline", "f12_h1_instrumented_baseline_prepared"),
                          ("candidate", "f12_h1_instrumented_candidate_prepared")):
        out = ROOT / "models/generated/mode_ii" / dirname
        out.mkdir(parents=True, exist_ok=True)
        deck = (h1 / "m2h1_u020.inp").read_text(encoding="ascii").replace("*Depvar\n16", "*Depvar\n28")
        source = h1_source((h1 / "m2h1_u020.for").read_text(encoding="ascii"), role == "candidate")
        (out / "m2h1_u020.inp").write_text(deck, encoding="ascii", newline="\n")
        (out / "m2h1_u020.for").write_text(source, encoding="ascii", newline="\n")
        write_json(out / "PACKAGE_MANIFEST.json", {
            "status": "prepared_not_authorized", "role": role, "n_elem": 12064,
            "canonical_h1_deck_sha256": sha(h1 / "m2h1_u020.inp"),
            "canonical_h1_source_sha256": sha(h1 / "m2h1_u020.for"),
            "deck_sha256": sha(out / "m2h1_u020.inp"),
            "source_sha256": sha(out / "m2h1_u020.for"),
            "physical_element_count": 12064, "submission_authorized": False,
            "bounds_guards": True, "target_u1_mm": 0.020})

    remesh_src = ROOT / "models/generated/mode_ii/miseseri_preanalysis_corrected_pbs/ModeII_MISESERI_preanalysis.inp"
    remesh = ROOT / "models/generated/mode_ii/f12_native_miseseri_remesh_preparation"
    if not remesh.exists():
        remesh.mkdir(parents=True)
        (remesh / "source_deck.inp").write_bytes(remesh_src.read_bytes())
        write_json(remesh / "PACKAGE_MANIFEST.json", {
            "status": "prepared_authorized_cae_only", "source_job": "1379893.mmaster02",
            "source_deck_sha256": sha(remesh / "source_deck.inp"),
            "source_odb_sha256": "bfcdbec08669774a9f80939d67c9c86ffe7df707e760450b08b1f6073fc588ac",
            "physical_element_count": 3930, "true_slit_coincident_pairs": 15,
            "variables": ["MISESERI"], "variables_container": "tuple",
            "variables_element_type": "Python 2 str", "min_size_mm": 0.001,
            "max_size_mm": 0.010, "refinement_factor": 10,
            "coarsening_factor": "NOT_ALLOWED", "error_target": 1.0,
            "sizing_method": "UNIFORM_ERROR", "passes": 1,
            "solver_execution_authorized": False, "adaptive_execution_authorized": False,
            "remesh_execution_authorized": False})

    frozen = ROOT / "runs/hpc/stage_f/f12_rollback_qualification_and_native_remesh_preparation/FROZEN_HASHES.json"
    frozen.parent.mkdir(parents=True, exist_ok=True)
    write_json(frozen, {
        "f11_candidate_deck_sha256": sha(f11_deck),
        "f11_candidate_source_sha256": sha(f11_src),
        "f11_model_generator_sha256": sha(ROOT / "scripts/model_generation/build_stage_f11_instrumented_pair.py"),
        "f11_extractor_sha256": sha(ROOT / "scripts/postprocessing/extract_stage_f11_instrumented_pair.py"),
        "f12_analyzer_sha256": sha(ROOT / "scripts/validation/analyze_stage_f12_rollback.py"),
        "f11_energy_contract_sha256": sha(ROOT / "docs/decisions/STAGE_F11_ENERGY_DEFINITION_AND_ACCEPTANCE.md"),
        "f11_diagnostic_variable_map": json.loads((f11 / "PACKAGE_MANIFEST.json").read_text())["diagnostic_sdv_map"],
        "canonical_h1_deck_sha256": sha(h1 / "m2h1_u020.inp"),
        "canonical_h1_source_sha256": sha(h1 / "m2h1_u020.for"),
        "official_miseseri_deck_sha256": sha(remesh_src)})


if __name__ == "__main__":
    main()
