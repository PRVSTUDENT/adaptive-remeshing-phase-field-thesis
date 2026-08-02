#!/bin/bash
set -eu
root=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
tmp=/tmp/f18_codex_fortran_smoke
case "$tmp" in /tmp/f18_codex_fortran_smoke) ;; *) exit 90;; esac
rm -rf "$tmp"
mkdir "$tmp"
trap 'rm -rf /tmp/f18_codex_fortran_smoke' EXIT
cp "$root/models/generated/mode_ii/f18_penalty_active_rollback_control/runtime/M2IRR_F18.for" "$tmp/"
printf '%s\n' '      IMPLICIT REAL*8 (A-H,O-Z)' > "$tmp/ABA_PARAM.INC"
cd "$tmp"
gfortran -std=legacy -ffixed-line-length-none -fallow-argument-mismatch -c M2IRR_F18.for -o M2IRR_F18.o
ld -r M2IRR_F18.o -o M2IRR_F18.rel.o
test -s M2IRR_F18.rel.o
