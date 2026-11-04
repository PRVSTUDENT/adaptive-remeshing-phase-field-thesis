# Package 171-R8 Authentic Telemetry Replay: 18 Stage 2 Rollback Events

**Job ID**: `1420188.mmaster02`  
**Predecessor Task**: `F1609-PACKAGE171-R8-C6-EXECUTION-QUALIFICATION`  
**Relaxation Scaling Factor**: $\omega_2 / \omega_1 = 0.85 / 0.50 = 1.70$  

| Outer | $|A_k|$ | $|\Delta A_k|$ | $\Delta A^+$ | $\Delta d_{\text{cand}}^{(R8)}$ | $\Delta d_{\text{prev}}^{(R8)}$ | Ratio $R_8$ | R8 Decision | $\|\delta d_{\text{cand}}\|_\infty$ | $\|\delta d_{\text{prev}}\|_\infty$ | Ratio $R_9$ | R9 Decision |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| 89 | 225 | 8 | 0 | 1.5690e-02 | 9.3147e-03 | 1.6844 | `ROLLBACK_REJECTED` | 1.8459e-02 | 1.8629e-02 | 0.9908 | **`ADMITTED_STAGE2`** |
| 92 | 206 | 5 | 0 | 1.5235e-02 | 9.0394e-03 | 1.6854 | `ROLLBACK_REJECTED` | 1.7924e-02 | 1.8079e-02 | 0.9914 | **`ADMITTED_STAGE2`** |
| 95 | 188 | 5 | 0 | 1.4805e-02 | 8.7822e-03 | 1.6858 | `ROLLBACK_REJECTED` | 1.7418e-02 | 1.7564e-02 | 0.9916 | **`ADMITTED_STAGE2`** |
| 98 | 170 | 7 | 0 | 1.4399e-02 | 8.5376e-03 | 1.6865 | `ROLLBACK_REJECTED` | 1.6940e-02 | 1.7075e-02 | 0.9921 | **`ADMITTED_STAGE2`** |
| 101 | 155 | 5 | 0 | 1.4003e-02 | 8.3084e-03 | 1.6854 | `ROLLBACK_REJECTED` | 1.6474e-02 | 1.6617e-02 | 0.9914 | **`ADMITTED_STAGE2`** |
| 104 | 139 | 7 | 0 | 1.3623e-02 | 8.0964e-03 | 1.6826 | `ROLLBACK_REJECTED` | 1.6027e-02 | 1.6193e-02 | 0.9898 | **`ADMITTED_STAGE2`** |
| 107 | 126 | 4 | 0 | 1.3287e-02 | 7.8843e-03 | 1.6852 | `ROLLBACK_REJECTED` | 1.5632e-02 | 1.5769e-02 | 0.9913 | **`ADMITTED_STAGE2`** |
| 110 | 112 | 4 | 0 | 1.2926e-02 | 7.6566e-03 | 1.6882 | `ROLLBACK_REJECTED` | 1.5207e-02 | 1.5313e-02 | 0.9931 | **`ADMITTED_STAGE2`** |
| 113 | 100 | 4 | 0 | 1.2592e-02 | 7.4794e-03 | 1.6836 | `ROLLBACK_REJECTED` | 1.4814e-02 | 1.4959e-02 | 0.9903 | **`ADMITTED_STAGE2`** |
| 116 | 86 | 5 | 0 | 1.2268e-02 | 7.2688e-03 | 1.6878 | `ROLLBACK_REJECTED` | 1.4433e-02 | 1.4538e-02 | 0.9928 | **`ADMITTED_STAGE2`** |
| 119 | 74 | 3 | 0 | 1.1945e-02 | 7.0953e-03 | 1.6835 | `ROLLBACK_REJECTED` | 1.4053e-02 | 1.4191e-02 | 0.9903 | **`ADMITTED_STAGE2`** |
| 122 | 60 | 5 | 0 | 1.1632e-02 | 6.8890e-03 | 1.6885 | `ROLLBACK_REJECTED` | 1.3685e-02 | 1.3778e-02 | 0.9932 | **`ADMITTED_STAGE2`** |
| 125 | 50 | 3 | 0 | 1.1347e-02 | 6.7353e-03 | 1.6847 | `ROLLBACK_REJECTED` | 1.3349e-02 | 1.3471e-02 | 0.9910 | **`ADMITTED_STAGE2`** |
| 128 | 42 | 3 | 0 | 1.1003e-02 | 6.5387e-03 | 1.6827 | `ROLLBACK_REJECTED` | 1.2945e-02 | 1.3077e-02 | 0.9899 | **`ADMITTED_STAGE2`** |
| 131 | 39 | 0 | 0 | 1.0773e-02 | 6.3858e-03 | 1.6870 | `ROLLBACK_REJECTED` | 1.2674e-02 | 1.2772e-02 | 0.9924 | **`ADMITTED_STAGE2`** |
| 134 | 37 | 0 | 0 | 1.0486e-02 | 6.2287e-03 | 1.6835 | `ROLLBACK_REJECTED` | 1.2336e-02 | 1.2457e-02 | 0.9903 | **`ADMITTED_STAGE2`** |
| 137 | 35 | 0 | 0 | 1.0179e-02 | 6.0352e-03 | 1.6866 | `ROLLBACK_REJECTED` | 1.1975e-02 | 1.2070e-02 | 0.9921 | **`ADMITTED_STAGE2`** |
| 140 | 35 | 0 | 0 | 9.9669e-03 | 5.9071e-03 | 1.6873 | `ROLLBACK_REJECTED` | 1.1726e-02 | 1.1814e-02 | 0.9925 | **`ADMITTED_STAGE2`** |

### Key Findings:
1. **18 of 18 attempts were falsely rejected in R8**: The ratio across the transition was inflated by the relaxation step multiplier $\approx 1.70\times$, resulting in ratios $1.682 - 1.688 > 1.50$.
2. **100% of transitions were contracting in the unrelaxed solver norm**: In all 18 cases, $\frac{\|\delta d_{\text{cand}}\|_\infty}{\|\delta d_{\text{prev}}\|_\infty} \in [0.9898, 0.9932] < 1.00$.
3. **Zero false-positive rollbacks in R9**: Evaluating contraction on the intrinsic unrelaxed solver step admits Stage 2 in all 18 instances while preserving the 5% growth ($1.05$) and 50% divergence ($1.50$) safeguards against genuine divergence.
