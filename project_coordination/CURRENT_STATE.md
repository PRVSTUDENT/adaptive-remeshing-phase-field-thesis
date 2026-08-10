# Project Current State

# Current Project State - Stage C Mode-II Adaptive Comparison Contract Frozen

**Active Task**: `F43ADAPT-COMPARE-CONTRACT1`  
**Date**: 2026-08-10  
**Active Agent**: `gemini-antigravity`  
**Task Status**: `complete_pass`  

---

## 1. Frozen Scientific Comparison Contract for Adaptive Mode-II Runs

Grounding on the censoring-corrected uniform grid refinement evidence ($H_0$, $H_1$, $H_2$), the scientific comparison contract for adaptive production runs ($\text{MM}$ and $\text{PK5}$) is officially frozen:

### Explicit Classifications:
```text
pre_peak_force_response_convergence       = PASS
damage_initiation_mesh_consistency        = PASS
initial_stiffness_mesh_consistency        = PASS

H1_minimum_prepeak_reference              = SUPPORTED

matched_state_crack_path_convergence      = FAIL (Hausdorff 0.005443 mm > 0.00375 mm)
global_peak_force_convergence             = UNRESOLVED_CENSORED
full_postpeak_uniform_convergence         = UNRESOLVED
energy_convergence                        = UNRESOLVED

complete_fracture_reference_resolution    = UNRESOLVED
complete_uniform_fracture_reference       = NONE
adaptive_remeshing_motivation             = STRONGLY_SUPPORTED
```

### Uniform Reference Roles:
- **$H_0$ Baseline Reference** (`1386372.mmaster02`, $N_{\text{phys}}=3930$): Coarse historical/corrected baseline ($h/l_0 = 2.0$).
- **$H_1$ Refined Reference** (`1386447.mmaster02`, $N_{\text{phys}}=12064$): Supported minimum uniform comparison mesh for initial elastic stiffness ($45.9035\,\text{kN/mm}$), pre-peak $RF_1\text{--}u_1$ response, damage initiation ($7.75\,\mu\text{m}$), and common-window global response ($0 \le u_1 \le 0.009250\,\text{mm}$).
- **$H_2$ Ultra-Fine Diagnostic** (`1386448.mmaster02`, $N_{\text{phys}}=33852$): Fine uniform spatial-resolution diagnostic ($h/l_0 = 0.5$) for $H_1/H_2$ refinement sensitivity and matched-state crack geometry.
- **Negative Rules**: $H_2$ is NOT a completed post-peak reference; $H_1$ is NOT a converged fracture/crack-path reference.

### Two-Domain Scientific Comparison Protocol:
1. **Domain A (Common Pre-Peak / Uniform Domain, $0 \le u_1 \le 0.009250\,\text{mm}$)**:
   - $RF_1\text{--}u_1$ normalized $L_2$ error versus $H_1$ (Gate: $\le 2.0\%$)
   - Relative work/area difference versus $H_1$
   - Initial elastic stiffness $K_0$ regression ($0 < u_1 \le 2\,\mu\text{m}$)
   - Damage initiation threshold $u_1(d \ge 0.5) \approx 7.75\,\mu\text{m}$
   - Matched-state crack path and Hausdorff distance at $u_1 = 0.009250\,\text{mm}$
2. **Domain B (Post-$0.009250\,\text{mm}$ Adaptive Domain, $0.009250 < u_1 \le 0.0100\,\text{mm}$)**:
   - Adaptive-run continuation only (no completed uniform reference exists).
   - Evaluated based on internal adaptive convergence ($\text{MM}$ vs $\text{PK5}$), physical consistency, energy balance, and crack-path stability. No comparison against fabricated/extrapolated uniform curves.

### Adaptive Candidates:
- **$\text{MM}$ (`F43REM4_MM`)**: 2,206 physical elements, `MINIMUM_MAXIMUM` sizing ($[1.0\%, 5.0\%]$ error), local $h/l_0 \in [0.30, 2.00]$. Role: Stronger adaptive localization / lowest global cost.
- **$\text{PK5}$ (`F43REM4_PK5`)**: 4,894 physical elements, `UNIFORM_ERROR` sizing ($5.0\%$ error), local $h/l_0 \in [0.45, 2.00]$. Role: Higher crack-corridor resolution / intermediate cost.
- **Output Sufficiency**: Both $\text{MM}$ and $\text{PK5}$ pass output variable audit (`RP U1, RF1`, `SDV14, 15, 16`, `EVOL`, `ALLAE..ETOTAL`, solver timing).

### Primary Cost Baselines:
- $H_0$ CPU: $2,000\,\text{s}$ (Walltime: $2,004\,\text{s}$)
- $H_1$ CPU: $5,434\,\text{s}$ (Walltime: $5,453\,\text{s}$, $2.72\times H_0$)
- $H_2$ CPU: $14,455\,\text{s}$ (Walltime: $14,501\,\text{s}$, $7.23\times H_0$, $2.66\times H_1$)

---

## 2. Governance and Authority Boundary

- `authorization_ready_for_adaptive_production`: `false`
- `direct_human_authorization_message_found`: `false`
- `execution_authorized`: `false`
- `submission_approved`: `false`
- `maximum_jobs_now`: `0`
- `remaining_authorized_submissions`: `0`
- `running_jobs_final`: `0`
- `queued_jobs_final`: `0`
- `qsub_called`: `false`
- `HPC_submissions`: `0`
