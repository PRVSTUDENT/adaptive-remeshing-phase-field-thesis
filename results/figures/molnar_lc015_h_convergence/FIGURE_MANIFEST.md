# Figure manifest

- `01_rf_u_h0_h1_h2.png`: H0/H1/H2 RF2-U2; lc=0.015; CAE job 1376236
- `02_rf_u_with_fig7_lc015.png`: With approximate digitized publication reference
- `03_rf_u_peak_zoom.png`: Zoom around peak load
- `04_pairwise_force_diff_vs_u.png`: H0-H1 and H1-H2 force differences
- `05_peak_rf2_vs_h.png`: Peak RF2 vs measured h
- `06_upeak_vs_h.png`: U2 at peak vs measured h
- `07_tangent_vs_h.png`: Initial tangent vs h
- `08_curve_nrmse_vs_h.png`: Full/pre/post successive NRMSE
- `09_walltime_vs_elements.png`: Serial walltime; log-log slope alpha≈0.968
- `10_memory_vs_elements.png`: Serial peak memory

Script: `scripts/postprocessing/analyze_molnar_lc015_h_convergence.py`
lc=0.015 mm; cases H0/H1/H2-PUB; CAE job 1376236; units U2 mm, RF2 kN.
Reference: approximate_digitized_publication_reference (not exact author data).
Interpolation: linear on common grid N=1001, U in [0,0.007].
