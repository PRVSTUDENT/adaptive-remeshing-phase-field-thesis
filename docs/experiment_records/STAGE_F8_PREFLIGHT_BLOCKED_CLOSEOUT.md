# Stage F8 qualification preflight closeout

The explicitly authorized three-job batch was not submitted. All three
preflights had to complete before the first qsub. The paired minimal patch
sources both compiled and linked with ifort 2021.13.0 under Abaqus 2023, and
input processing completed, but Abaqus/Standard datacheck terminated by
signal 11 in the initial-stress/constraint phase for both the frozen and
candidate sources.

This common deck/runtime failure precedes any baseline or candidate result
and does not classify the mathematical candidate as accepted or rejected.
`M2IRRCAN1` remained ineligible because its datacheck gate was false.

The CAE type-matrix script passed Abaqus Python 2.7 compilation, and the
required source ODB/deck hashes matched. Nevertheless, `M2RMTYPE1` was not
submitted because the shared all-preflights-before-first-qsub rule had
already failed.

Counts: qsub attempts 0, successful submissions 0, retries 0, replacements 0,
direct qsub 0, qdel 0, qmove 0. No solver analysis, native adaptive analysis,
or candidate deck generation occurred.

