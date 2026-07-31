#!/usr/bin/env python3
"""Build the compact Stage F10 baseline/candidate qualification pair."""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
F8_BUILDER = ROOT / "scripts/model_generation/build_stage_f8_minimal_patch.py"
FROZEN_SHA = "49c9054ab5faec9e069e0a9149af5058e6f1e11ab164c2a0e318f60282309b37"


def load_f8():
    spec = importlib.util.spec_from_file_location("f8_builder", F8_BUILDER)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def compact_deck(text):
    text = text.replace("Stage F8", "Stage F10")
    for old, new in zip(range(33853, 33876), range(24, 47)):
        text = text.replace(str(old), str(new))
    for old, new in zip(range(67705, 67728), range(47, 70)):
        text = text.replace(str(old), str(new))
    return text


def adapt_source(text):
    text = text.replace("N_ELEM=33852", "N_ELEM=23")
    text = text.replace(
        "       IF (JTYPE.EQ.ONE) THEN",
        "       IF (JTYPE.EQ.ONE) THEN\n"
        "       IF (JELEM.LT.1.OR.JELEM.GT.N_ELEM) THEN\n"
        "        WRITE(7,*) 'F10 BOUNDS PHASE',JELEM,N_ELEM\n"
        "        CALL XIT\n"
        "       ENDIF",
        1,
    )
    text = text.replace(
        "      ELSEIF (JTYPE.EQ.TWO) THEN\n"
        "      STEPITER=USRVAR(JELEM-N_ELEM,18,1)",
        "      ELSEIF (JTYPE.EQ.TWO) THEN\n"
        "      NELEMAN=JELEM-N_ELEM\n"
        "      IF (NELEMAN.LT.1.OR.NELEMAN.GT.N_ELEM) THEN\n"
        "       WRITE(7,*) 'F10 BOUNDS DISP',JELEM,N_ELEM,NELEMAN\n"
        "       CALL XIT\n"
        "      ENDIF\n"
        "      STEPITER=USRVAR(NELEMAN,18,1)",
        1,
    )
    text = text.replace("USRVAR(JELEM-N_ELEM,", "USRVAR(NELEMAN,")
    text = text.replace(
        "       NELEMAN=NOEL-TWO*N_ELEM",
        "       NELEMAN=NOEL-TWO*N_ELEM\n"
        "       IF (NELEMAN.LT.1.OR.NELEMAN.GT.N_ELEM) THEN\n"
        "        WRITE(7,*) 'F10 BOUNDS UMAT',NOEL,N_ELEM,NELEMAN,NPT\n"
        "        CALL XIT\n"
        "       ENDIF\n"
        "       IF (NPT.LT.1.OR.NPT.GT.4) THEN\n"
        "        WRITE(7,*) 'F10 BOUNDS NPT',NOEL,NPT\n"
        "        CALL XIT\n"
        "       ENDIF",
        1,
    )
    return text


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--frozen-source", type=Path, required=True)
    parser.add_argument("--baseline-dir", type=Path, required=True)
    parser.add_argument("--candidate-dir", type=Path, required=True)
    args = parser.parse_args()
    frozen = args.frozen_source.read_text(encoding="ascii")
    if hashlib.sha256(frozen.encode("ascii")).hexdigest() != FROZEN_SHA:
        raise ValueError("frozen source mismatch")
    f8 = load_f8()
    baseline = adapt_source(frozen)
    candidate = adapt_source(f8.candidate_source(frozen))
    deck = compact_deck(f8.deck())
    for directory, source, role in (
        (args.baseline_dir, baseline, "baseline"),
        (args.candidate_dir, candidate, "candidate"),
    ):
        directory.mkdir(parents=True, exist_ok=True)
        (directory / "M2IRR_PATCH.inp").write_text(deck, encoding="ascii", newline="\n")
        (directory / "M2IRR_PATCH.for").write_text(source, encoding="ascii", newline="\n")
        manifest = {
            "role": role,
            "deck_sha256": sha(directory / "M2IRR_PATCH.inp"),
            "source_sha256": sha(directory / "M2IRR_PATCH.for"),
            "frozen_source_sha256": FROZEN_SHA,
            "n_elem": 23,
            "phase_labels": [1, 23],
            "displacement_labels": [24, 46],
            "visualization_labels": [47, 69],
            "bounds_guards": True,
            "mapping_adaptation_not_constitutive_change": True,
        }
        (directory / "PACKAGE_MANIFEST.json").write_text(
            json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
