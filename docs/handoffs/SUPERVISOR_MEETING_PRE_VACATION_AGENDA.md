# Recommended Short Supervisor Meeting (≤ 30 min)

Status: `recommended_before_supervisor_vacation`  
Context: after decisions 1A and 2B; before first MISESERI HPC submission

## Agenda

1. **Confirm H0 / H1 / H2-PUB roles**  
   - H0 test/debug  
   - H1 production/report  
   - H2-PUB fine RF–U validation only  

2. **Confirm H1 as Stage C comparison reference**  
   - Uniform H1 vs MISESERI-refined targeting H1 local resolution  
   - H2-PUB secondary fine check only  

3. **MISESERI pre-analysis load mode**  
   - Elastic only, or partial fracture loading?  

4. **Approve initial remeshing parameters (record once; do not retune after final crack)**  
   - `errorTarget`  
   - `refinementFactor`  
   - `minElementSize`  
   - `maxElementSize`  
   - one remeshing pass  
   - coarsening disabled  

5. **Approve first limited HPC campaign and maximum job count**  
   - Five-job plan in `docs/studies/STAGE_C_FIVE_JOB_CAMPAIGN_PLAN.md`  
   - Serial only  
   - Explicit `qsub` authorization required  

## Current project stance (for confirmation)

```text
gate_a3_conditionally_accepted_rf_u
contour_validation_deferred
stage_c_miseseri_preparation_authorized
hpc_submission: not authorized until this (or equivalent) approval
```
