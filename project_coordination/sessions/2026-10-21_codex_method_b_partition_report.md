# Method B partition-study explanation correction - 21 October 2026

Task: SUPERVISOR-REPORT-METHOD-B-PARTITION
Starting commit: a3a940618a60ae998c9d3801597e04531d375807

Corrected the canonical five-page supervisor report to distinguish Method A from Method B without claiming an unsupported advantage. Both are one-remesh/two-pass methods. B parameterizes pre-analysis loading (1/2/4 steps) and field-selection opportunities; it does not transfer loaded state across meshes or execute multiple adaptive cycles. One-step B reduces to A's architecture at the same controls.

Finding A is the archived verified loading-partition invariance result: terminal MISESERI fields identical, native 14,677-element meshes identical. Finding B is the separate retrospective 14,483-element ligament-resolution verification: peak error -1.86%, matched work error -3.87%, partial horizon 0.007889 mm. The improved fracture response is not attributed to loading-partition count. The report gives a bounded linear-elastic companion-layer interpretation and explicitly says intermediate-frame advantages, evolving damage and different loading histories were not established by this comparison.

New deck parser and three-row diagram read actual M1_MB_INF_1S/2S/4S execution decks, verify input names against their PBS wrappers, extract step names/durations, absolute prescribed RP-U2 targets, initial/max increments and per-increment MISESERI requests. Actual equal endpoint increments are supported by decks, not assumed: 1S=0.005; 2S=0.0025/0.005; 4S=0.00125/0.0025/0.00375/0.005 mm. Each step lasts 1.0 model-time units, so totals are 1/2/4. Last Step-1/2/4 frame selection is traced to the manifest; archived 500-total-increment, zero-cutback completion supports local terminal increments 500/250/125. One remesh follows selection. Diagram is labeled prescribed deck-derived history, not newly measured solver output; static pseudo-time is not runtime. Provenance records exact controls and source hashes. No historical ODB was reopened or missing arrays recomputed.

Visuals now distinguish A/B workflows and genuine native 14,677-element geometry from the separate retrospective 14,483-element verification mesh. Native tip close-up restored to genuine native geometry. Accurate Method C four-cycle explanation, authentic C1/C2 mesh views, and C2 force/healing limitations preserved.

Validation:
- Builder exit 0; parsed deck/manifest/wrapper/result assertions passed.
- Existing test_mode1_f1461_method_b_step_partition_invariance: 1 passed (pytest selected test; 0.15 s).
- PDF reopened with five pages; every page rendered and visually inspected. Step endpoint annotations adjusted to avoid overlap; no clipping/orphan pages.
- Required scientific distinctions, quantities, Markdown image links, source/output SHA-256 hashes verified; matched work unchanged at 2.267379222 / 2.358731686 mJ (-3.87295%).
- Temporary PDF validation initially used an exact substring across a PDF line break and failed; whitespace-normalized check passed, with report/science unchanged.
- git diff --check passed for revised report text and builder.

No solver/HPC/controller/model changes. Original unrelated dirty paths preserved. Only verified report artifacts, builder and mandatory coordination closeout records staged. Forward-only origin/main synchronization uses HEAD:main on the existing branch.

Artifact hashes:
- docs/supervisor_reports/22-10-2026/SUPERVISOR_REPORT_SUCCESSFUL_RESULTS_ONLY.md: 6f167ddea3e03135c79f833371f43a0b8157be8608fc61ad1754b93d84f618b2
- docs/supervisor_reports/22-10-2026/SUPERVISOR_REPORT_SUCCESSFUL_RESULTS_ONLY.pdf: 4b0404ca992665b340dd74af0d36307e1a2451a4f66314a83be14bc4c3d2ea24
- docs/supervisor_reports/22-10-2026/FIGURE_SOURCES.md: 344260961931be28e8671f7c8eadf907f6c463331eba4ffa9197cb4069247240
- docs/supervisor_reports/22-10-2026/build_successful_results_report.py: edeced4872b840b01a6ab2329d66bf271382a4d1a07f6911ce086c4f289c62ba
- docs/supervisor_reports/22-10-2026/figures/method_b_workflow.png: fc7256b5bd54bc632c002d1b0e3f81247132b24f7a918fa336a830946769d5d5
- docs/supervisor_reports/22-10-2026/figures/method_b_loading_schedules.png: 91d027faa05ceaf2e6003580db044482a37236e420f974412df32b85390b3293
- docs/supervisor_reports/22-10-2026/figures/mesh_artifacts.png: cd7f35c95f50d3cb3855c5f4f7a6f79d757ff8e60775797421282f35c45b7a77
- docs/supervisor_reports/22-10-2026/figures/native_crack_tip.png: e83566d5aa565fd7e49472ae079ede548c27467600944264c64d47fdaaa01815
