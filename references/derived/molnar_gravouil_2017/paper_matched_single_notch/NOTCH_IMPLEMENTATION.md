# Notch Implementation

Date: 2026-07-16

Candidate: `paper_matched_candidate_v2`

## Source Evidence

Molnar Fig. 6a shows a 1 mm by 1 mm plate with a left-edge notch of length `0.5 mm` at `y=0`. The preserved supplementary `SingleNotch.inp` uses an explicit crack-line topology near `y=0`; the line is not merely a comment or a post-processing convention.

The exact paper mesh topology is not published. Candidate v2 therefore uses a deterministic reconstruction choice that preserves the source geometry and does not tie the open notch faces.

## Candidate-v2 Construction

The generated deck duplicates nodes on the open notch segment:

```text
x in [-0.5, 0.0)
y = 0.0
```

It creates two node sets:

- `notch_lower_face`
- `notch_upper_face`

Elements below the crack line use the lower-face nodes. Elements above the crack line use the upper-face nodes. The notch tip at `(0.0, 0.0)` is represented by the shared grid coordinate at the crack tip.

Validation checks require:

- notch length `0.5 mm`;
- notch location at `y=0`;
- split opposing faces with no shared node IDs;
- zero physical elements bridging the open notch faces;
- visualization elements mirroring the physical topology.

Status:

```text
deterministic_split_node_reconstruction_choice
```
