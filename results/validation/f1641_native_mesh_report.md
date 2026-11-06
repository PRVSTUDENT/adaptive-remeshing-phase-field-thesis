# F1641: one actual native indicator-driven hole mesh

**Verdict: mesh generated and evaluated; local resolution NOT ACCEPTED for production.** No solver run, datacheck or PBS submission occurred. F1641 remains open for scientific review of this measured failure; no execution successor is registered from an unaccepted mesh.

## Actual generated mesh and reproducibility

Candidate `PK_HOLE_F1641_1PCT` contains **130,435 physical elements** (127,175 quads, 3,260 triangles), **129,657 physical nodes**, and a generated three-layer deck with 391,305 elements. Physical input is preserved under `models/pandey_kumar_mode1/176_method_a_plate_with_hole/f1641_native_1pct/`. Its SHA256 is `22BF94EBF19AD007F1E8754D884048B95C272A1EAF0AA9D19C29BC4793DBDB5A` (9,731,419 bytes), identical locally and remotely. Text capture removed one final LF; restoring that one byte reproduced the exact remote hash.

The layered input remains at `/scratch9/pr21vyci/runs/mode1_hole_method_a_f1641/PK_HOLE_F1641_1PCT_PROD.inp`, SHA256 `F29D0C49BC8751479521ABCAEED20D1FD03B1783EB9D3EA4EFBC3DE86D6BB2CE`. It is an unqualified candidate, not a frozen-source datacheck result. No UEL was executed.

The deterministic command is `scripts/remeshing/generate_f1641_native_candidate.sh`, calling the canonical generator with native Abaqus2023 `UNIFORM_ERROR`, **errorTarget=1.0 percentage point**, coarse seed0.020mm, min0.001mm, max0.020mm, refinementFactor10. This tests whether tightening the existing2% target improves phase-field resolution. It does not reinterpret raw MISESERI as a percentage. No refinement corridor, CAD partition or prescribed crack path was added.

The generator now supports an explicit reuse-only branch with mandatory ODB hash, matching coarse element/node identities, and no solver submit/wait calls. The ordinary branch retains existing behavior. Geometry is reconstructed identically and compared against the authentic coarse ODB before adaptiveRemesh. Source ODB SHA256 remained `0A108C6A8404F1AF9D8F5DDC03223E9D8D051AB08587F841D9F5799970AE93B1` after generation. Source generator hash matches locally/remotely: `A57A240749DDD76A020E93B6F96406D3875825816DD981F5F69ABAA3752A2E95`.

## Measured comparison

All rows below use the SAME conservative characteristic size: maximum consecutive boundary-edge length of each element. Historical reports sometimes summarized individual edge populations; those different statistics must not be compared as identical measures. Regions are the existing diagnostic zones, used only to measure the mesh, never to prescribe refinement.

| Metric | New native1% | Existing native2% | Rejected coarse-source candidate |
|---|---:|---:|---:|
| Physical elements | 130,435 | 46,747 | 31,035 |
| Physical nodes | 129,657 | 46,651 | 31,037 |
| Tip-zone median h, µm | 1.8637 | 1.8427 | 2.7439 |
| Tip-zone fraction h≤1.5µm | 5.28% | 8.71% | 0.00% |
| Ligament-zone median h, µm | 1.7490 | 1.8034 | 3.0831 |
| Ligament-zone fraction h≤1.5µm | 14.13% | 12.47% | 0.163% |
| Hole-band median h, µm | 2.1160 | 2.1484 | 4.0910 |
| Nonpositive Jacobian/area elements | 0 | 0 | 0 |
| Minimum interior angle, degrees | 25.747 | 30.367 | 28.241 |
| Maximum edge aspect ratio | 3.183 | 2.479 | 2.586 |
| Maximum adjacent sqrt(area) ratio | 3.061 | 2.933 | 2.626 |

Candidate global h spans0.3748–15.6560µm, median2.2035µm. Tip-zone h/l0 min/median/max=0.1653/0.2485/0.3950; ligament=0.1258/0.2332/0.4122; hole band=0.1608/0.2821/0.4231. The documented requirement is h/l0≤0.2 where fracture resolution is required. Full coverage of the diagnostic tip/ligament/hole regions fails. Even the initial tip region is not resolved by that criterion; a favorable lower percentile cannot establish acceptance.

Quad Jacobians were checked at all four2×2 Gauss points; triangle signed areas were checked directly. Minimum measured determinant=2.30822e-8mm². There are zero nonmanifold edges. The minimum triangle mean-ratio or quad corner scaled-Jacobian quality is0.6186. Adjacent sqrt(area) grading median/p90/max=1.0424/1.1907/3.0610. These are measured quality descriptors; no new retrospective angle/aspect/gradation acceptance threshold was invented.

## Geometry and indicator response

Plate bounds remain exactly[0,1]×[0,1]mm. The finite slit retains the established half-opening0.001mm and length0.5mm; both tip-corner position errors are1.3e-8mm. Hole center/radius are unchanged at(0.65,0.65),0.1mm. Its314 boundary nodes have maximum radial error4.10e-8mm; maximum straight-chord midpoint error6.744e-6mm. Mesh area0.9675862156mm² versus exact slit/circle area0.9675840735mm². No geometry-boundary load was added; the candidate builder retains the original outer-boundary displacement sets. Traction-free hole behavior still requires future solver/input qualification.

Native remeshing used the authentic recovered MISESERI field, complete on2,906 coarse elements. For a separate diagnostic association, each new centroid is paired with its nearest authentic coarse centroid (explicit approximation, not a new sizing algorithm). Spearman rho between raw MISESERI and h is−0.67154. Median h falls from4.1921µm in the lowest indicator quartile to1.9109µm in the highest decile. Thus refinement responds spatially to the indicator, but this does not guarantee the phase-field length criterion. The existing2% mesh gives rho−0.87525 under the same association diagnostic.92.55% of candidate elements lie outside the diagnostic tip/ligament/hole zones.

## Scientific acceptance and execution readiness

The one tested hypothesis—tightening native UNIFORM_ERROR from2% to1% with unchanged bounds suffices for local phase-field resolution—is **not supported**. Element count increases2.79× while median initial-tip h is slightly larger. This is evidence against obtaining the required local resolution by blindly tightening the global error target. Preserve the candidate; do not sweep errorTarget or weaken h/l0 to obtain a pass. A distinct localized sizing hypothesis requires scientific review and must remain indicator-driven, without a fixed crack corridor.

This verdict is based on measured resolution, **not an eight-hour rejection**. Live read-only PBS evidence confirms `longq` max168h and `normal_imfdfkmq` max336h; both are route-only. Enabled `entry_imfdfkmq` routes to normal/short, allows the account's `t2-dl-rights-hpc_hw_kieferams` group, and itself has max336h. That verifies a configured eligible long-duration route; no test qsub was manufactured. It does not prove a future submission will be accepted. CPU/memory and exact allocation still require package-specific qualification; serial remains the scientific anchor, SMP requires parity evidence. Hole fracture runtime has not been measured; no production walltime is inferred from the element-count increase.

The old1CPU/16GB/8h limit belongs to the legacy adapter, not universal scheduler capacity. Canonical/deployed bridge rules now distinguish those scopes (97lines, identical hashes). The adapter itself was not bypassed or broadened. F1641 still permits zero PBS and no solver; the local frozen UEL remains unchanged. Historical scratch UEL mismatch remains unresolved for future frozen-source datacheck.

## Tests, bridge and next action

Nine focused generator/hash/coverage/geometry-metric checks pass. An initial pytest teardown failed on pre-existing `pytest-current` permissions after seven assertions passed; an isolated explicit basetemp repaired that deterministic local test-environment failure. The actual mesh validator evaluated all three meshes once and wrote `f1641_native_mesh_metrics.json`; original output is preserved.

First live bridge exchange passed. Second transaction `HND-CODEX-76f296e313674518b1f729057d62773b` failed INVALID_JSON because the response was raw goal text. Original failed receipt and raw archive are preserved; it is not numerical approval. The subsequent direct user message independently authorized this exact mesh generation. A durable reconciliation record closes the failed transport as failed and archives the stray ready file without replay. No PAD flow, clipboard or userscript was modified.

Next action: independent scientific review of the failed native1% sizing hypothesis and the measured regional resolution. Select one evidence-backed correction before generating another mesh. F1641 remains open; an execution successor/datacheck is withheld until a mesh meets declared scientific criteria. Method C stays paused and the overall Method A Goal remains active.

Fresh result-review handoff HND-CODEX-fd28bbfa72e44082a97d56d21d44e77f returned RECEIVED_VALIDATED in106seconds. Its planning verdict rejects this mesh for production and requests ONE offline locally constrained indicator-sizing hypothesis and authenticated independent scientific review before another candidate. No new mesh/solver/PBS is permitted in that next definition operation. This planning reply is not signed approval.
