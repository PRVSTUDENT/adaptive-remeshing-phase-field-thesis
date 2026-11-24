# Mode II takeover and offline recovery audit — 24 November 2026

Goal `METHOD_C_MODE2_LPANEL_V1` remains OPEN. This is preparation evidence,
not a numerical result or scientific acceptance. User explicitly requested
Codex takeover after AGY conversation `d97b09c5-df77-4255-bcb9-1a24ffc2e00d`
failed with model/network errors. No AGY, Python orchestrator or Abaqus solver
process was running at takeover; ABAQUSLM is the license service. The stale
AGY lock was reconciled under that explicit takeover instruction. Existing
dirty paths and failed preparation were preserved; no solver evidence deleted.

## Reconciled scope

User supplied original dispatch `HND-METHOD-C-MODE2-LPANEL-001` and amendment
`HND-METHOD-C-MODE2-LPANEL-002` directly in this session. They instruct local
Mode II first, independent review, then L-panel. No PBS; historical cumulative
count 73 and HPC job 1424916 untouched. Source CE8D5EDC remains frozen.
The new dispatch supersedes older roadmap restrictions but simultaneously
requires a Miehe spectral split and that exact unchanged source.

## Concrete preparation defects and repairs

- AGY's orchestrator ended after `check_mode2_completion`: no main entrypoint,
  execution loop, checkpoint extraction/resume or runtime gates. Its launcher
  could exit successfully without starting anything. Added an honest dry-run
  audit and nonzero execution refusal instead of silent success. The runtime
  remains unfinished; it is not claimed operational.
- Its initial-condition block repeated each element label, supplied only 16
  intended phase state variables, and duplicated mechanical zero records.
  Replaced with one correctly continued 18-state phase record per element,
  using the existing Case 1/frozen UEL quad and triangular initialization
  convention. Mechanical states default to zero. Verified individual GP
  committed history indices 9–12 on a nonuniform synthetic history witness.
- Step 1 donor displacement used the default ramp from zero. Added constant
  amplitude `CONST_HOLD`, preserving the intended fixed-load hold.
- Corrected the old unit-test fixture to provide nodal damage at all nodes;
  its previous one-entry dictionary was neither a full nodal field nor an
  unambiguous elemental field. The physical assertion was preserved.
- Original new regression attempt: three failures (state record malformed;
  two subprocess checks also exposed invalid inherited Windows stdin).
  Explicit DEVNULL repaired the subprocess harness. Final affected suite:
  12 passed. These tests do not qualify the numerical workflow.

## Scientific specification conflict — no solver launched

Frozen SHA256:
`CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6`.
The quadrilateral mechanical branch, source lines 517–525, computes

`POS_M = lambda/2 * positive(trace(eps))^2 + mu * (eps11^2 + eps22^2 + 2*eps12^2)`.

This is not Miehe's spectral tensile energy. The latter retains only positive
principal strains in the term multiplied by mu; see Miehe, Hofacker and
Welschinger (2010), *A phase field model for rate-independent crack propagation*,
[primary paper](https://doi.org/10.1016/j.cma.2010.04.011).

Offline witness (`audit_frozen_split.py`), E=210 kN/mm², nu=0.3:

| Tensor strain | Frozen POS_M (kN/mm²) | Miehe tensile energy (kN/mm²) |
|---|---:|---:|
| eps11=eps22=0, eps12=0.001 | 0.000161538461538 | 0.0000807692307692 |
| eps11=eps22=-0.001, eps12=0 | 0.000161538461538 | 0 |

This is an algebraic witness, not an Abaqus patch test. It establishes a
specification incompatibility, not the resulting crack path or numerical
convergence. The unchanged frozen formulation could be tested as a disclosed
Method C shear demonstration, but cannot be labelled a faithful Miehe
reproduction. A spectral variant would alter frozen physics and requires
explicit scientific direction; none was created.

## Remaining work and resume condition

Resolve which formulation defines the experiment, then implement and qualify
the bounded execution loop, authentic checkpoint extraction, existing transfer
reuse, hold/advance gate sequencing, broad causal refinement, completion and
stall monitoring, and cycle evidence publication. The current default proposed
schedule (0.0095 coarse, six increments of 0.0015 mm) is a draft; distinguish
it from the supplied paper schedule and the repository's documented historical
schedule conflict. Do not silently substitute one.

Before execution, resolve geometry-versus-load-drop completion semantics:
the draft uses a 20% force condition and a path-length shortcut not equivalent
to the supplied bottom/right-boundary-or-5%-force definition. No results exist
that justify changing the acceptance criterion.

No local solve, datacheck, submission, retry or source change was made during
this recovery audit. Numerical uncertainty remains the transferred shear
response and deflected crack path. Next measurable numerical test must be
defined against the resolved formulation and exact schedule, not launched
under contradictory physics requirements.

## Bridge routing finding

The guarded publisher was tested with -DryRun using matching request
HND-METHOD-C-MODE2-RECOVERY-001 and a structured research_contract. It
rejected the new goal with BRIDGE_RESEARCH_SCOPE_CONFLICT: use the canonical
METHOD_C numerical objective. The canonical policy still names the prior
METHOD_C_INCREMENTAL_ADAPTIVE_REMESHING_V1 goal; it has not been synchronized
with the supplied new dispatch. No ready file was published, no PAD flow
launched, and no review response or approval is claimed. The existing policy
and bridge transactions were preserved. The formulation decision is pending
with the user; resolving that scientific conflict takes precedence over
starting any solve.

## Subsequent user decision and bounded runtime preparation

The user explicitly resolved the formulation question in this session:
"Keep the frozen UEL and report Mode II as a Method C shear demonstration
with a disclosed formulation difference." The earlier scientific decision
block is therefore resolved; no source modification is authorized or needed.

Completed a local runtime reusing the existing Case 1 transfer function
unchanged (the implementation is spatial nearest-neighbour transfer, not
bilinear interpolation; no contrary claim is made). It writes full checkpoints,
refuses automatic retries of existing run folders, checks actual Jacobians,
extracts actual U1/RF1 and SDV fields read-only, follows the notch-connected
damage component including downward growth, writes per-cycle paired images,
and commits/pushes each cycle with pinned image provenance. No internal
boundary displacements are prescribed. The global maximum-damage gate remains
the dispatched acceptance measure; it is not evidence of pointwise irreversibility.
Hold force and energy are measured after the two-step job as in the inherited
framework; failure prevents donor acceptance and subsequent cycles. This
post-job timing is explicitly disclosed, not claimed as a pre-advance gate.
The watchdog is polled every five seconds during solves, with clean Abaqus
termination on its stall thresholds and preserved blocker evidence.

Exact first numerical action: one coarse cycle on one local CPU in a fresh
scratch folder, with a separately named datacheck, unchanged coarse deck and
frozen source. Coarse target U1=0.0095 mm. This tests toolchain/deck convergence
and authentic damage/shear response; it does not qualify transfer. The fresh
runtime will stop after this coarse qualification for result inspection.

Bounded subsequent proposal: at most seven adaptive cycles, nominal target
increment 0.0015 mm and upper target 0.0200 mm; actual Riks displacement is
recorded, never assumed equal to target. This is a Method C demonstration
schedule, not a literal reproduction of contradictory printed schedules.
Completion means the notch-connected d>=0.95 component reaches the actual
bottom/right boundary, or reaction force falls below 5% of the observed peak.
A cycle cap is partial progress. The runtime does not use path-length or 20%
force shortcuts. L-panel remains conditional on independent Mode-II review.

Canonical bridge goal/scope was synchronized to the user's supplied new
dispatch and formulation decision, with old packet contexts preserved.
Current source/deployed rules hash:
6DF468F0BC35DD1728130AC65BB65490AE3EB8C9C528C6D60B85E44223C850C9.
The original scope rejection remains recorded above; it was not bypassed
by inventing approval, changing the goal label or directly writing ready files.

## First real qualification: inherited property-order defect (preserved)

Attempt R0, D:\mc3_local\mode2_qualification_20261124_1558: datacheck
completed, then the real solver ran. Reaction force at U1=0.000798 mm was
5.1871383e-7 kN, prompting inspection of the actual property card. The inherited
coarse deck supplied `210,0.3,0.0027,0.015,1e-7,2960`, while frozen source lines
212–217 read `l0,Gc,E,nu,k,N_PHYS`. Consequently it ran with l0=210 mm and
E=0.0027 kN/mm²: scientifically invalid input, despite a passing datacheck.
Codex stopped that exact local job via normal `abaqus terminate` at 16:01 CET.
Its scratch files, lightweight .sta/.dat and diagnosis are preserved. No
partial state is accepted as donor and no successful cycle is claimed.

Corrected the coarse generator's property order, regenerated the input,
and added a semantic preflight rejecting mismatched material cards before
Abaqus execution. The field-output interval is .005, matching the already
specified coarse max dt=.005 rather than silently forcing .001 time points.
The frozen source remains unchanged. A distinct technical replacement R1
has a fresh exact input hash, manifest and scratch folder; the R0 accounting
is not reset. Exactly one R0 datacheck and one R0 solver start were consumed.
R1 is bounded to one new datacheck and one new coarse solve on one CPU.
Affected tests after correction: 16 passed. No adaptive execution is implied.
