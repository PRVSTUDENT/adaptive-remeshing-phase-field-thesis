# Session report: Stage F8 qualification preflight

Starting SHA: `359f45cc3c70bf8ff5d0944f994b2df7ea4c7a12`
Preparation/preflight SHA: `6a313e8b262b894dae275f76a916eacc655d45dd`

The exact frozen source was audited and M-106 was repaired offline. SDV15 is
the transferred nodal phase and SDV16 is the maximum-energy history. The
source has no explicit phase obstacle. A consistent quadrature-point penalty
candidate was prepared with matched residual and tangent contributions.

On the cluster login qualification lane, both the frozen and candidate
sources compiled and linked with ifort 2021.13.0 under Abaqus 2023. Input
processing passed. Both then terminated in datacheck with signal 11 during
initial-stress/constraint processing. The candidate eligibility gate
therefore remained false.

The CAE type-matrix script passed Abaqus Python 2.7 compilation and the
frozen MISESERI ODB/deck hashes matched. It was not submitted because all
three preflights had to pass before the first qsub.

Requested submissions: 3. Actual submissions and qsub attempts: 0. Retries,
replacements, direct qsub, qdel and qmove: 0. No run ID, authorization
activation, submission SHA or PBS job ID exists. No solver analysis, native
adaptive analysis or candidate deck generation occurred.

Targeted Stage F8 tests, Python compilation, Bash syntax checks, JSON parsing
and `git diff --check` passed. The thesis master was compiled during closeout.
All unrelated working-tree changes were preserved.
