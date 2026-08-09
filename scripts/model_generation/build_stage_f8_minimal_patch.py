#!/usr/bin/env python3
"""Build paired Stage-F8 minimal patch packages.

The two decks are byte-identical.  Their only scientific difference is the
user-subroutine source selected at execution.
"""

import argparse
import hashlib
import json
from pathlib import Path


FROZEN_SHA = "49c9054ab5faec9e069e0a9149af5058e6f1e11ab164c2a0e318f60282309b37"
N_ELEM_FROZEN = 33852


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def deck() -> str:
    nx, ny = 6, 4
    dx = dy = 0.005
    nodes = []
    for j in range(ny + 1):
        for i in range(nx + 1):
            nodes.append((j * (nx + 1) + i + 1, i * dx, j * dy))
    conn = []
    for j in range(ny):
        for i in range(nx):
            if i == 0 and j == 2:
                continue
            n1 = j * (nx + 1) + i + 1
            conn.append((len(conn) + 1, n1, n1 + 1, n1 + nx + 2, n1 + nx + 1))
    bottom = [n for n, _, y in nodes if y == 0.0]
    top = [n for n, _, y in nodes if y == ny * dy]
    def data_lines(values):
        return [", ".join(map(str, values[i:i + 16])) for i in range(0, len(values), 16)]
    lines = [
        "*Heading",
        "** Stage F8 deterministic 6x4 seeded-notch patch",
        "*Preprint, echo=NO, model=NO, history=NO, contact=NO",
        "*Part, name=PATCH",
        "*Node",
    ]
    lines += ["%d, %.10g, %.10g" % row for row in nodes]
    lines += [
        "*User element, nodes=4, type=U1, properties=3, coordinates=2, VARIABLES=8",
        "3",
        "*Element, type=U1",
    ]
    lines += ["%d, %d, %d, %d, %d" % row for row in conn]
    lines += [
        "*Elset, elset=PHASE",
    ]
    lines += data_lines([row[0] for row in conn])
    lines += [
        "*Uel property, elset=PHASE",
        "0.015, 0.0027, 1.0",
        "*User element, nodes=4, type=U2, properties=4, coordinates=2, VARIABLES=56",
        "1, 2",
        "*Element, type=U2",
    ]
    lines += [
        "%d, %d, %d, %d, %d" % ((N_ELEM_FROZEN + eid,) + row[1:])
        for eid, *rest in conn
        for row in [(eid, *rest)]
    ]
    lines += [
        "*Elset, elset=DISP",
    ]
    lines += data_lines([N_ELEM_FROZEN + row[0] for row in conn])
    lines += [
        "*Uel property, elset=DISP",
        "210.0, 0.3, 1.0, 1.0e-7",
        "*Element, type=CPE4, elset=UMATELEM",
    ]
    lines += [
        "%d, %d, %d, %d, %d" % ((2 * N_ELEM_FROZEN + eid,) + row[1:])
        for eid, *rest in conn
        for row in [(eid, *rest)]
    ]
    lines += [
        "*Solid Section, elset=UMATELEM, material=UMATELEM",
        "1.0",
        "*End Part",
        "*Assembly, name=Assembly",
        "*Instance, name=PATCH-1, part=PATCH",
        "*End Instance",
        "*Nset, nset=BOTTOM, instance=PATCH-1",
        ", ".join(map(str, bottom)),
        "*Nset, nset=TOP, instance=PATCH-1",
        ", ".join(map(str, top)),
        "*Nset, nset=TOPLEFT, instance=PATCH-1",
        str(top[0]),
        "*Nset, nset=ALLNODES, instance=PATCH-1, generate",
        "1, %d, 1" % len(nodes),
        "*Elset, elset=UMATELEM, instance=PATCH-1",
    ]
    lines += data_lines([2 * N_ELEM_FROZEN + row[0] for row in conn])
    lines += [
        "*End Assembly",
        "*Material, name=UMATELEM",
        "*Depvar",
        "16",
        "*User Material, constants=2",
        "1.0e-11, 0.3",
        "*Amplitude, name=CYCLE, time=TOTAL TIME",
        "1.0, 0.003, 1.5, 0.001, 2.0, 0.006",
        "** Step 1: monotonic shear",
        "*Step, name=MONOTONIC, nlgeom=NO, inc=200",
        "*Static, direct",
        "0.02, 1.0",
        "*Boundary",
        "BOTTOM, 1, 2, 0.0",
        "TOPLEFT, 2, 2, 0.0",
        "TOP, 1, 1, 0.003",
        "*Output, field, frequency=1",
        "*Node Output, nset=ALLNODES",
        "U, RF",
        "*Element Output, elset=UMATELEM",
        "SDV",
        "*Energy Output",
        "ALLIE, ALLSE, ALLWK",
        "*End Step",
        "** Step 2: partial unload then reload",
        "*Step, name=UNLOAD_RELOAD, nlgeom=NO, inc=200",
        "*Static, direct",
        "0.02, 1.0",
        "*Boundary, amplitude=CYCLE",
        "TOP, 1, 1, 1.0",
        "*Output, field, frequency=1",
        "*Node Output, nset=ALLNODES",
        "U, RF",
        "*Element Output, elset=UMATELEM",
        "SDV",
        "*Energy Output",
        "ALLIE, ALLSE, ALLWK",
        "*End Step",
    ]
    return "\n".join(lines) + "\n"


def candidate_source(text: str) -> str:
    if hashlib.sha256(text.encode()).hexdigest() != FROZEN_SHA:
        raise ValueError("frozen source SHA mismatch")
    text = text.replace(
        "       REAL*8 DTM,THCK,HIST,CLPAR,GCPAR,EMOD,ENU,PARK,ENG",
        "       REAL*8 DTM,THCK,HIST,CLPAR,GCPAR,EMOD,ENU,PARK,ENG\n"
        "       REAL*8 PHASEOLD,PENALTY,GAP",
        1,
    )
    text = text.replace(
        "        DO I=1,NSTVTO\n          SDV(I)=SVARS(NSTVTO*(INPT-1)+I)\n        END DO",
        "        DO I=1,NSTVTO\n"
        "          SDV(I)=SVARS(NSTVTO*(INPT-1)+I)\n"
        "        END DO\n"
        "        PHASEOLD=SDV(1)",
        1,
    )
    marker = (
        "         RHS(I,1)=RHS(I,1)-AN(I)*AINTW(INPT)*DTM*THCK*\n"
        "     1    ((GCPAR/CLPAR+TWO*HIST)*PHASE-TWO*HIST)\n"
        "        END DO"
    )
    replacement = marker + (
        "\nC     Consistent quadrature-point penalty for d_(n+1) >= d_n.\n"
        "        PENALTY=1.0D6*GCPAR/CLPAR\n"
        "        GAP=PHASE-PHASEOLD\n"
        "        IF (GAP.LT.ZERO) THEN\n"
        "         DO I=1,NNODE\n"
        "          DO K=1,NNODE\n"
        "           AMATRX(I,K)=AMATRX(I,K)+AN(I)*AN(K)*DTM*THCK*\n"
        "     1      AINTW(INPT)*PENALTY\n"
        "          END DO\n"
        "          RHS(I,1)=RHS(I,1)-AN(I)*AINTW(INPT)*DTM*THCK*\n"
        "     1      PENALTY*GAP\n"
        "         END DO\n"
        "        ENDIF"
    )
    if marker not in text:
        raise ValueError("residual insertion marker missing")
    return text.replace(marker, replacement, 1)


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--frozen-source", type=Path, required=True)
    p.add_argument("--baseline-dir", type=Path, required=True)
    p.add_argument("--candidate-dir", type=Path, required=True)
    args = p.parse_args()
    frozen = args.frozen_source.read_text(encoding="ascii")
    cand = candidate_source(frozen)
    common_deck = deck()
    for directory, source in ((args.baseline_dir, frozen), (args.candidate_dir, cand)):
        directory.mkdir(parents=True, exist_ok=True)
        (directory / "M2IRR_PATCH.inp").write_text(common_deck, encoding="ascii", newline="\n")
        (directory / "M2IRR_PATCH.for").write_text(source, encoding="ascii", newline="\n")
        manifest = {
            "deck_sha256": sha(directory / "M2IRR_PATCH.inp"),
            "source_sha256": sha(directory / "M2IRR_PATCH.for"),
            "frozen_source_sha256": FROZEN_SHA,
            "elements_per_layer": 23,
            "scientific_difference": "user source only",
            "full_h2_analysis": False,
        }
        (directory / "PACKAGE_MANIFEST.json").write_text(
            json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
