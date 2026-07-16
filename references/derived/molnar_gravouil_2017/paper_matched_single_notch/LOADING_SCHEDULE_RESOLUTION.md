# Loading Schedule Resolution

Date: 2026-07-16

Candidate: `paper_matched_candidate_v2`

## Arithmetic Conflict

The candidate-v1 interpretation combined these statements:

```text
500 increments
increment size = 1e-4 mm
Step-1 endpoint = 0.005 mm
```

They cannot all be true because:

```text
500 * 1e-4 mm = 0.05 mm
```

Reaching `0.005 mm` in `500` increments requires:

```text
0.005 mm / 500 = 1e-5 mm
```

## Source Reinspection

The preserved supplementary deck contains `Amp-1` ending at `0.005` and `Step-1` with `inc=500`. That implementation therefore supports the Step-1 endpoint and count, and the displacement increment follows from arithmetic as `1e-5 mm`. The earlier `1e-4 mm` Step-1 interpretation is rejected for candidate v2.

The final plotted displacement remains an approximate Fig. 7 endpoint measurement at `0.0067 mm`. The post-Step-1 increment is retained as `1e-5 mm`; the count is derived as `(0.0067 - 0.005) / 1e-5 = 170`.

## Candidate-v2 Schedule

| Quantity | Value | Unit | Provenance status |
|---|---:|---|---|
| Step-1 initial displacement | 0.0 | mm | exact supplementary convention |
| Step-1 final displacement | 0.005 | mm | exact supplementary endpoint |
| Step-1 nominal increment | 1e-5 | mm | derived from endpoint/count arithmetic |
| Step-1 increment count | 500 | increments | exact supplementary count |
| Step-2 initial displacement | 0.005 | mm | continuity from Step 1 |
| Step-2 final displacement | 0.0067 | mm | measured from Fig. 7 extent |
| Step-2 nominal increment | 1e-5 | mm | paper interpretation retained |
| Step-2 increment count | 170 | increments | derived |
| Total final displacement | 0.0067 | mm | measured/inferred candidate endpoint |

Arithmetic checks:

```text
500 * 1e-5 mm = 0.005 mm
170 * 1e-5 mm = 0.0017 mm
0.005 mm + 0.0017 mm = 0.0067 mm
```

Status:

```text
loading_schedule_resolved_for_candidate_v2
```
