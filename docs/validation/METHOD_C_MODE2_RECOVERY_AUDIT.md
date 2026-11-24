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

## Corrected coarse qualification R1 — authentic result

The one-CPU corrected coarse job completed successfully, .sta increment 200,
U1=0.009499999694526196 mm, RF1=0.3980390131473541 kN, averaged companion
maximum damage=0.35076945275068283, tip detector remains at (0.5,0.5) mm,
2960 elements / 3036 nodes. Measured solve elapsed 180.04 seconds.
This is a pre-adaptive donor, not forward-growth or transfer evidence.
Source remains CE8D5EDC. Input SHA256 3349F60B04C8FBF849A83D8028ECAED5BEC09DA25B50995C0B5D0C595CD05207.
Image and solver artifacts committed, with pinned manifest, and pushed through
89fcbacd7. Scratch checkpoint:
D:\mc3_local\mode2_qualification_r1_20261124_1602\PK_METHOD_C_MODE2_COARSE_JOB1_checkpoint.json.

Next bounded numerical operation: exactly one adaptive cycle from this donor,
using a fresh scratch folder, existing nearest-neighbour transfer unchanged,
actual donor data only, broad tip-controlled refinement h_ref=.007 mm,
fixed-load hold and target donor U1+0.0015 mm. One CPU, one datacheck, one solve,
no automatic retry, zero PBS. Test measurable force continuity <=5% and the
unchanged global-maximum-damage gate; record energies, actual target/response,
connected damage geometry, cost and hashes. Failure preserves evidence and
blocks further cycles for independent review. Latest offline suite: 18 passed.

## First remesh preparation and technical datacheck correction

Cycle 1 R0 generated 5028 physical elements (4848 quads, 180 tris; 96.42%
quads), minimum quadrature Jacobian 2.9596e-8, maximum edge-length ratio 3.05,
median refined h=.006462 mm. Datacheck rejected TYPE=SOLUTION continuation
records with INVALID INTEGER VALUE; no Cycle 1 solver was started.
The companion material incorrectly declared DEPVAR30. Its global continuation
count consumed the next element label as state data, then interpreted a
continuation float as an integer label. Corrected DEPVAR to 20, matching the
validated Case 1 builder and frozen visualizer's STATEV1–20 layout. The 18 UEL
variables remain unchanged; the last two companion slots default to zero.
Rejected diagnostics and mesh audit are preserved under failed_preparation/
depvar30_cycle1_r0; the full rejected deck remains in its original scratch.
A distinct bounded R1 candidate uses a fresh scratch folder and scope; no
identical retry or reset accounting. The material/order correction and this
continuation correction change no frozen source or declared physical inputs.

Cycle 1 R1 datacheck confirmed the state continuation correction: no invalid
integer errors remained. It then diagnosed one independent input error,
`YOU ARE MIXING OP=NEW AND OP=MOD FOR *BOUNDARY`: the inherited first-step
OP=NEW card conflicted with the constant-amplitude card's default OP=MOD.
Normalized the first step to default OP=MOD throughout (as in Case 1);
constraints and constant donor hold are unchanged. R1 diagnostics preserved
under failed_preparation/boundary_operation_cycle1_r1; no R1 cycle solve
started. R2 is a distinct freshly scoped datacheck/solve candidate, not an
identical rerun; input errors do not consume a PBS submission or imply a
numerical transfer result.
