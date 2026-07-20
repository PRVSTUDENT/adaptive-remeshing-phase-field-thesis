# Stage B HPC Resource Estimate

Status: `h_convergence_subset_authorized_execution_pending`

This file estimates resource risk for Stage B planning. The supervisor has
authorized only the three-case `lc = 0.015 mm` h-convergence subset. PBS
requests for that subset are defined in the dedicated study scripts and are
serial (`cpus=1`) only. Length-scale, increment-sensitivity, MISESERI, and
remeshing campaigns remain unauthorized and unestimated as executable work.

## Calibration Evidence

Current calibration run:

- job: `1374864.mmaster02`;
- classification: `paper_matched_v2_technical_pass`;
- physical elements: `33852`;
- layered elements: `101556`;
- equations: `102975`;
- increments: `670`;
- solver passes: `705`;
- walltime: `00:38:38`;
- CPU time: `00:35:52`;
- used memory: `2970760kb`;
- virtual memory: `3565868kb`;
- Abaqus peak memory: about `2 GB`;
- requested memory: `32gb`;
- requested walltime: `24:00:00`.

Candidate v2 is graded, so this calibration does not directly predict uniform
mesh cost. It is the only committed reference point available now.

## Provisional Resource Classes

| Class | Meaning | Request policy |
|---|---|---|
| `R0` | evidence-only current candidate-v2 reconstruction | no run |
| `R1` | first moderate uniform mesh | provisional; default to conservative serial request only after authorization |
| `R2` | fine uniform mesh | resource review required after `R1` |
| `R3` | optional confirmation mesh | separate authorization and queue/resource review required |

No final memory or walltime is assigned before the supervisor route is known.

## Initial Estimate Method

After each future run, estimate next-level cost from:

- equation-count ratio;
- increment-count ratio;
- observed walltime per increment;
- observed memory per equation;
- output size growth;
- convergence/cutback behavior.

The estimate must be written into the completed run summary before the next run
is requested.

## Stop Criteria

Stop before requesting the next run if:

- used walltime exceeds 75 percent of requested walltime;
- used memory or virtual memory exceeds 75 percent of requested memory;
- Abaqus reports memory pressure;
- solver iterations or decompositions grow sharply relative to the previous
  level;
- output size threatens evidence retention;
- the next level is predicted to exceed queue limits or the approved compute
  envelope.

## Submission Order

After supervisor approval and explicit user authorization:

1. Current evidence review only: `U0_L0_I0`.
2. First moderate uniform mesh: `U1_L0_I0`.
3. Resource and scientific review.
4. Fine uniform mesh: `U2_L0_I0`.
5. Decide whether optional confirmation `U3_L0_I0` is needed.
6. Length-scale and increment studies only after mesh convergence is reviewed.

No MISESERI, adaptive remeshing, or state transfer should start from this
resource estimate.
