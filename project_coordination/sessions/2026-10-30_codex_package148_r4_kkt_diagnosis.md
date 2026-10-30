# Package 148 R4: bounded independent phase/KKT investigation

Starting commit: 0cd237719992c532b0bf930c7415829ae7a29e2b. Actual PBS job: 1418902.mmaster02, Exit1, 00:07:12. No new solver run, PBS submission, autonomous restart, R5 candidate, production-source edit or acceptance-threshold change occurred.

## Root cause

The coupled driver serializes each 18-SVAR `*Initial Conditions, type=SOLUTION` record as **element ID + eight values**, then eight values, then two values. The first line has nine fields. The documented format is **element ID + seven values**, followed by eight values per continuation line. For 18 states the correct layout is **7 + 8 + 3 state values**. The current generator silently shifts the intended H1..H4 from SVARS9..12 to the loaded vector **[H2, H3, H4, 0]**. All 7,056 records in each of the 21 actual input decks exhibit this defect (148,176 records).

This is an initial-state ABI/serialization defect, with a numerical consequence: Abaqus solves the phase equation for the shifted history while the driver evaluates KKT and updates the active set for the intended history. Those are different operators. Neither reversing KKT signs nor increasing the twenty-iteration cap addresses that mismatch.

Primary specification: SIMULIA [*INITIAL CONDITIONS, TYPE=SOLUTION](https://docs.software.vt.edu/abaqusv2025/English/SIMACAEKEYRefMap/simakey-r-initialconditions.htm), data-line section. The accessible manual is 2025; actual Abaqus2023 behavior is independently corroborated below, rather than inferred from that version alone. The frozen UEL reads history from SVARS(8+KPT), and its visualizer exports the observed shared history as SDV2.

## Direct causal evidence

1. Recovered 189 explicitly named text artifacts: input, DAT, MSG, STA, endpoint, receipt, solver/extractor stdout and energy CSV for mechanical solve00 and phase solves01..20. Reconciled every receipt/input/endpoint hash. All twenty phase STA files report successful Abaqus completion, one equilibrium iteration, no analysis errors/negative eigenvalue warnings. Their small linear residuals are genuine; the outer driver rejected the resulting fields.
2. Read all 21 existing ODBs with `openOdb(readOnly=True)`, verifying SHA256 before/after against their original endpoint receipts. No binary solver outputs were committed. Exported all observed H/IP and element-average damage values; two identical-history tables are losslessly deduplicated in odb_fields.json.gz. All twenty phase histories are identical. All 21 actual per-solve UEL copies remain bitwise CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6.
3. For every phase, the predicted final history `max(shifted-initial-H, psi(fixed-u))` matches **28,224/28,224** observed SDV2 values exactly at stored float32 precision. This also explains why end-of-call trial H is not the operator originally assembled by the phase element: the fully prescribed mechanical elements subsequently take the max with psi.
4. Reconstructing the actual shifted phase operator yields free-node residuals **<=1.2447719634474337e-12** across all twenty DAT-rounded endpoints. The intended operator gives free-node residuals 4.06e-8 to 7.87e-7 on the same actually unconstrained nodes. MSG solver residuals are around 1e-20. The remaining shifted-operator discrepancy is consistent with finite DAT precision.
5. The error causes genuine committed-history loss: mechanical solve00 already has **12,421** observed GP history values below H0 by more than 1e-6, with minimum H-H0 **-0.3593888282775881**. Phase solves have **12,323** such points and minimum **-0.3593897819519045**. Shifted high neighboring values also spuriously increase other GP histories. The unchanged H0 CSV/source bindings do not prove that Abaqus loaded the correct slots.

Example, actual element3484: intended history `[0.48311803552652544, 2.738001122528113, 4.376411032217344, 1.7402396696928961]`; shifted initialization `[2.738001122528113, 4.376411032217344, 1.7402396696928961, 0]`. After mechanical callbacks, observed SDV2 is `[2.7380011081695557, 4.376410961151123, 4.376410961151123, 1.7402396202087402]`, exactly the predicted float32 max operation. Authentic cards and both state vectors are preserved in state_card_fixture.json.

## All twenty iterations and failure classification

Earliest causal defect: mechanical initialization00, before phase1, when the malformed state records are read. Earliest unconstrained numerical evidence: **phase1** heals by **0.0350491**, and its endpoint satisfies the shifted equation instead of the intended one. Phase2 restores many constraints; phase3 returns to the other branch. This becomes a persistent near-two-cycle, not a sequence approaching tolerance. Every adjacent phase damage change has infinity norm **0.0350491** through iteration20; active-set changes still exceed 3,000 nodes at the end. There is small membership drift, so it is not an exactly repeated full-state cycle.

The full iteration summary is iterations.csv. nodal_kkt.csv.gz contains **145,300 node/iteration records**, including signed intended and assembled-operator residuals, signed damage increments, gaps and used/inferred/next active memberships. Thus all membership changes can be independently recovered without guessed iteration history. The table below uses the actually prescribed active set; r_min/r_max are the signed intended-operator residual extrema. Driver dual error uses its geometric bound classification, exactly as the frozen runtime does.

| Phase | Active BCs | Added | Removed | Min(d-d0) | Signed r min | Signed r max | Driver dual error |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 1 | 3266 | - | - | -3.504910E-002 | -7.867832E-007 | 8.020570E-007 | 7.867832E-007 |
| 2 | 6229 | 3388 | 425 | -1.381855E-003 | -2.465533E-007 | 8.463141E-008 | 1.663221E-007 |
| 3 | 2815 | 75 | 3489 | -3.504910E-002 | -7.867837E-007 | 8.020524E-007 | 7.867837E-007 |
| 4 | 6102 | 3378 | 91 | -1.381855E-003 | -2.465533E-007 | 8.463141E-008 | 1.663221E-007 |
| 5 | 2796 | 75 | 3381 | -3.504910E-002 | -7.867843E-007 | 8.020524E-007 | 7.867843E-007 |
| 6 | 6093 | 3375 | 78 | -1.381855E-003 | -2.465533E-007 | 8.463141E-008 | 1.663221E-007 |
| 7 | 2799 | 74 | 3368 | -3.504910E-002 | -7.867841E-007 | 8.020524E-007 | 7.867841E-007 |
| 8 | 6075 | 3354 | 78 | -1.381855E-003 | -2.465533E-007 | 8.463141E-008 | 1.663221E-007 |
| 9 | 2797 | 73 | 3351 | -3.504910E-002 | -7.867843E-007 | 8.020524E-007 | 7.867843E-007 |
| 10 | 6071 | 3348 | 74 | -1.381855E-003 | -2.465533E-007 | 8.463141E-008 | 1.663221E-007 |
| 11 | 2804 | 71 | 3338 | -3.504910E-002 | -7.867841E-007 | 8.020524E-007 | 7.867841E-007 |
| 12 | 6057 | 3325 | 72 | -1.381855E-003 | -2.465533E-007 | 8.463141E-008 | 1.663221E-007 |
| 13 | 2803 | 71 | 3325 | -3.504910E-002 | -7.867843E-007 | 8.020524E-007 | 7.867843E-007 |
| 14 | 6061 | 3329 | 71 | -1.381855E-003 | -2.465533E-007 | 8.463141E-008 | 1.663221E-007 |
| 15 | 2806 | 71 | 3326 | -3.504910E-002 | -7.867841E-007 | 8.020524E-007 | 7.867841E-007 |
| 16 | 6053 | 3318 | 71 | -1.381855E-003 | -2.465533E-007 | 8.463141E-008 | 1.663221E-007 |
| 17 | 2806 | 71 | 3318 | -3.504910E-002 | -7.867843E-007 | 8.020524E-007 | 7.867843E-007 |
| 18 | 6054 | 3320 | 72 | -1.381855E-003 | -2.465533E-007 | 8.463141E-008 | 1.663221E-007 |
| 19 | 2808 | 70 | 3316 | -3.504910E-002 | -7.867841E-007 | 8.020524E-007 | 7.867841E-007 |
| 20 | 6045 | 3307 | 70 | -1.381855E-003 | -2.465533E-007 | 8.463141E-008 | 1.663221E-007 |

All iterations have free_error <=1e-6 and complementarity product <=1e-6 (zero product violations at that threshold), but fail primal feasibility and signed dual conditions. There are **277–3,626** nodes per iteration with d-d0 < -1e-6. Driver dual errors alternate between approximately 7.868e-7 and 1.663e-7 versus the fixed 1e-9 tolerance. The complementarity product alone cannot certify this state.

## Variational inequality, constraints and previous behavior

For fixed u and admissible history H, the phase functional is the integral of `Gc*d^2/(2*l0) + Gc*l0*|grad d|^2/2 + H*(1-d)^2`. Its discrete derivative is `r=K(H)d-f(H)`. The lower-obstacle variational inequality requires `d>=d0`, r=0 on free nodes, r>=0 on lower-bound nodes and r*(d-d0)=0. The implemented sign and update `d-r/diag(K)<=d0` are consistent with this inequality **when the solver and evaluator use the same H**. No upper-obstacle multiplier is introduced; [0,1] damage bounds remain validation requirements.

Actual input BC audits confirm all physical U1/U2 values are prescribed consistently in every phase, no phase MPC equations are retained, and all selected active d constraints equal d0 exactly in the cards. Endpoint mechanical changes are <=1.6e-38 and active damage retention errors <=4.9996653206374475e-9. History cards are identical between phase solves, so there is no inter-iteration committed-baseline ratcheting in the driver; their malformed serialization is the defect. The local reconstruction of intended H differs from the actual serialized values by at most 6.572520305780927e-14 due to cross-interpreter arithmetic; analysis uses the exact serialized H, not a changed physical/KKT tolerance.

The earlier independent small-mesh/skew-element tests verified equations and signed KKT given an H array, and prior R1/R2/R3 failures stopped before a successful coupled phase loop. They did not verify Abaqus' state-card line/slot interpretation. Flattening all numerical tokens into an 18-value vector reproduces the writer's intention and misses the first-line overflow. Correct GP perimeter conversion alone cannot repair a shifted SVARS vector. R3's genuine mechanical/force/energy evidence remains preserved; it did not establish correct committed-GP state preservation.

## One falsifiable correction hypothesis

**Encode every 18-SVAR solution-initialization record with seven states on the element-ID line, eight on the next, and three on the last. Keep the existing slot9–12 perimeter mapping, frozen UEL, KKT signs, active update, physical thresholds and twenty-iteration cap unchanged.** Use one shared, independently decoded formatter for generated includes and coupled runtime cards; no numerical clipping or history substitution.

The hypothesis-only formatter exists in the forensic analyzer, not in the qualified runtime. Offline independent sparse replays of the intended fixed-u phase variational inequality converge in **8 iterations**, both in full precision and with eight-significant-digit DAT round-tripping. For the latter, final dual error=3.714982670536884e-10, free error=6.687649183149339e-10, complementarity=4.6911179041240575e-15 and min(d-d0)=-6.199619012603463e-10. No nodal clipping is used: active equalities are solved as VI constraints and free unknowns by the sparse linear system. This supports the hypothesis; it is not an Abaqus-coupled or full force/energy acceptance result.

Focused regression result: **24 tests plus 11 subtests PASS** (eleven new tests and the existing coupled-runtime suite). Cases cover 18 distinct sentinels, strict overflow rejection, authentic shifted history, correct round-trip GP slots, prediction of ODB fields, all twenty operator mismatches, primal/dual rejection despite small free/product errors, persistent oscillation, corrected bounded replay, exact convex-quadratic KKT signs and invalid state vectors. Production driver/UEL/qualification/manifests, all old failures and once-only ledgers remain unchanged.

Falsifier and exact next numerical action: after independent review of a serializer-only repair, qualify **one frozen-UEL, one-quad initialization/phase-operator parity solve** with nonuniform binary-exact history `[0.125,0.25,0.5,1]` and fixed mechanical displacement. Offline 18-distinct-SVAR round-trip must pass first. In the real parity solve verify the observable loaded slots9–12/SDV2, H>=H0, signed free/active residuals against the identical intended operator, and damage irreversibility using unchanged KKT thresholds. Use a bounded serial manifest (1 CPU, <=4GB, <=10min), genuine technical/notification checks and once-only execution. If loaded slots or operator parity still differ, reject this hypothesis and preserve the result; do not compensate by extending iterations. Only a passed parity result can support a separately reviewed full transfer correction. No such manifest, R5 package or job was created in this investigation.

## Unattended-execution safeguards

Keep the loop stopped. Its original Turn354 BLOCKED checkpoint remains byte-identical (SHA256 85E4EAF8A08AC8FFF8C9669E94F4E8E16B8DA4C74B9455B2DD26545C070D204B). That turn ended a diagnostic with a released session and missing scientific receipt. Governed reconciliation must preserve its run identity, error/receipt/log provenance and consumed operation IDs, then create a fresh explicitly scoped diagnostic/monitoring checkpoint. Do not manufacture Scientific/Complete evidence for Turn354 or replay R4's submit instruction. Repository session cleanup is performed only for this owned Codex session; no controller/AGY process is active.

Login-node Telegram/email preflight evidence exists, but real compute-node STARTED and terminal delivery still has no durable API acknowledgement in the job artifacts. Absence of notification warnings does not prove receipt. Before unattended operation require sanitized per-event evidence (PBS ID, node, event/time, HTTP200/ok=true for Telegram and verified email transport/delivery condition), including actual start and terminal paths, or a separately verified durable login-node relay/monitor. Preserve config mode600 and never log tokens. Until then classify compute delivery UNRESOLVED, not PASS.

Before eligibility, require semantic state-card round-trip and real phase-operator parity evidence, and durable per-phase signed residual/active-set/history/feasibility telemetry (R4 retained only an outer summary). Require fresh-process requested/selected operation and task-type agreement; a requested qualified operation must stop on missing registration rather than silently falling back into preparation cycles. Also retain once-only reservations, automatic_retry=false, no qdel/qmove, frozen-source and manifest checks, bounded process-tree watchdogs, error-stop/session-finally cleanup, finite/complete output and signed KKT checks. Refresh both authenticated quota windows immediately before any future launch; the old quota snapshot is not a current launch decision. An unconverged R4 result cannot authorize C1-2 or an automatic replacement.

Initial read-only postprocessing found that `abaqus` was absent from the noninteractive PATH; loading the existing gcc/intel/Abaqus2023 modules in a temporary bounded shell wrapper repaired that environment issue without a solver invocation. Initial diagnostic bitwise H reconstruction checks exposed only the 6.57e-14 arithmetic difference; using the exact existing input operator preserved the numerical evidence. Original solver evidence was never overwritten.

Finished
