# Post-Supervisor Decision Execution Routes

Date: 2026-07-18

Status: `route_neutral_plan`

Gate A3 remains `reference_data_insufficient`. This note does not choose a
route and does not authorize new Abaqus/PBS work.

## Current Frozen Inputs

- Candidate v2: technically passed.
- Scientific review: incomplete.
- SDV15 completed-increment result:
  `sdv15_completed_increment_irreversibility_violation`.
- SDV16 completed-increment decreases: `0`.
- Gate A3: `reference_data_insufficient`.
- New solution run: not authorized.
- Supervisor package revision:
  `a7294b30851d7190ee91c8bf92390bf32b2442c8`.

## Route A - Candidate v2 Accepted With Limitation

Supervisor decision:

- Candidate v2 may be used as the Stage A reproduction baseline, with explicit
  limitations on RF--U mismatch and SDV15 completed-increment behavior.

Required documentation updates:

- Update `docs/reports/STAGE_A_BASELINE_REPORT.tex` with the accepted-limitation
  decision.
- Update `docs/reports/STAGE_A_EXECUTION_AND_FAILURE_LOG.tex` with the
  supervisor decision date and wording.
- Update `.agent.md`, `adaptive_remeshing_phase_field_agent.md`, and
  `docs/project/PROJECT_PHASE_CHECKLIST.md`.
- Keep the SDV15 limitation visible in thesis text and final figure/table
  captions.

Required static validation:

- Re-run existing static validators only for unchanged candidate-v2 consistency
  if new downstream scripts depend on the deck.
- No candidate-v2 source or deck modification is implied.

New solution authorization needed:

- Yes, for any Stage B uniform-reference, mesh-size, length-scale, or
  load-increment studies.

Uniform-reference studies may begin:

- Yes, after explicit supervisor/user authorization and after acceptance
  metrics are written.

MISESERI/remeshing remains blocked:

- Yes, until a justified uniform fine reference is established and Gate B
  prerequisites are satisfied.

## Route B - Gate A3 Waiver

Supervisor decision:

- Gate A3 is waived for proceeding to a limited next phase, while candidate v2
  remains scientifically incomplete.

Required documentation updates:

- Record the waiver scope, exclusions, and expiration condition in
  `docs/decisions/`.
- Update Stage A reports and handoff files with `Gate A3: waived_with_limits`,
  not `passed`.
- Add thesis caveats explaining that the waiver is procedural, not scientific
  validation.

Required static validation:

- Re-run static deck/source/hash checks before any authorized new solve.
- Validate that no candidate-v2 scientific model changes are hidden in the
  next-stage inputs.

New solution authorization needed:

- Yes. The waiver does not itself authorize computation.

Uniform-reference studies may begin:

- Only if the waiver explicitly permits them and acceptance metrics are written
  before evaluation.

MISESERI/remeshing remains blocked:

- Yes, unless the waiver explicitly includes downstream remeshing work. The
  conservative default is blocked.

## Route C - Corrected Irreversibility Formulation Required

Supervisor decision:

- Candidate v2 cannot support Stage B until strict phase-field irreversibility
  is enforced or otherwise corrected.

Required documentation updates:

- Record candidate v2 as a technical reproduction baseline with a scientific
  irreversibility limitation.
- Create a new formulation decision record before implementation begins.
- Update Stage A reports, `.agent.md`, and the checklist to mark candidate v2
  as not accepted for Gate A3 closure.
- Preserve candidate v2 unchanged as historical evidence.

Required static validation:

- Required before any corrected formulation run.
- Include source-diff review, state-variable map updates, deck equivalence or
  intentional-difference documentation, Python compatibility checks, and
  validator updates for the corrected irreversibility behavior.

New solution authorization needed:

- Yes. Candidate v3 or any corrected formulation run requires explicit
  authorization.

Uniform-reference studies may begin:

- No. They must wait until the corrected formulation is implemented, statically
  validated, technically run, and scientifically reviewed.

MISESERI/remeshing remains blocked:

- Yes.

## Route D - Candidate v2 Rejected

Supervisor decision:

- Candidate v2 is rejected as a Stage A reproduction baseline.

Required documentation updates:

- Mark candidate v2 as rejected in Stage A reports, handoff files, and the
  project checklist.
- Preserve its technical-pass and diagnostic evidence as negative/limitation
  evidence.
- Record the replacement benchmark or revised formulation route in a new
  decision record before implementation begins.

Required static validation:

- Required for any replacement candidate or alternative benchmark.
- Candidate v2 validators remain historical; do not repair candidate v2 in
  place unless explicitly instructed.

New solution authorization needed:

- Yes, for any replacement solve or new benchmark.

Uniform-reference studies may begin:

- No. A rejected baseline cannot seed uniform-reference studies.

MISESERI/remeshing remains blocked:

- Yes, until a new Stage A route passes or is explicitly waived.

## Common Stop Rules

- Do not submit PBS or run Abaqus without explicit authorization.
- Do not implement candidate v3 unless Route C or Route D explicitly requests
  it.
- Do not start mesh-size, length-scale, load-increment, MISESERI, remeshing, or
  state-transfer work while Gate A3 remains unresolved without an explicit
  waiver.
- Do not convert a waiver into a scientific pass in reports, captions, or
  handoff files.
