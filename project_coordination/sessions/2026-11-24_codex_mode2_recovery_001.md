# Codex takeover: Mode II offline recovery

User explicitly transferred AGY's interrupted task to Codex. Base commit:
68e75140462c671a36816cb001c89368dbcadbea. AGY process had exited; only the
Abaqus license service was running. Prior lock snapshot and exact dirty-path
inventory preserved in the Windows temporary directory. No apps closed,
files deleted, solver started, HPC query/change or PBS submission performed.

Recovered AGY's in-progress deck builder. Fixed 18-state initial-condition
continuations, removed duplicate zero initialization records, added constant
hold amplitude, and made unfinished execution fail visibly. Existing broad
mesh generator and untracked generated deck were preserved unchanged.

Checks: 12 affected tests passed; frozen UEL exact SHA256 CE8D5EDC... confirmed;
offline constitutive witness establishes mismatch with requested Miehe split.
Detailed evidence: docs/validation/METHOD_C_MODE2_RECOVERY_AUDIT.md.

Guarded review publisher dry-run rejected new campaign goal with
BRIDGE_RESEARCH_SCOPE_CONFLICT. No dispatch or response is claimed.
User was asked for a scientific formulation choice after concrete evidence
was prepared. Master goal remains OPEN; numerical execution is unqualified.
Next action depends on that answer, then implement/review exact loop and
schedule, synchronize canonical bridge scope under supplied campaign dispatch,
and verify one bounded numerical step. L-panel remains subsequent to Mode II
independent review. PBS cumulative 73 preserved; job 1424916 untouched.

User resolved formulation choice: retain frozen UEL and disclose deviation. Runtime implemented with 14 passing tests; canonical bridge scope synchronized from original dispatch, guarded publisher dry-run PASS. Prepared one local coarse cycle and separate datacheck on one CPU under MODE2_LOCAL_QUALIFICATION.json.

## Numerical and recovery closeout

Coarse R0 exposed inherited wrong material-property order and was cleanly
terminated; all evidence retained. Corrected coarse R1 completed on one CPU,
U1=.0095 mm, RF1=.398039 kN, dmax=.350769, 2960 elements, solve 180 seconds.
Cycle1 R0/R1 datachecks exposed DEPVAR30 and mixed boundary OP flags; each
distinct technical correction and failed evidence is preserved. Cycle1 R2
passed datacheck and solved, but hold reaction changed -32.278584 percent,
failing the unchanged 5 percent scientific gate. It was rejected and no
Cycle2 ran. Real images, inputs, checkpoints, summaries and .sta/.dat published.

Offline audit: H integral +.875662 percent; averaged-damage integral +.022348
percent; maxima preserved before hold. Hold damage grew .350769 to .986888.
Cause unproven. Prepared a distinct same-mesh hold-only control without running
it. Latest affected tests: 18 passed. Frozen UEL exact hash unchanged.
Accounting: five datachecks, three local solver starts including the cleanly
stopped invalid-input coarse attempt; zero PBS, cumulative 73 preserved.

Automatic approval review rejected the action to assemble the failure/control
review packet with `blocked by policy`; smaller attempt also rejected. No
candidate definition, ready publication, review response or approval exists.
Draft adapter repair and unexecuted metadata preparer preserved; no signing
keys read/generated and no placeholder provenance used. Master goal OPEN.
No solver running. Resume with safe authenticated review dispatch and apply
the scientific response before any more numerical action. No L-panel work.
