#!/usr/bin/env python3
"""Build F11 from the frozen F10 pair, changing diagnostic infrastructure only."""
import argparse
import hashlib
import json
from pathlib import Path


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def instrument(text, candidate):
    text = text.replace("F10 BOUNDS", "F11 BOUNDS")
    text = text.replace("NSTVTO=2,NSTVTT=14,NSTV=18",
                        "NSTVTO=2,NSTVTT=14,NSTV=28")
    text = text.replace("N_ELEM=23,NSTV=18)", "N_ELEM=23,NSTV=28)")
    text = text.replace("       REAL*8 PHASEOLD,PENALTY,GAP",
                        "       REAL*8 PHASEOLD,PENALTY,GAP,PENEDEN,PENRES,PENTAN")
    marker = "        GAP=PHASE-PHASEOLD\n"
    diagnostics = (
        marker
        + "        PENEDEN=ZERO\n"
        + "        PENRES=ZERO\n"
        + "        PENTAN=ZERO\n"
        + "        USRVAR(JELEM,19,INPT)=PHASE\n"
        + "        USRVAR(JELEM,20,INPT)=PHASEOLD\n"
        + "        USRVAR(JELEM,21,INPT)=GAP\n"
        + "        USRVAR(JELEM,22,INPT)=ZERO\n"
    )
    tail = (
        "        USRVAR(JELEM,23,INPT)=PENEDEN\n"
        "        USRVAR(JELEM,24,INPT)=PENRES\n"
        "        USRVAR(JELEM,25,INPT)=PENTAN\n"
        "        USRVAR(JELEM,26,INPT)=HALF*GCPAR/CLPAR*PHASE*PHASE\n"
        "        USRVAR(JELEM,27,INPT)=HALF*GCPAR*CLPAR*\n"
        "     1   (DP(1)*DP(1)+DP(2)*DP(2))\n"
        "        USRVAR(JELEM,28,INPT)=HIST*(ONE-PHASE)*(ONE-PHASE)\n"
        "        IF (JELEM.EQ.1.AND.INPT.EQ.1.AND.STEPITER.LE.20) THEN\n"
        "         WRITE(99,*) KSTEP,KINC,TIME(1),TIME(2),DTIME,STEPITER,\n"
        "     1    PHASEOLD,PHASE-DPHASE,PHASE,GAP\n"
        "        ENDIF\n"
    )
    if marker in text:
        text = text.replace(marker, diagnostics, 1)
    else:
        zero_block = (
            "        PENALTY=1.0D6*GCPAR/CLPAR\n"
            "        GAP=PHASE-PHASEOLD\n"
            "        PENEDEN=ZERO\n"
            "        PENRES=ZERO\n"
            "        PENTAN=ZERO\n"
            "        USRVAR(JELEM,19,INPT)=PHASE\n"
            "        USRVAR(JELEM,20,INPT)=PHASEOLD\n"
            "        USRVAR(JELEM,21,INPT)=GAP\n"
            "        USRVAR(JELEM,22,INPT)=ZERO\n"
        )
        upload = (
            "C\nC     ==================================================================\n"
            "C     Uploading solution dep. variables"
        )
        text = text.replace(upload, zero_block + tail + upload, 1)
    if candidate:
        text = text.replace(
            "        IF (GAP.LT.ZERO) THEN\n",
            "        IF (GAP.LT.ZERO) THEN\n"
            "         PENEDEN=HALF*PENALTY*GAP*GAP\n"
            "         PENRES=PENALTY*(-GAP)\n"
            "         PENTAN=PENALTY\n"
            "         USRVAR(JELEM,22,INPT)=ONE\n",
            1,
        )
    if candidate:
        text = text.replace(
            "        ENDIF\nC\nC     ==================================================================\n"
            "C     Uploading solution dep. variables",
            "        ENDIF\n" + tail +
            "C\nC     ==================================================================\n"
            "C     Uploading solution dep. variables",
            1,
        )
    return text


def deck(text):
    text = text.replace("Stage F10", "Stage F11")
    text = text.replace("*Depvar\n16", "*Depvar\n28")
    text = text.replace("*Energy Output\nALLIE, ALLSE, ALLWK\n", "")
    return text


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--f10-baseline", type=Path, required=True)
    p.add_argument("--f10-candidate", type=Path, required=True)
    p.add_argument("--baseline-dir", type=Path, required=True)
    p.add_argument("--candidate-dir", type=Path, required=True)
    a = p.parse_args()
    bdeck = a.f10_baseline / "M2IRR_PATCH.inp"
    cdeck = a.f10_candidate / "M2IRR_PATCH.inp"
    if bdeck.read_bytes() != cdeck.read_bytes():
        raise ValueError("F10 decks are not byte-identical")
    frozen = {
        "f10_baseline_deck_sha256": sha(bdeck),
        "f10_baseline_source_sha256": sha(a.f10_baseline / "M2IRR_PATCH.for"),
        "f10_candidate_deck_sha256": sha(cdeck),
        "f10_candidate_source_sha256": sha(a.f10_candidate / "M2IRR_PATCH.for"),
    }
    common_deck = deck(bdeck.read_text(encoding="ascii"))
    for srcdir, outdir, role in (
        (a.f10_baseline, a.baseline_dir, "baseline"),
        (a.f10_candidate, a.candidate_dir, "candidate"),
    ):
        outdir.mkdir(parents=True, exist_ok=False)
        source = instrument((srcdir / "M2IRR_PATCH.for").read_text(encoding="ascii"),
                            role == "candidate")
        (outdir / "M2IRR_PATCH.inp").write_text(common_deck, encoding="ascii", newline="\n")
        (outdir / "M2IRR_PATCH.for").write_text(source, encoding="ascii", newline="\n")
        manifest = dict(frozen)
        manifest.update({
            "role": role,
            "deck_sha256": sha(outdir / "M2IRR_PATCH.inp"),
            "source_sha256": sha(outdir / "M2IRR_PATCH.for"),
            "n_elem": 23,
            "phase_labels": [1, 23],
            "displacement_labels": [24, 46],
            "visualization_labels": [47, 69],
            "diagnostic_sdv_map": {
                "SDV19": "current_phase", "SDV20": "prior_converged_phase",
                "SDV21": "phase_gap", "SDV22": "penalty_active",
                "SDV23": "penalty_energy_density",
                "SDV24": "penalty_residual_density_magnitude",
                "SDV25": "penalty_tangent_density_magnitude",
                "SDV26": "local_crack_energy_density",
                "SDV27": "gradient_crack_energy_density",
                "SDV28": "history_driven_phase_density",
            },
        })
        (outdir / "PACKAGE_MANIFEST.json").write_text(
            json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
