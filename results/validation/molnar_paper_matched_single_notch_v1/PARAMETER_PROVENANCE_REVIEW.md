# Parameter Provenance Review - Molnar Paper-Matched Single-Notch v1

Date: 2026-07-16

Candidate: `paper_matched_candidate_v1`

Review scope: no-run provenance and generated-deck review. No Abaqus command was run, no PBS job was submitted, and preserved Molnar supplementary files were not modified.

## Review Decision

Classification: `static_validation_fail`

Configuration runnable status: `false`

Candidate v1 is not ready for a baseline run. Several source-traceable and reconstruction-choice values are documented correctly, but the generated deck has structural and provenance mismatches:

- The generated deck does not explicitly represent the left-edge notch/crack cut.
- The generated deck lacks UEL property blocks for the U1 and U2 layers.
- The generated deck lacks an in-plane rigid-body constraint equivalent to the supplementary `bottoml`/`topl` convention.
- The configured coarse schedule is internally inconsistent: `500 * 1e-4 mm = 0.05 mm`, but `coarse_displacement` is `0.005 mm`.
- The deck Step-1 amplitude/step representation gives `0.005 mm / 500 = 1e-5 mm` per increment, not the configured `1e-4 mm`.

## Summary Counts

| Result | Count |
|---|---:|
| Parameters reviewed | 33 |
| PASS | 20 |
| ACCEPTED_RECONSTRUCTION_CHOICE | 8 |
| FAIL | 5 |

## Parameter Review Table

| Parameter | Value used | Unit | Provenance status | Source | Generated-deck location | Config match | Snapshot match | Manifest match | Review result | Limitation |
|---|---:|---|---|---|---|---|---|---|---|---|
| Geometry width | 1.0 | mm | exact_from_figure | Molnar Fig. 6a | node coordinate extent x = -0.5..0.5 | yes | yes | n/a | PASS | none |
| Geometry height | 1.0 | mm | exact_from_figure | Molnar Fig. 6a | node coordinate extent y = -0.5..0.5 | yes | yes | n/a | PASS | none |
| Notch geometry | left notch length 0.5 at y=0 | mm | exact_from_figure target | Molnar Fig. 6a | not represented as cut/discontinuity in generated deck | config target yes | snapshot target yes | n/a | FAIL | deck is a full rectangle; no explicit notch representation found |
| Loading direction | alpha = 90 | deg | exact_from_text | Molnar Sec. 3.2/Fig. 6b | RP vertical displacement, U2 | yes | yes | n/a | PASS | x constraints incomplete, see rigid-body row |
| Plane-strain condition | true | - | exact_from_text | Molnar Sec. 3 | U1/U2/CPS4 2D skeleton | yes | yes | n/a | PASS | element-property formulation not complete |
| Physical thickness | 1.0 | mm | exact_from_text/supplementary | Molnar Sec. 3; supplementary deck | CPS4 solid section thickness 1.0 | yes | yes | n/a | PASS | UEL property blocks missing |
| Young's modulus E | 210 | kN/mm^2 | exact_from_text | Molnar Sec. 3.2 | absent from UEL property block | config yes | snapshot yes | n/a | FAIL | U2 layer has no `*Uel property` containing E |
| Poisson's ratio nu | 0.3 | - | exact_from_text | Molnar Sec. 3.2 | UMAT material constants include 0.3 | yes | yes | n/a | PASS | UEL displacement property missing |
| Critical energy release rate Gc | 0.0027 | kN/mm | exact_from_text | Molnar Sec. 3.2 | absent from UEL property block | config yes | snapshot yes | n/a | FAIL | U1 layer has no `*Uel property` containing Gc |
| Residual stiffness | UEL 1e-7; UMAT 1e-11 | - | exact_from_supplementary | SingleNotch.inp | UMAT constant 1e-11 only | yes | yes | n/a | FAIL | UEL residual stiffness property missing |
| Length scale lc | 0.0075 | mm | exact_from_text | Molnar Sec. 3.2 | absent from UEL property block | config yes | snapshot yes | n/a | FAIL | U1 layer has no `*Uel property` containing lc |
| Local h | 0.001 | mm | exact_from_text target | Molnar Sec. 3.2 | not directly encoded as variable; estimator reports minimum size | yes | yes | n/a | PASS | generated grid is a reconstruction skeleton |
| h/l | 0.13333333333333333 | - | derived | h/lc | mesh_statistics.csv | yes | yes | n/a | PASS | none |
| Refined-zone bounds | x=-0.02..0.5; y=-0.005..0.005 | mm | adopted_reconstruction_choice | project reconstruction choice | configuration only; deck has uniform structured grid | yes | yes | n/a | ACCEPTED_RECONSTRUCTION_CHOICE | not published; deck does not actually vary mesh by zone |
| Global mesh size | 0.025 | mm | adopted_reconstruction_choice | project reconstruction choice | configuration/mesh statistics | yes | yes | n/a | ACCEPTED_RECONSTRUCTION_CHOICE | not published |
| Transition width and rule | 0.02; linear_size_growth | mm / rule | adopted_reconstruction_choice | project reconstruction choice | configuration only | yes | yes | n/a | ACCEPTED_RECONSTRUCTION_CHOICE | not published; not physically realized in generated uniform grid |
| Maximum neighbouring-size ratio | 1.5 | - | adopted_reconstruction_choice | project reconstruction choice | configuration only | yes | yes | n/a | ACCEPTED_RECONSTRUCTION_CHOICE | not published |
| Element topology | structured quad skeleton | - | adopted_reconstruction_choice | project reconstruction choice | U1/U2/CPS4 quadrilateral elements | yes | yes | n/a | ACCEPTED_RECONSTRUCTION_CHOICE | not paper mesh topology |
| Element aspect-ratio rule | 5.0 | - | adopted_reconstruction_choice | project reconstruction choice | configuration only | yes | yes | n/a | ACCEPTED_RECONSTRUCTION_CHOICE | not checked as a mesh-quality report yet |
| Physical/visualization-layer construction | U1/U2/CPS4 | - | exact_from_supplementary pattern | SingleNotch.inp | U1, U2, CPS4 blocks | yes | yes | counts yes | PASS | UEL property blocks missing |
| Element offsets | 1, N+1, 2N+1 | element ID | exact_from_supplementary pattern | SingleNotch.inp | element IDs 1, 21761, 43521 | yes | yes | counts yes | PASS | none |
| Node offset rules | shared nodes plus RP | node ID | adopted_reconstruction_choice | supplementary RP convention | RP node 22346 after mesh nodes | yes | yes | nodes yes | PASS | none |
| RF extraction set | RP, RF2/U2 | - | exact_from_supplementary/reconstruction | SingleNotch.inp | `*Nset, nset=RP`; `*Node Output, nset=RP` | yes | yes | n/a | PASS | none |
| Required SDVs | SDV on `umatelem` | - | exact_from_supplementary | SingleNotch.inp | `*Element Output, elset=umatelem`; `SDV` | yes | yes | n/a | PASS | none |
| Final displacement | 0.0067 | mm | measured_from_figure | Fig. 7 extent | Amp-2 ends at 0.0067 | yes | yes | n/a | ACCEPTED_RECONSTRUCTION_CHOICE | not exact_from_text |
| Coarse increment count | 500 | increments | exact_from_text count | Molnar Sec. 3.2 | Step-1 `inc=500` | yes | yes | n/a | PASS | displacement increment mismatch below |
| Coarse displacement increment | 1e-4 | mm | exact_from_text target | Molnar Sec. 3.2 | deck gives 0.005/500 = 1e-5 | config yes | snapshot yes | n/a | FAIL | config and deck are internally inconsistent |
| Fine increment count | 170 | increments | derived | Fig. 7 endpoint and fine increment | Step-2 `inc=170` | yes | yes | n/a | PASS | derived, not stated |
| Fine displacement increment | 1e-5 | mm | exact_from_text target | Molnar Sec. 3.2 | deck gives 0.0017/170 = 1e-5 | yes | yes | n/a | PASS | none |
| Contour comparison states | final, peak, post-peak 50% | response states | reconstruction_choice | Fig. 6 unlabeled | configuration only | yes | yes | n/a | ACCEPTED_RECONSTRUCTION_CHOICE | future frame selection depends on run response |
| Selected Fig. 7 curve | Molnar red dashed lc=0.0075 | - | exact_from_figure/inferred target | Fig. 7 legend | reference files | yes | yes | n/a | PASS | approximate digitization only |
| Digitization uncertainty | +/-0.00004; +/-0.015 | mm; kN | measured_from_figure | metadata | `FIG7_DIGITIZATION_METADATA.md` | yes | yes | n/a | PASS | overlap/line-width uncertainty |
| Generated physical elements | 21760 | elements | generated | generator/manifest | 21760 physical IDs per layer | yes | yes | yes | PASS | close to approximate 22000 but not exact |
| Generated layered elements | 65280 | elements | generated | generator/manifest | 65280 element IDs | yes | yes | yes | PASS | none |

## Digitized Reference Review

- Raw file: `fig7_lc_0p0075_raw.csv`, 877 points.
- Processed file: `fig7_lc_0p0075_processed.csv`, 91 points.
- Selected curve: red dashed Molnar `lc = 0.0075 mm` curve in Fig. 7.
- Axes: `u [mm]` and `F [kN]`, matching metadata.
- Classification remains `approximate_published_reference`.
- Ambiguous regions: pre-peak overlap with the other Molnar curves and Miehe symbols; steep post-peak drop has increased uncertainty.
- No smoothing/interpolation is presented as author-supplied data.

## Loading Schedule Review

The generated deck implements:

```text
*Amplitude, name=Amp-1
0., 0., 1., 0.005
*Step, name=Step-1, nlgeom=NO, inc=500
*Static, direct
0.002, 1.
```

This gives a candidate Step-1 displacement increment of `0.005 / 500 = 1e-5 mm`, not the configured `1e-4 mm`. Also, the config row `coarse_steps = 500` and `coarse_increment = 1e-4 mm` implies `0.05 mm`, not the configured `coarse_displacement = 0.005 mm`.

Step 2 is internally consistent:

```text
*Amplitude, name=Amp-2
0., 0.005, 1., 0.0067
*Step, name=Step-2, nlgeom=NO, inc=170
*Static, direct
0.00588235294117647, 1.
```

This gives `(0.0067 - 0.005) / 170 = 1e-5 mm`.

## Contour-State Review

Fig. 6 panels do not provide confirmed numerical displacement labels. Candidate v1 correctly avoids invented panel displacements and uses response-based states:

| Planned state | Source status | Future frame-selection rule | Review |
|---|---|---|---|
| Final Fig. 6b comparison | unlabeled figure panel | final converged state | accepted as response-based |
| Peak force | reconstruction choice | frame at maximum RF2 | accepted as response-based |
| Post-peak propagation | reconstruction choice | first post-peak frame with RF2 <= 0.5 peak | accepted as response-based |

Missing exact Fig. 6 displacements would not by itself block a first baseline run, but the current generated deck is blocked by structural and loading-schedule failures.

## Structural Deck Review

| Check | Result | Evidence |
|---|---|---|
| Deck hash matches manifest | PASS | `645231291b4ec5c40e8f649e7386159332c595e3e93c0de50ba91b7f01f5ea88` |
| Generator determinism | PASS | regenerated hash unchanged during review |
| Node IDs unique | PASS | validator |
| Element IDs unique | PASS | validator |
| Connectivity references valid nodes | PASS | validator |
| Layer counts and offsets | PASS | 21760 physical, 65280 layered |
| UEL property blocks | FAIL | no `*Uel property` block found |
| Notch geometry present | FAIL | no explicit notch/crack cut or comment found; generated grid is rectangular |
| In-plane rigid-body constraint | FAIL | no U1 constraint equivalent to supplementary `bottoml`/`topl` found |
| Boundary condition top displacement | PASS | RP U2 displacement and equation present |
| RF set and SDV request | PASS | RP output and `SDV` on `umatelem` present |
| Absolute Windows/HPC paths | PASS | none found in deck |
| Preserved source hashes | PASS | original SingleNotch hashes match recorded values |

## Remaining Blocking Items

1. Revise the generator so the single-edge notch is physically represented in the mesh/deck.
2. Add correct UEL property blocks for the U1 phase layer and U2 displacement layer.
3. Add or document the intended in-plane rigid-body constraint equivalent to the supplementary deck.
4. Resolve the coarse loading inconsistency: paper text `1e-4 mm for 500 steps` conflicts with candidate `0.005 mm` endpoint; the deck currently implements `1e-5 mm` increments in Step 1.
5. Re-run static validation after revision.

## Final Classification

```text
static_validation_fail
runnable: false
```

Gate A3 remains:

```text
Gate A3: reference_data_insufficient
Stage A: open
```
