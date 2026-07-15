#!/usr/bin/env bash
set -u

JOB_ID="1374532.mmaster02"
JOB_NUM="${JOB_ID%%.*}"
REPO_ROOT="/home/pr21vyci/projects/adaptive-remeshing"
RUN_DIR="/scratch/pr21vyci/adaptive-remeshing/runs/abaqus_user_subroutine_smoke_${JOB_ID}"
ABAQUS_SCRATCH_DIR="${RUN_DIR}/abaqus_scratch"
STAGE_DIR="/scratch/pr21vyci/adaptive-remeshing/stage/abaqus_user_subroutine_smoke_${JOB_ID}"
PBS_SUBMISSION_DIR="${REPO_ROOT}"
REPO_EVIDENCE_DIR="${REPO_ROOT}/runs/hpc/20260715_abaqus_user_subroutine_smoke"
EVIDENCE_DIR="${REPO_ROOT}/runs/hpc/20260715_abaqus_user_subroutine_smoke_callback_investigation"

mkdir -p "${EVIDENCE_DIR}"

COMMANDS_USED="${EVIDENCE_DIR}/commands_used.txt"
SUMMARY="${EVIDENCE_DIR}/diagnostic_summary.txt"
INVENTORY="${EVIDENCE_DIR}/file_inventory.tsv"
MARKER_SEARCH="${EVIDENCE_DIR}/marker_search.txt"
TEXT_SEARCH="${EVIDENCE_DIR}/text_search.txt"
TEXT_OUTPUT_HITS="${EVIDENCE_DIR}/text_output_hits.txt"
BINARY_INSPECTION="${EVIDENCE_DIR}/binary_inspection.txt"
COM_LOG_REFERENCES="${EVIDENCE_DIR}/scratch_references_from_text.txt"

: > "${COMMANDS_USED}"
: > "${SUMMARY}"
: > "${INVENTORY}"
: > "${MARKER_SEARCH}"
: > "${TEXT_SEARCH}"
: > "${TEXT_OUTPUT_HITS}"
: > "${BINARY_INSPECTION}"
: > "${COM_LOG_REFERENCES}"

record_command() {
  printf '%s\n' "$*" >> "${COMMANDS_USED}"
}

section() {
  printf '\n==== %s ====\n' "$1"
}

require_dir() {
  local label="$1"
  local path="$2"
  if [ -d "${path}" ]; then
    printf 'PASS: %s exists: %s\n' "${label}" "${path}" >> "${SUMMARY}"
    return 0
  fi
  printf 'MISSING: %s: %s\n' "${label}" "${path}" >> "${SUMMARY}"
  return 1
}

safe_find_roots=()
add_root_if_dir() {
  local path="$1"
  if [ -d "${path}" ]; then
    safe_find_roots+=("${path}")
  fi
}

{
  section "Job constants"
  printf 'JOB_ID=%s\n' "${JOB_ID}"
  printf 'RUN_DIR=%s\n' "${RUN_DIR}"
  printf 'ABAQUS_SCRATCH_DIR=%s\n' "${ABAQUS_SCRATCH_DIR}"
  printf 'STAGE_DIR=%s\n' "${STAGE_DIR}"
  printf 'PBS_SUBMISSION_DIR=%s\n' "${PBS_SUBMISSION_DIR}"
  printf 'REPO_EVIDENCE_DIR=%s\n' "${REPO_EVIDENCE_DIR}"
  printf 'EVIDENCE_DIR=%s\n' "${EVIDENCE_DIR}"
  printf 'hostname=%s\n' "$(hostname)"
  printf 'timestamp=%s\n' "$(date -Is)"
} >> "${SUMMARY}"

require_dir "run directory" "${RUN_DIR}" || true
require_dir "Abaqus scratch directory" "${ABAQUS_SCRATCH_DIR}" || true
require_dir "stage directory" "${STAGE_DIR}" || true
require_dir "repository root" "${REPO_ROOT}" || true
require_dir "PBS submission directory" "${PBS_SUBMISSION_DIR}" || true
require_dir "repository evidence directory" "${REPO_EVIDENCE_DIR}" || true

add_root_if_dir "${RUN_DIR}"
add_root_if_dir "${ABAQUS_SCRATCH_DIR}"
add_root_if_dir "${STAGE_DIR}"
add_root_if_dir "${PBS_SUBMISSION_DIR}"
add_root_if_dir "${REPO_EVIDENCE_DIR}"

section "File inventory" >> "${INVENTORY}"
printf 'path\tsize_bytes\tmodified_time\n' >> "${INVENTORY}"
record_command "find <root> -type f -printf '%p\\t%s\\t%TY-%Tm-%Td %TH:%TM:%TS\\n'"
for root in "${safe_find_roots[@]}"; do
  printf '\n# root: %s\n' "${root}" >> "${INVENTORY}"
  find "${root}" -type f -printf '%p\t%s\t%TY-%Tm-%Td %TH:%TM:%TS\n' 2>/dev/null >> "${INVENTORY}"
done

section "Marker filename and candidate binary/object search" >> "${MARKER_SEARCH}"
record_command "find <root> -type f \\( -name 'uexternaldb_smoke.called' -o -iname '*uexternaldb*' -o -iname '*.so' -o -iname '*.o' -o -iname '*.obj' \\)"
for root in "${safe_find_roots[@]}"; do
  printf '\n# root: %s\n' "${root}" >> "${MARKER_SEARCH}"
  find "${root}" -type f \( -name 'uexternaldb_smoke.called' -o -iname '*uexternaldb*' -o -iname '*.so' -o -iname '*.o' -o -iname '*.obj' \) -print 2>/dev/null >> "${MARKER_SEARCH}"
done

section "Marker text and callback text search" >> "${TEXT_SEARCH}"
record_command "grep -RInE 'UEXTERNALDB_SMOKE_CALLED|UEXTERNALDB|uexternaldb_smoke' <root>"
for root in "${safe_find_roots[@]}"; do
  printf '\n# root: %s\n' "${root}" >> "${TEXT_SEARCH}"
  grep -RInE 'UEXTERNALDB_SMOKE_CALLED|UEXTERNALDB|uexternaldb_smoke' "${root}" 2>/dev/null >> "${TEXT_SEARCH}" || true
done

section "Abaqus output keyword scan" >> "${TEXT_OUTPUT_HITS}"
record_command "grep -RInEi 'UEXTERNALDB|compile|link|ifx|ifort|fortran|license|checked out|library|load|callback|warning|error|completed successfully|COMPLETED|ANALYSIS COMPLETE' selected text outputs"
for root in "${RUN_DIR}" "${STAGE_DIR}" "${REPO_EVIDENCE_DIR}" "${PBS_SUBMISSION_DIR}"; do
  [ -d "${root}" ] || continue
  printf '\n# root: %s\n' "${root}" >> "${TEXT_OUTPUT_HITS}"
  find "${root}" -type f \( -name '*.log' -o -name '*.msg' -o -name '*.dat' -o -name '*.sta' -o -name '*.com' -o -name "abq_usrsub_smoke.o${JOB_NUM}" -o -name 'pbs_completed_job.txt' -o -name '*grep*.txt' -o -name 'RUN_SUMMARY.md' \) -print0 2>/dev/null |
    xargs -0 grep -InEi 'UEXTERNALDB|compile|link|ifx|ifort|fortran|license|checked out|library|load|callback|warning|error|completed successfully|COMPLETED|ANALYSIS COMPLETE' 2>/dev/null >> "${TEXT_OUTPUT_HITS}" || true
done

section "Scratch/temp directory references in retained text" >> "${COM_LOG_REFERENCES}"
record_command "grep -RInE '/scratch/[^[:space:]]+|tmpdir|scratch|standardU|libstandard|\\.so|\\.o' selected text outputs"
for root in "${RUN_DIR}" "${STAGE_DIR}" "${REPO_EVIDENCE_DIR}"; do
  [ -d "${root}" ] || continue
  printf '\n# root: %s\n' "${root}" >> "${COM_LOG_REFERENCES}"
  find "${root}" -type f \( -name '*.log' -o -name '*.msg' -o -name '*.dat' -o -name '*.sta' -o -name '*.com' -o -name "abq_usrsub_smoke.o${JOB_NUM}" -o -name 'pbs_completed_job.txt' -o -name '*grep*.txt' -o -name 'RUN_SUMMARY.md' \) -print0 2>/dev/null |
    xargs -0 grep -InE '/scratch/[^[:space:]]+|tmpdir|scratch|standardU|libstandard|\.so|\.o' 2>/dev/null >> "${COM_LOG_REFERENCES}" || true
done

section "Binary/object/shared-library inspection" >> "${BINARY_INSPECTION}"
record_command "file, nm -a, readelf -Ws, strings on retained *.so, *.o, *.obj files"
mapfile -t binary_candidates < <(
  for root in "${safe_find_roots[@]}"; do
    find "${root}" -type f \( -iname '*.so' -o -iname '*.o' -o -iname '*.obj' \) -print 2>/dev/null
  done | sort -u
)

if [ "${#binary_candidates[@]}" -eq 0 ]; then
  printf 'No retained .so, .o, or .obj files found in inspected roots.\n' >> "${BINARY_INSPECTION}"
else
  for candidate in "${binary_candidates[@]}"; do
    section "${candidate}" >> "${BINARY_INSPECTION}"
    printf '$ file %s\n' "${candidate}" >> "${BINARY_INSPECTION}"
    file "${candidate}" >> "${BINARY_INSPECTION}" 2>&1 || true
    if command -v nm >/dev/null 2>&1; then
      printf '$ nm -a %s | grep -i uexternaldb\n' "${candidate}" >> "${BINARY_INSPECTION}"
      nm -a "${candidate}" 2>&1 | grep -i uexternaldb >> "${BINARY_INSPECTION}" || true
    else
      printf 'nm not available\n' >> "${BINARY_INSPECTION}"
    fi
    if command -v readelf >/dev/null 2>&1; then
      printf '$ readelf -Ws %s | grep -i uexternaldb\n' "${candidate}" >> "${BINARY_INSPECTION}"
      readelf -Ws "${candidate}" 2>&1 | grep -i uexternaldb >> "${BINARY_INSPECTION}" || true
    else
      printf 'readelf not available\n' >> "${BINARY_INSPECTION}"
    fi
    if command -v strings >/dev/null 2>&1; then
      printf "$ strings %s | grep -E 'UEXTERNALDB_SMOKE_CALLED|uexternaldb_smoke.called'\n" "${candidate}" >> "${BINARY_INSPECTION}"
      strings "${candidate}" 2>&1 | grep -E 'UEXTERNALDB_SMOKE_CALLED|uexternaldb_smoke.called' >> "${BINARY_INSPECTION}" || true
    else
      printf 'strings not available\n' >> "${BINARY_INSPECTION}"
    fi
  done
fi

{
  section "Marker location classification"
  for location in \
    "run directory:${RUN_DIR}" \
    "Abaqus scratch:${ABAQUS_SCRATCH_DIR}" \
    "stage directory:${STAGE_DIR}" \
    "repository evidence:${REPO_EVIDENCE_DIR}" \
    "PBS submission:${PBS_SUBMISSION_DIR}"
  do
    label="${location%%:*}"
    path="${location#*:}"
    if [ -d "${path}" ] && find "${path}" -type f -name 'uexternaldb_smoke.called' -print -quit 2>/dev/null | grep -q .; then
      printf 'FOUND: %s\n' "${label}"
    else
      printf 'NOT_FOUND: %s\n' "${label}"
    fi
  done
} >> "${SUMMARY}"

{
  section "Evidence outputs"
  printf '%s\n' "${COMMANDS_USED}"
  printf '%s\n' "${SUMMARY}"
  printf '%s\n' "${INVENTORY}"
  printf '%s\n' "${MARKER_SEARCH}"
  printf '%s\n' "${TEXT_SEARCH}"
  printf '%s\n' "${TEXT_OUTPUT_HITS}"
  printf '%s\n' "${BINARY_INSPECTION}"
  printf '%s\n' "${COM_LOG_REFERENCES}"
} >> "${SUMMARY}"

printf 'Diagnostic evidence written to %s\n' "${EVIDENCE_DIR}"
