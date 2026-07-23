# Mistakes And Fixes Log

This file is the consolidated ledger for execution mistakes, solver failures,
workflow mistakes, and bounded fixes. Failed attempts stay recorded; a later fix
does not erase the original evidence.

Status terms: `resolved`, `open`, `external block`, or `scientific limitation`.

## Ledger

| ID | Job/stage | Mistake and consequence | Fix or current action | Status |
|---|---|---|---|---|
| M-001 | Process | Failure information was distributed across checklists, reports, status JSONs, commits, and run folders, with no single project-wide ledger. | Maintain this file at `docs/project/MISTAKES_AND_FIXES_LOG.md`; append every failed attempt, diagnosis, correction, rerun, and prevention rule without deleting predecessors. | Open process improvement |
| M-002 | `1374529` | Intel `ifx` was loaded without a compatible GCC environment; `ifx --version` failed with compiler error `#10417`. | Load `gcc/11.4.0` before `intel/2024.2.0`, then load `abaqus/2023`. | Resolved by `1374531` |
| M-003 | `1374530` | The batch script attempted to run `git` on the compute node, but `git` was absent from the batch `PATH`. | Resolve the Git revision on the login node and pass it through `PROJECT_REVISION`; do not require Git inside PBS. | Resolved by `1374531` |
| M-004 | `1374532` | The UEXTERNALDB smoke used a relative marker path, so callback entry could not be proven although solve, compile, link, license checkout, and ODB creation passed. | Use `GETOUTDIR` to construct an absolute marker path, write callback tokens to Abaqus output, capture `IOSTAT`, and preserve build evidence. | Resolved by `1374533` |
| M-005 | Early PBS scripts | Failure-safe evidence collection was incomplete; scripts could exit before staging logs, binaries, command files, or callback evidence. | Capture solver return codes without immediate `set -e` termination; always stage `.msg`, `.dat`, `.sta`, `.log`, `.com`, inventories, and status JSON. | Resolved as workflow rule |
| M-006 | Candidate v1 | No explicit source-faithful split notch was implemented. | Candidate v2 added documented notch construction and validation. | Resolved |
| M-007 | Candidate v1 | U1 and U2 layers lacked the required UEL property blocks. | Add complete UEL property definitions derived from the preserved source formulation. | Resolved |
| M-008 | Candidate v1 | The in-plane rigid-body constraint corresponding to the original boundary arrangement was missing. | Reconstruct and validate the original boundary-condition mapping. | Resolved |
| M-009 | Candidate v1 | Loading was internally inconsistent: `500 x 1e-4 mm = 0.05 mm`, although `0.005 mm` was intended. | Resolve and freeze the displacement schedule before deck generation. | Resolved |
| M-010 | Candidate v1 | The generated mesh was a uniform structured skeleton and did not implement the stated refined strip and transition recipe. | Build candidate v2 with the documented refined-region and mesh-transition implementation. | Resolved |
| M-011 | `1375020` | The targeted SDV15 diagnostic again used a compute-node Git revision guard; `git` was unavailable, so Abaqus was never launched. | Prestage an immutable package on the login node and carry the revision in a manifest/environment variable. | Resolved in R2 infrastructure |
| M-012 | `1375028` | Abaqus solved successfully, but postprocessing used Python 3.9-style built-in generic annotations that the cluster interpreter could not parse. | Rewrite for the available interpreter and replay postprocessing from retained outputs without rerunning Abaqus. | Resolved by no-solve replay |
| M-013 | SDV15 analysis | Call-level values and intermediate staggered calls could be mistaken for accepted converged states. | Reduce each increment to its final relevant U1 update, align events by step time/load level, and compare only consecutive converged increment states. | Resolved methodologically |
| M-014 | SDV15 diagnostic | The initial run did not retain enough direct evidence to distinguish true completed-increment phase decreases from call-order artifacts. | Add target-gated source logging, deterministic monitored targets, completed-increment classification, and severity auditing. | Resolved as diagnostic procedure |
| M-015 | Submission preflight | Input hashes containing relative paths were checked from the wrong directory, making valid staged inputs appear missing or mismatched. | Run `sha256sum` from each case directory so relative entries resolve correctly. | Resolved |
| M-016 | PBS staged-input guard | The same relative-path assumption was repeated inside staged PBS checks. | Change into each staged case folder before validating hashes. | Resolved |
| M-017 | CAE postprocessing | Scripts used syntax or libraries unsupported by Abaqus Python; a successful solver could be followed by a CAE failure. | Make extraction scripts Abaqus-Python compatible and keep ordinary analysis/comparison in module Python. | Resolved |
| M-018 | PBS dependency design | `afterok` linked downstream mesh jobs to the entire upstream wrapper, so a postprocessing failure could cancel later solver jobs even when the upstream solve passed. | Separate solver status from postprocessing status; use `afterany` plus explicit `.ok` markers/status JSON for scientific gating. | Resolved |
| M-019 | CAE command interface | Paths supplied through `abaqus cae noGUI=... -- arguments` were contaminated by Abaqus CAE argument handling. | Pass ODB and output paths through dedicated `MOLNAR_*` environment variables. | Resolved |
| M-020 | ODB export | The postprocessor accessed an Abaqus field-value element label using the wrong API assumption. | Correct the element-label access for the returned field-value object. | Resolved |
| M-021 | HPC Python compatibility | `Path.write_text(..., newline=...)` was used, but the available Python version did not support that argument. | Use `open(..., newline=...)` or `write_text()` without the unsupported argument. | Resolved |
| M-022 | C2B | Cluster Python mismatch and unsupported annotations crashed C2B and caused `afterok` dependents to be cancelled. | Pin the intended Python version, remove incompatible annotations, and resume from the successful C2A result. | Resolved |
| M-023 | C2C | `baseline_original` was not prestaged, so the deck rebuild failed although upstream data existed. | Prestage preserved baseline sources, validate required products explicitly, and resume from frozen C2B. | Resolved |
| M-024 | C2C | Hash checks treated Windows CRLF and HPC LF versions of the preserved source as different scientific inputs. | Accept the historical CRLF hash and LF-normalized equivalent while still rejecting content changes. | Resolved |
| M-025 | C2C | Path relativization assumed one literal scratch root; `/scratch` versus `/scratchN` aliases caused a successful build to abort during path reporting. | Use a safe `path_under_root` helper and support home, prestage, and scratch aliases. | Resolved |
| M-026 | C2D | ODB extraction and numerical qualification were run under one incompatible Python environment. | Split Abaqus-Python ODB extraction from module-Python comparison and validation. | Resolved |
| M-027 | MISESERI v1 | `0.05` was interpreted as an absolute raw MISESERI threshold, marking nearly everything and generating an approximately 160k-element over-refined mesh. | Define the algorithm as `MISESERI/max(MISESERI) > 0.05`, retain notch-dominant components, bound refinement windows, and reject the over-refined product. | Resolved in C2C-v2 |
| M-028 | Terminology | The normalized threshold was described as though it were native Abaqus absolute `errorTarget` semantics. | Rename it `relative_MISESERI_threshold` and document the exact implemented formula. | Resolved |
| M-029 | C2E/F-v2 prestage | The refined deck was generated locally/untracked and assumed to be available through Git staging. | Copy the explicitly validated product from its known home/prestage location and verify its hash. | Resolved |
| M-030 | C2F-v2 `1376444` | The generated target lacked an exact `y=0` line and open notch faces, producing a continuous plate, about 72% stiffness error, and no expected softening. | Force the exact `y=0` line, duplicate notch-face nodes, run geometry/stiffness/SDV probes, and build notch-corrected C2F-v3. | Resolved |
| M-031 | Efficiency reporting | C2F-v3 used four threads while original H1 reference was serial, making direct walltime comparison unfair. | Run and use an H1 four-thread baseline for fair cost comparison. | Resolved |
| M-032 | PBS mail | Email settings were inconsistent between tracked directives and actual `qsub` command. | Use verified recipients in `#PBS -M` and `qsub -M`, retain `-m abe`, and add a `mailx` begin/end fallback. | Resolved |
| M-033 | Crack-path closeout | The crack-path extractor had Abaqus-Python compatibility problems, and H1 submission did not propagate the intended mail environment correctly. | Repair the extractor and H1 qsub mail environment before closeout. | Resolved |
| M-034 | T5 `1376598` | The guard searched only the immediate output directory, but generated products were nested; empty paths caused `IsADirectoryError`. | Discover products recursively and deterministically; fail with explicit missing-product status; add smoke-specific validator mode. | Resolved by corrected T5 rerun |
| M-035 | D2A preparation | The visualization/displacement layer used elastic modulus `1e-11`, unsuitable even for a stable routing harness. | Change the visualization/displacement modulus to `1.0` while preserving tiny nonphysical smoke-test scope. | Resolved before accepted D2A |
| M-036 | D2A output assumption | The plan assumed UEL phase DOF would be available as usable nodal `U` output; Abaqus did not expose it in the smoke deck. | Verify phase ingestion through UMAT `SDV15` and history through `SDV16`; record nodal phase output as unavailable. | Resolved with limitation |
| M-037 | D2B `1376819` | Release/continuation steps allowed only two increments; Abaqus found a convergent smaller increment but exhausted the increment count. | Change only maximum increment count from `2` to `50`; preserve all state, mesh, physics, and loading settings. | Resolved by `1376825` |
| M-038 | D2D planning | ABAQUSER was treated as forthcoming before executable/module/interface availability was confirmed. | Perform login-node availability audit first; formally block D2D when no executable, source, module, or interface is found. | External block |
| M-039 | D3A `1376868` | Extractor used Abaqus `frameId` as a Python list index; the two values are not guaranteed identical. | Store and use the actual enumerated frame-list index separately from `frameId`. | Resolved |
| M-040 | D3A `1376877` | Python 2.7 `csv.DictWriter` received dictionaries containing fields not listed in `fieldnames`. | Filter every row to declared output fields before `writerow`. | Resolved |
| M-041 | D3A `1376879` | Accepted H0 source ODB was selected before confirming required global energy histories existed; it lacked `ALLIE`, `ALLSE`, and `ALLWK`. | Audit ODB outputs before eligibility; reconstruct energy independently from retained state when justified. | Resolved through D3A-E |
| M-042 | D3A-E first CAE attempt | Field extraction was too slow because code repeatedly scanned large ODB field arrays for individual values. | Build keyed lookup dictionaries once and perform direct element/IP access. | Resolved |
| M-043 | D3A-E R0 `1376885` | Parser mixed `Part-1` and assembly node namespaces; assembly RP node 1 overwrote physical part node 1, creating five false non-positive Jacobians. | Track `*Part` and `*Assembly` scopes separately; use only `Part-1` nodes/U1 elements for physical quadrature. | Resolved by R1 |
| M-044 | D3A-E validation | Negative Jacobians were initially interpreted as mesh defects before checking whether parser scope altered coordinates. | Audit affected connectivity and duplicate labels before changing accepted mesh or applying `abs(detJ)`. | Resolved; no mesh modification |
| M-045 | Energy evidence | The original UEL `ENERGY(2)=ENG` assignment could not automatically be treated as verified domain-integrated fracture energy. | Reconstruct external work, degraded bulk energy, undamaged bulk energy, and AT2 fracture energy independently using quadrature and accepted state fields. | Resolved |
| M-046 | D3A closure | A blocked result risked being overwritten when a later corrected route passed. | Preserve the missing-energy block and failed R0 separately, then create `D3A.ok` only from scope-corrected R1 evidence. | Resolved |
| M-047 | Initial D3A2 target | A structured target had a geometric `y=0` line but no mechanically open split seam; the 6561-node count revealed an unsplit `81x81` grid. | Duplicate the 40 open-notch face nodes, keep the tip shared, and validate coincident pairs, notch length, crossing connectivity, and Jacobians. | Resolved |
| M-048 | Target validation | Standard mesh-count and positive-Jacobian checks alone were insufficient to detect an unsplit notch. | Add a dedicated notch-topology audit requiring distinct face labels and zero elements crossing the open seam. | Resolved |
| M-049 | Transfer validation | A transfer package could pass coverage and bounds while still using the wrong target topology. | Make notch-topology success a prerequisite for `D3_PACKAGE.ok`. | Resolved |
| M-050 | D3A3 `1377382` | PBS loaded only `abaqus/2023`; `ifort` was unavailable in the clean batch environment, so user-subroutine compilation failed before analysis. | Explicitly load `gcc/11.4.0`, `intel/2024.2.0`, and `abaqus/2023`; record paths and versions inside PBS. | Resolved in R1 environment |
| M-051 | D3A3-R1 `1377383` | The 25600-record history field was compiled into enormous Fortran `DATA` statements; fixed-form continuations did not avoid Intel's per-statement token limit. | Replace compiled table with a runtime `d3_transfer_h.dat` loaded once through `UEXTERNALDB`. | Partly resolved; R2 exposed file-staging issue |
| M-052 | D3A3-R1 source | UEL searched all 25600 transfer records for every physical element and IP, producing unnecessary quadratic-style work. | Load directly into `USRVAR(element,16,IP)` once, then use constant-time direct indexing. | Addressed in R2 |
| M-053 | D3A3-R1 initialization | History initialization occurred from element calls guarded by shared logical flags, creating shared-state/call-order risk for future threaded execution. | Perform initialization in serial startup logic inside `UEXTERNALDB`; validate completeness there. | Addressed in R2 |
| M-054 | D3A3 UEL | The phase stored at all four IPs was the same arithmetic nodal average, not Q4 interpolation at each Gauss point. | Evaluate `d_q=sum_a N_a(xi_q,eta_q)d_a` separately at every IP. | Open |
| M-055 | D3A3 physical model | The prepared UEL used zero residual/identity tangent and dummy stiffness, so it could not establish physical checkpoint equilibrium, RF continuity, or release behavior. | Base R2 on the accepted Molnar physical UEL/UMAT formulation, changing only element count, offsets, transferred-state initialization, and target connectivity. | Addressed in R2 |
| M-056 | D3A3 postprocessor | `extract_d3a3_ingested_state.py` was only a request/placeholder writer. | Implement real Abaqus-Python extraction for ingestion, fixed-phase equilibrium, release frames, SDV15/16, RF-U, and state comparisons. | Addressed in R2 prep |
| M-057 | D3A3 validator | Validator checked only whether expected output files existed; it did not calculate ingestion errors, irreversibility, RF jump, or energy jump. | Implement numerical gates and create markers only after thresholds pass. | Addressed in R2 prep |
| M-058 | D3A3 execution strategy | Two full PBS submissions were attempted before a separate compile/datacheck gate existed; both failed before solver analysis. | Add one small compile/datacheck job and submit full ingestion only after `D3A3_R2_COMPILE.ok`. | Addressed in R2 prep |
| M-059 | D3A3-R2 `1377389` | Runtime H loading avoided the R1 compile-token limit: Abaqus compiled and linked the user subroutine and completed input processing. Datacheck then failed because `UEXTERNALDB` opened relative `d3_transfer_h.dat` from Abaqus internal `/local/...` workdir where the file was not staged. | Bounded successor M-060 uses `GETOUTDIR` and `HFILE(1:LHFILE)` so Standard opens the staged runtime-H file from the launch/output directory. Do not submit full D3A3-R2 before a compile/datacheck pass. | Open predecessor; no `D3A3_R2_COMPILE.ok` |
| M-060 | D3A3-R2-R1 pathfix prep | A relative runtime-H file path was unsafe because Abaqus/Standard can execute from an internal `/local/...` workdir that differs from the PBS launch directory. | Update `UEXTERNALDB` to call `GETOUTDIR`, construct `OUTDIR//'/d3_transfer_h.dat'`, print the resolved path, open `FILE=HFILE(1:LHFILE)`, and report path plus `IOSTAT` on failure. Static path audit rejects the old relative open, `d3_transfer_table.inc`, and `D3_TRANSFER_COUNT`; runtime-H SHA256 remains `4689ea5c10c0972e69ba46f8676a326c8b011b98faa8031c7c26cfb218607cd9`. | Prepared; corrected datacheck pending |

## Scientific Findings And Limitations

These should not be labelled as implementation mistakes:

1. Candidate-v2 completed-increment SDV15 decreases persisted after compatible postprocessing and are a scientific/formulation finding.
2. C2F-v3 post-peak mismatch and crack-path deviation from H1 are repeatable results, not failed implementation.
3. D1 analytical transfer errors are measured baselines and must not be described as negligible.
4. D2D ABAQUSER unavailable is an external availability block after audit, although availability should have been checked earlier.
5. PBS history `job_state=F` means finished, not necessarily failed; use `Exit_status`, solver status, markers, and output evidence together.

## Maintenance Rule

For each future entry, append:

```text
ID:
Date:
Stage/job:
Source commit:
Classification:
Symptom:
Root cause:
Scientific inputs changed: yes/no
Correction:
Retry job:
Outcome:
Evidence paths:
Prevention rule:
Status: resolved/open/external block/scientific limitation
```

Never replace the original failure entry after a correction passes; link the
failed attempt to the accepted successor.
