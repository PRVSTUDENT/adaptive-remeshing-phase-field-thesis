#!/usr/bin/env python3
import hashlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / "models/generated/mode_ii/verification_batch"

def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()

j1_inp = sha256_file(BASE / "M2REF_ONEEL_FRACFIX_VERIFY_R2/M2REF_ONEEL_FRACFIX_VERIFY_R2.inp")
j1_uel = sha256_file(BASE / "M2REF_ONEEL_FRACFIX_VERIFY_R2/f42_mixed_uel.for")
j1_pbs = sha256_file(BASE / "M2REF_ONEEL_FRACFIX_VERIFY_R2/M2REF_ONEEL_FRACFIX_VERIFY_R2.pbs")
j1_sh  = sha256_file(BASE / "M2REF_ONEEL_FRACFIX_VERIFY_R2/submit_m2ref_oneel_fracfix_verify_r2.sh")

j2_inp = sha256_file(BASE / "M2REF_H0_EXACT_FRACFIX_REPRO/M2REF_H0_EXACT_FRACFIX_REPRO.inp")
j2_uel = sha256_file(BASE / "M2REF_H0_EXACT_FRACFIX_REPRO/f42_mixed_uel.for")
j2_pbs = sha256_file(BASE / "M2REF_H0_EXACT_FRACFIX_REPRO/M2REF_H0_EXACT_FRACFIX_REPRO.pbs")
j2_sh  = sha256_file(BASE / "M2REF_H0_EXACT_FRACFIX_REPRO/submit_m2ref_h0_exact_fracfix_repro.sh")

print("J1_INP:", j1_inp)
print("J1_UEL:", j1_uel)
print("J1_PBS:", j1_pbs)
print("J1_SH: ", j1_sh)
print("---")
print("J2_INP:", j2_inp)
print("J2_UEL:", j2_uel)
print("J2_PBS:", j2_pbs)
print("J2_SH: ", j2_sh)
