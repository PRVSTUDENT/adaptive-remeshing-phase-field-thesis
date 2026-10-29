# Package146/147 authentic result reader implementation and review packet

Task: F1597-CORRECT-PACKAGE72-STATE-TRANSFER. Implementation task: F1597-PACKAGE146147-RESULT-READER. Starting commit: d68950c0ec00e0e4b672346aff7825061886be2e. Date: 2026-10-29.

## HPC STATUS

Independently queried exact PBS IDs through Invoke-GuardedSsh.ps1 (noninteractive, bounded, existing tu_freiberg alias). Both jobs are terminal F, Exit_status=0, run_count=1:

| Package | PBS ID | PBS name | Walltime | Step-1 accepted increment |
|---|---|---|---|---|
|146 donor|1418753.mmaster02|M1_C3_P146_DON|00:02:47|76|
|147 corrected reference|1418768.mmaster02|M1_C4_P147_REF|00:04:20|79|

Retrieved authentic DAT, STA, MSG, PBS log, UEL CSV, input, frozen UEL and terminal accounting. Base64 transport preserves original bytes; independently queried remote SHA256 values match each local artifact. Read-only Abaqus Python opened each existing ODB with readOnly=True; full accepted Step-1 history, endpoint U/RF and companion SDV fields were exported. ODB SHA256 before and after extraction matched. No ODB binaries were downloaded or committed.

Raw originals, complete compressed ODB exports (14.5MB and 20.7MB), query hashes and development/test logs remain outside Git:
C:/Users/pruth/OpenClawPAD/backups/package146147-reader-6ab68ef24c4f461ba7db8bd27b992081/{146,147}.
Each directory has manifest.json binding the exact remote directory, job ID, remote/local artifact digests, ODB digest and extractor revision. Review-ready JSON includes both manifests. The remote exports remain at /scratch9/pr21vyci/runs/package146147_result_review_codex/package146.json.gz and package147.json.gz. Explicit local cache outputs are made read-only after closeout; attributes guard accidental edits, not WORM storage.

## NEW EXPERIMENT

None. No job submissions, cancellations, moves, solver reruns, UEL edits, tolerance changes or controller registration. Abaqus Python was used only for ODB postprocessing. Existing once-only execution/receipt ledgers are not reset. Two genuine terminal-accounting events are appended for already submitted IDs; these are not new submissions. Notification delivery was not requalified or claimed by this task.

## SCIENTIFIC PROGRESS

Authenticated the actual final Step-1 frames by step name, increment, time, target displacement, accepted STA records, full energy CSV frame coverage and DAT/ODB agreement. Do not confuse the nominal historical "Frame77" label with Package147's actual final increment79/frame index79. Both end at uRP=0.0018003125442191958 mm.

| Measurement | Package146 | Package147 |
|---|---:|---:|
|RF2, kN|0.1873079389333725|0.18730823695659637|
|Elastic energy, kN mm|0.00016860480|0.00016860122|
|Fracture energy, kN mm|0.000044099740|0.000044386635|
|Total energy, kN mm|0.00021270454|0.00021298786|
|Physical nodes|5290|7265|
|Recorded GP points|20448|28224|
|Endpoint damage maximum|0.49527405|0.50354272|
|Damage bound violations (retained 1e-6 tolerance)|0|0|

Delta_E=100*(E147-E146)/E146=0.13319884944626892%; Delta_RF=100*(RF147-RF146)/RF146=0.0001591086985282366%. Existing raw-energy <=2% and RF <=5% numerical gates pass. Values in kN mm are joules; multiplying by1000 gives mJ. No Abaqus ALLSE/ALLPD/ALLFD substitution is used.

The frozen UEL's UEXTERNALDB LOP=2 writes accepted-increment elastic/fracture/global totals to uel_energy_balance.csv. Independent checks sum companion UMAT SDV17 fracture and SDV18 elastic once per physical element, verifying all four duplicated IP values agree rather than summing the element total four times. CSV and SDV sums agree within explicit export precision tolerances.

Using the existing centroid-containing donor-quad metric on the authenticated input decks, all7056 receiver quads satisfy refinement-only coverage: zero coarsened elements, area ratios0.6037998203400575..0.8569691243595188. This preserves the existing geometric constraint; it is not a new transfer criterion.

Scientific limitations remain explicit and block scientific acceptance:

- ODB U in these2D runs contains U1/U2, while the genuine nodal phase U3 is present in the final DAT table. Intermediate nodal U3 was not recorded in this ODB, so full nodal path irreversibility cannot be verified. No element-average phase is substituted for nodal phase.
- SDV2 records SV_H_TRIAL through the companion UMAT at accepted output frames. Recorded trial history is complete, finite and nondecreasing across Step-1 frames. Equivalence to the internal committed history array remains unverified and is never asserted as full state preservation.
- This is continuous-mesh sensitivity, not transferred-state re-equilibration or Stage C1-1/C1-2 acceptance. The evaluator explicitly returns scientific_acceptance=false and stage_c1_1_transfer_acceptance=false. Package113's failed cross-mesh energy gate and all previous scientific failures remain unchanged.

## DOCUMENTATION / IMPLEMENTATION

Repaired evaluate_package146_package147_results.py into a real authenticated reader. It requires manifest/file/remote hashes, exact PBS job identity and terminal exit0, frozen UEL and pinned input integrity, converged full Step-1 frame coverage and exact node/GP mappings before comparisons. It rejects nonfinite measurements, empty/inconsistent arrays, malformed/truncated data, incorrect steps/frames, nonconverged output, duplicate mappings, unphysical phase bounds and decreasing recorded history. UNAVAILABLE, INVALID_EVIDENCE and PHYSICAL_FAILURE remain distinguishable; missing evidence cannot yield a comparison. Existing local model sources are cross-checked if present; authenticated remote originals and pinned hashes remain mandatory, so a fresh checkout can use retrieved originals without committing pre-existing untracked Package147 files.

Added extract_package146147_odb.py for portable Abaqus2023 Python2.7 read-only extraction with ODB before/after hashing. No scheduler/solver invocation exists in it. Explicit --retrieve in the evaluator copies only already existing artifacts through the guarded wrapper, compares remote digests and creates new local destinations exclusively. It never uploads, submits or reruns anything. Report output also uses exclusive creation and cannot overwrite original evidence.

Replaced the misleading review-intake hardcoded True declarations with a packet builder requiring actual authenticated result evidence, current source/test/fixture hashes, a bound test receipt with zero failures/errors/skips and a result-report SHA256. It returns READY_FOR_INDEPENDENT_REVIEW, not registration or permission. The registry, qualification mechanism and scientific formulation remain untouched. No .qualification.json or executable-registration entry was created.

### Tests and preserved technical repairs

- Replaced the8 inadequate declaration tests with45 meaningful tests: 45 PASS,0 failures,0 errors,0 skipped. Includes authentic completed Mode-I endpoint DAT excerpts, actual UEL CSVs and PBS evidence, full authentic ODB exports, independent numerical recomputation, GP/element energy deduplication, and negative fixtures for NaN/Inf, empty arrays, bad lengths/labels, missing/truncated data/history, wrong frame/step, nonconvergence, tampering and physical bounds. All synthetic algorithm/adversarial fixtures are explicitly labelled and never presented as solver measurements.
- Existing Package146/147 read-only pytest regressions:12 PASS,4 deliberately deselected (package generation and remote staging/datachecks would mutate evidence/run new solver work).
- Existing controller operation checks:9 PASS. Existing definition-recovery checks:33 PASS. Total99 passing checks; no real controller/bridge/scientific dispatch.
- Compact authentic fixture corpus is282458 bytes, with original source hashes and exact excerpt rules in tests/fixtures/package146147/provenance.json. Full bulky exports/raw solver files stay in the external archive. Full-export tests require PACKAGE146147_ARTIFACT_ROOT; the recorded qualification run supplied it, with no skips. Default runs lacking the cache explicitly skip those tests and cannot create a review-ready receipt.

Development failures preserved in the archive: initial JSON inspection needed explicit float conversion for Abaqus numpy values; the guarded remote command needed an explicit shell script rather than timeout trying to execute shell builtin source. DAT parsing initially refused legitimate blank inactive RP columns and a fixed-width sign boundary; corrected using authenticated15-character columns while preserving missing RP DOFs as None. DAT8-significant-digit printing versus ODB float32 RF differed by1.1e-8kN; representation comparison now uses2e-7 relative tolerance, distinct from the unchanged5% scientific gate. One test initially demanded1e-12 absolute agreement between independently rounded CSV energy columns and failed at5e-12; its assertion now reflects the documented8-digit output precision, without changing the2% energy gate. Pytest isolated mode omitted user-site pygments; normal existing Python environment ran the read-only regressions successfully with no installation or global changes.

Review artifacts:
- results/validation/package146147/evaluation.json: complete extracted endpoint fields, node/GP mappings, scientific limitations and comparison.
- results/validation/package146147/test_receipt.json: source/fixture hashes, exact test counts and bound report digest.
- results/validation/package146147/review_ready.json: review packet, genuine provenance manifests and limitations.

Reproduce tests (no HPC action):
```powershell
$env:PACKAGE146147_ARTIFACT_ROOT = "$env:USERPROFILE/OpenClawPAD/backups/package146147-reader-6ab68ef24c4f461ba7db8bd27b992081"
python -m unittest discover -s tests/unit -p test_mode1_f1597_package146_147_evaluation_definition.py -v
```

Retrieve into a NEW external cache, only if needed (the completed ODB exports already exist):
```powershell
python scripts/validation/evaluate_package146_package147_results.py --workspace . --artifact-root <NEW-CACHE> --retrieve --output <NEW-REPORT.json>
```

## NEXT ACTION

READY FOR INDEPENDENT REVIEW of the corrected diagnostic evaluator. Review the source,45 artifact/adversarial tests, test receipt and genuine provenance before controller registration. No implementation/test evidence is missing for the recorded continuous-mesh diagnostic run. Missing scientific evidence is the full intermediate nodal U3 path and direct committed-array history/state-preservation proof; these remain limitations and cannot be converted into an irreversible transfer acceptance claim. The reviewer must retain this limited scope or require additional authentic state evidence before widening it. Do not register until that independent review approves; do not repeat the completed preparation/review-intake work or submit another experiment merely to populate this review packet.

Pre-existing dirty/untracked work, including CURRENT_STATE.md additions and Package147's untracked model tree, is preserved. Session released by restoring original inactive bytes.

Closeout metadata repair: git diff --check flagged authentic STA trailing column padding. Scoped .gitattributes now preserves exact fixture/review artifact bytes and exempts only *_step1_sta.txt trailing padding. No source-data bytes or hash-bound review sources changed. This preserves authentic artifact fidelity rather than trimming solver values. The pre-existing related Package147 SUBMITTED receipt row was preserved alongside the two new terminal events in the HPC ledger closeout.
