# Molnar Gate A3 Supervisor Decision Table

Status: `partially_resolved_by_decisions_1A_2B`  
Primary recording: `docs/decisions/MOLNAR_GATE_A3_SUPERVISOR_DECISION_1A_2B.md`

This table tracks residual supervisor items after Decisions **1A** (mesh roles)
and **2B** (contour deferred). RF–U mesh policy is frozen; Stage C preparation
is authorized. Remaining rows do not block preprocessing automation.

## Resolved by Decisions 1A / 2B

| Topic | Decision | Consequence |
|---|---|---|
| Fine RF–U validation mesh | **1A**: H2-PUB | validation reference only |
| Production/report mesh | **1A**: H1 | thesis/final simulations |
| Development/testing mesh | **1A**: H0 | debug / first MISESERI trials |
| Contour / crack-path gate | **2B**: deferred | does not block Stage C preparation |
| Stage C MISESERI preparation | authorized | no `qsub` without further approval |

## Residual / parallel items (do not block Stage C prep)

| Topic | Current evidence | Provisional project value | Supervisor decision needed | Consequence |
|---|---|---|---|---|
| Peak-force error (paper-matched lc=0.0075 narrative) | 6.4519% | 5% working gate | accept/revise/reject if paper-matched route still used | historical Stage A wording |
| Full RF-U NRMSE (paper-matched) | 24.5705% | 5% working gate | accept/revise/reject if needed | historical Stage A wording |
| Pre-peak mismatch (paper-matched) | pre-reference-peak RMSE 0.044136 kN | define | accept/revise | interpretation |
| Post-peak mismatch (h-conv + paper-matched) | H1→H2 post-peak NRMSE ~20% | documented limitation | retain limitation wording | Stage C claim boundary |
| Crack-path direction | deferred tools | qualitative later | deferred study | not Stage C gate |
| Crack extension threshold | 0.80-0.99 sensitivity | choose later | approve when path study runs | reporting |
| SDV15 decreases (candidate v2) | mapping resolved; residual insufficient_output_evidence / completed-increment findings | define tolerance/output requirement | approve interpretation if v2 claims are finalized | irreversibility narrative |
| SDV15 overshoot | max 1.005600 | define bound/tolerance | approve interpretation | bounds |
| SDV16 monotonicity | zero decreases at checked locations | monotone required | confirm | irreversibility |
| Approximate Fig. 7 data | digitized curve, not exact author data | approximate reference | accept as reference or require another route | paper comparison |
| Remeshing initial parameters | plan only | pending definition | approve errorTarget etc. before first remesh job | Stage C Job 3 |
| First five-job campaign submission | plan only | serial 5 jobs max | explicit `qsub` authorization | HPC execution |
