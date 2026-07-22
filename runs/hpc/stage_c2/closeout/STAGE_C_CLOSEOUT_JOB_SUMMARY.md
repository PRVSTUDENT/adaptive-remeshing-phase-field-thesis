# Stage C closeout job summary

Recorded from PBS history on 2026-07-22.

| Job | Purpose | PBS result | Key conclusion |
| --- | --- | --- | --- |
| 1376593.mmaster02 | Telegram smoke | F, Exit_status 0 | Notification smoke completed. |
| 1376594.mmaster02 | T1 H1 closeout | F, Exit_status 0 | Four-thread H1 baseline qualified for fair cost comparison. |
| 1376595.mmaster02 | T2 C2F-v3 repeat | F, Exit_status 0 | Repeatability supported; RF--U metrics and final SDV15 field match frozen C2F-v3. |
| 1376596.mmaster02 | T3 SDV extraction | F, Exit_status 0 | Matched-state SDV15 extraction completed for H1, C2F-v3, and C2F-v3 repeat. |
| 1376597.mmaster02 | T4 crack metrics | F, Exit_status 0 | Crack-path repeatability supported; H1 vs refined-v3 deviation detected. |
| 1376598.mmaster02 | T5 H0 automation smoke | F, Exit_status 12 | Completed as failed guard evidence; not used as a scientific result. |

## Important result files

- `runs/hpc/stage_c2/h1_threads4_closeout/FAIR_COST_COMPARISON.md`
- `runs/hpc/stage_c2/h1_threads4_closeout/FAIR_COST_COMPARISON.json`
- `runs/hpc/stage_c2/repeatability/c2f_v3_repeat/V3_REPEAT_COMPARISON.md`
- `runs/hpc/stage_c2/repeatability/c2f_v3_repeat/V3_REPEAT_STATUS.json`
- `runs/hpc/stage_c2/crack_path_quantitative/CRACK_PATH_QUANTITATIVE_REPORT.md`
- `runs/hpc/stage_c2/crack_path_quantitative/CRACK_PATH_METRICS.csv`
- `runs/hpc/stage_c2/crack_path_quantitative/H1_VS_REFINED_V3_CRACK_PATH.json`
- `runs/hpc/stage_c2/crack_path_quantitative/CRACK_PATH_REPEATABILITY.json`
- `results/figures/stage_c_final/01_rf_u_h0_h1_h2_refined_v3.png`
- `results/figures/stage_c_final/02_rf_u_h1_vs_refined_v3_prepeak.png`
- `results/figures/stage_c_final/03_rf_u_h1_vs_refined_v3_postpeak.png`

