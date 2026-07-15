# UEXTERNALDB Callback Investigation

Date: 2026-07-15

Job ID: 1374532.mmaster02

Repository revision:

```text
b2db162ff7a4a8cf034c20884323f3f674999e61
```

Original work path:

```text
/scratch/pr21vyci/adaptive-remeshing/runs/abaqus_user_subroutine_smoke_1374532.mmaster02
```

Original Abaqus scratch path:

```text
/scratch/pr21vyci/adaptive-remeshing/runs/abaqus_user_subroutine_smoke_1374532.mmaster02/abaqus_scratch
```

Original stage path:

```text
/scratch/pr21vyci/adaptive-remeshing/stage/abaqus_user_subroutine_smoke_1374532.mmaster02
```

Repository evidence path:

```text
runs/hpc/20260715_abaqus_user_subroutine_smoke
```

Investigation evidence path:

```text
runs/hpc/20260715_abaqus_user_subroutine_smoke_callback_investigation
```

## Scope

This was a no-submit, no-Abaqus-launch evidence review. The diagnostic script inspected existing retained files and scratch/stage directories only. It did not edit, move, remove, or regenerate solver outputs.

## Diagnostic Script

Script:

```text
scripts/hpc/inspect_uexternaldb_smoke_1374532.sh
```

The script was copied to the HPC checkout and run from:

```text
/home/pr21vyci/projects/adaptive-remeshing
```

Generated diagnostic files:

```text
commands_used.txt
diagnostic_summary.txt
file_inventory.tsv
marker_search.txt
text_search.txt
text_output_hits.txt
binary_inspection.txt
scratch_references_from_text.txt
```

## Commands Used

The investigation used read-only commands equivalent to:

```bash
find <root> -type f -printf '%p\t%s\t%TY-%Tm-%Td %TH:%TM:%TS\n'

find <root> -type f \
  \( -name 'uexternaldb_smoke.called' \
     -o -iname '*uexternaldb*' \
     -o -iname '*.so' \
     -o -iname '*.o' \
     -o -iname '*.obj' \)

grep -RInE \
  'UEXTERNALDB_SMOKE_CALLED|UEXTERNALDB|uexternaldb_smoke' \
  <root>

grep -RInEi \
  'UEXTERNALDB|compile|link|ifx|ifort|fortran|license|checked out|library|load|callback|warning|error|completed successfully|COMPLETED|ANALYSIS COMPLETE' \
  <selected text outputs>

grep -RInE \
  '/scratch/[^[:space:]]+|tmpdir|scratch|standardU|libstandard|\.so|\.o' \
  <selected text outputs>
```

It was also prepared to run `file`, `nm -a`, `readelf -Ws`, and `strings` on retained `.so`, `.o`, or `.obj` files, but no such retained files were found in the inspected roots.

## Files Inspected

The evidence review inspected the accessible job work directory, Abaqus scratch directory, stage directory, repository root, PBS submission directory, and repository evidence directory.

Key retained text files inspected include:

```text
abq_usrsub_smoke.o1374532
abaqus_user_subroutine_smoke.com
abaqus_user_subroutine_smoke.dat
abaqus_user_subroutine_smoke.inp
abaqus_user_subroutine_smoke.msg
abaqus_user_subroutine_smoke.pbs
abaqus_user_subroutine_smoke.sta
compile_link_license_completion_grep.txt
pbs_completed_job.txt
pbs_output_compile_link_license_grep.txt
RUN_SUMMARY.md
scratch_listing.txt
uexternaldb_smoke.for
```

The generated `file_inventory.tsv` lists all inspected files with paths, sizes, and modification times.

## Marker Search Result

Marker filename searched:

```text
uexternaldb_smoke.called
```

Marker text searched:

```text
UEXTERNALDB_SMOKE_CALLED
```

Results:

```text
run directory: not found
Abaqus scratch directory: not found
stage directory: not found
repository evidence directory: not found
PBS submission/repository root: not found as a marker file
elsewhere accessible: not found as a marker file
```

The marker text appears only in source or diagnostic files, not as evidence of a produced marker file.

## Symbol Search Result

No retained `.so`, `.o`, or `.obj` files were found in the inspected roots. Therefore the linked binary could not be checked with `nm`, `readelf`, or `strings`.

Status:

```text
callback symbol presence in linked library: to be checked
marker strings embedded in linked library: to be checked
```

The source file contains:

```text
SUBROUTINE UEXTERNALDB(...)
OPEN(... FILE='uexternaldb_smoke.called' ...)
WRITE(...) 'UEXTERNALDB_SMOKE_CALLED'
```

That confirms the submitted source intent, but it does not prove linked-symbol presence in the generated user library.

## Abaqus Library-Loading Evidence

Retained evidence confirms that Abaqus accepted `user='uexternaldb_smoke.for'`, compiled the user subroutine, and linked the user subroutine. The retained text does not include the exact generated shared-library path and does not contain an explicit Abaqus line proving user-library loading.

Status:

```text
callback library loading: to be checked
```

## Callback-Entry Evidence

No direct callback-entry token appears in `.msg`, `.dat`, `.sta`, `.com`, PBS output, or the retained evidence files. The expected marker file was not found in the work directory, Abaqus scratch directory, stage directory, repository evidence directory, or submission root.

Status:

```text
callback entry: unverified
marker write location: unknown
```

Do not infer callback entry merely from successful compilation and linking.

## Analysis-Completion Evidence

The retained evidence confirms:

```text
compiler environment: passed
Abaqus linking: passed
Abaqus analysis: passed
```

The `.sta` file contains:

```text
THE ANALYSIS HAS COMPLETED SUCCESSFULLY
```

The `.msg` file reports zero warning messages during user input processing, zero warning messages during analysis, and zero error messages.

## Finding

Supported finding:

```text
E. insufficient_retained_evidence
```

Rationale:

- The marker file was not found anywhere accessible.
- The retained evidence does not include generated `.so`, `.o`, or `.obj` files.
- The linked `UEXTERNALDB` symbol and marker strings cannot be inspected after the fact.
- The retained text proves compile/link/license/solver completion, but does not directly prove user-library loading or callback entry.

Unsupported findings for this evidence set:

- `marker_found_outside_expected_directory`: not supported; no marker file was found.
- `callback_symbol_present_but_invocation_unverified`: not supported; no linked library or object was retained for symbol inspection.
- `callback_invocation_confirmed_marker_write_failed`: not supported; callback entry was not directly demonstrated.
- `callback_not_linked_or_not_loaded`: not supported; linking passed, and the evidence is insufficient to disprove loading.

## Current Classification

```text
hpc_uexternaldb_callback_unverified
hpc_user_subroutine_smoke_fail
```

Failure category:

```text
callback_invocation
```

Component status:

```text
compiler environment: passed
Abaqus linking: passed
Abaqus analysis: passed
callback symbol presence: to be checked
callback library loading: to be checked
callback entry: unverified
marker write location: unknown
```

## Recommended Repair To Evaluate Before Any Retry

Do not modify the Fortran source or PBS script until this evidence review is accepted.

For a future one-CPU retry, the evidence path should be strengthened so callback entry is directly observable. Candidate changes to evaluate:

1. Add a unique callback token written to an Abaqus-managed text stream, such as the message or data output stream, if supported safely from `UEXTERNALDB`.
2. Write the marker using an explicit absolute path supplied by the PBS script, rather than relying on the process working directory.
3. Preserve generated compile/link artifacts or at least copy retained user-library/object files when Abaqus leaves them accessible, so `nm`, `readelf`, and `strings` can verify the linked symbol and embedded marker strings.
4. Capture exact compiler and linker command lines or generated command files when Abaqus exposes them.

## Rerun Requirement

A further one-CPU retry is necessary only if the project needs direct proof of `UEXTERNALDB` callback entry on HPC. That retry should be prepared after review of this evidence and should remain limited to the trivial Abaqus/Standard smoke model. It must not run Molnar, MISESERI, remeshing, state transfer, a parameter study, or multi-CPU execution.
