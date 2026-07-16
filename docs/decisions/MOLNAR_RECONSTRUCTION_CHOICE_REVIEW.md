# Molnar Reconstruction Choice Review

Date: 2026-07-16

Scope: candidate-v1 reconstruction-choice review only. This review does not select a new scientific route and does not authorize Abaqus/PBS execution.

## Reconstruction Choices

| Choice | Chosen value | Why it was chosen | Available paper evidence | Limitation | Effect on benchmark | Accepted for candidate v1 |
|---|---|---|---|---|---|---|
| Refined-zone bounds | x=-0.02..0.5 mm, y=-0.005..0.005 mm | Cover notch-tip process zone and horizontal ligament with local h | Paper says region around crack path is refined to h=0.001 mm | Bounds are not published; generated deck does not realize a variable-size zone | Controls local resolution and element count | No, because deck has structural failures |
| Global mesh size | 0.025 mm | Produce a coarse surrounding mesh while staying near approximate element count | Paper gives about 22000 elements, not global size | Not published | Controls far-field cost and transition | No, pending generator revision |
| Transition rule | linear_size_growth over 0.02 mm | Deterministic transition compatible with documented mesh-quality target | Single-notch paper text does not state a transition rule; double-notch text mentions linear transitions | Not published for this benchmark | Controls mesh grading | No, pending generator revision |
| Maximum size ratio | 1.5 | Conservative neighbouring-size ratio | No direct paper value | Reconstruction choice | Controls element-quality risk | No, pending generator revision |
| Final displacement | 0.0067 mm | Measured from Fig. 7 visible extent | Fig. 7 axis/curve extent only | Not exact_from_text | Sets final plotted/analysis endpoint | No, loading schedule contradiction must be resolved |
| Fine increment count | 170 | Derived from (0.0067 - 0.005) / 1e-5 | Paper gives fine increment but not count | Derived from measured endpoint | Controls post-peak resolution | Provisionally yes after loading revision |
| Response-based contour states | final, peak force, first post-peak RF2 <= 0.5 peak | Avoid invented numerical displacements for unlabeled Fig. 6 panels | Fig. 6b shows contour but no displacement labels | Requires future run response | Enables matched contour comparison without fake labels | Yes as a comparison plan |

## Decision

- [ ] Candidate-v1 reconstruction choices accepted for first baseline run
- [x] Revise reconstruction choices before running
- [ ] Supervisor review required before running

Reviewer: Codex no-run provenance review

Date: 2026-07-16

Conditions:

- Revise the generator/deck to include an explicit notch representation.
- Add UEL property blocks for U1 and U2 layers.
- Add or document the in-plane rigid-body constraint.
- Resolve the Step-1 loading inconsistency before changing `runnable` to true.
- Re-run static validation and update the checklist/reports before requesting a baseline run.
