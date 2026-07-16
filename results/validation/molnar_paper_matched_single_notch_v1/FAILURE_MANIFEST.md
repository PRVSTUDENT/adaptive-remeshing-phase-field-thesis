# Candidate v1 Failure Manifest

Date: 2026-07-16

Candidate: `paper_matched_candidate_v1`

Final static classification:

```text
static_validation_fail
runnable: false
```

Candidate v1 is preserved as failed static evidence. It must not be silently repaired in place or submitted to Abaqus/PBS.

## Blocking Defects

1. No explicit source-faithful notch/crack representation.
2. Missing UEL property blocks for the U1 and U2 layers.
3. Missing in-plane rigid-body constraint equivalent to the original `bottoml`/`topl` arrangement.
4. Inconsistent Step-1 loading schedule: `500 * 1e-4 mm = 0.05 mm`, not `0.005 mm`.
5. Generated mesh is a uniform structured skeleton and does not physically implement the documented refined strip and transition recipe.

Evidence:

- `STATIC_VALIDATION.md`
- `PARAMETER_PROVENANCE_REVIEW.md`
