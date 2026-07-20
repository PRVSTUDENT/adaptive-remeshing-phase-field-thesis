# Molnar lc015 h-convergence STUDY MANIFEST

Status: prepared_not_submitted

Study family: molnar_single_notch_lc015_h_convergence

## Authorization

- Supervisor approved controlled h-convergence subset only
- Exactly three serial jobs: H0, H1, H2-PUB
- No length-scale, increment-sensitivity, MISESERI, remeshing, multi-CPU, GPU

## Cases

| Case | Folder | Physical elements | Layered | Target h [mm] | Measured corridor h median [mm] | h/lc median | Static class |
|---|---|---:|---:|---:|---:|---:|---|
| H0 | H0_exact | 3930 | 11790 | 0.005 | 0.004943904068987025 | 0.329593604599135 | exact_author_inputs_verified |
| H1 | H1_h0025 | 12064 | 36192 | 0.0025 | 0.0025000000000000022 | 0.16666666666666682 | h_convergence_static_validation_pass |
| H2-PUB | H2_pub_h0010 | 33852 | 101556 | 0.001 | 0.0010000000000000009 | 0.06666666666666674 | h_convergence_static_validation_pass + publication_resolution_verified |

## Scientific fixed settings

- lc = 0.015 mm
- E = 210, nu = 0.3, Gc = 2.7e-3, thickness = 1
- residual k = 1e-7, UMAT residual 1e-11
- exact supplementary Amp-1/Amp-2 and Step-1/Step-2

## Reference

- Fig. 7 lc=0.015 approximate digitized publication reference
- path: references/derived/molnar_gravouil_2017/single_notch/fig7_lc015_corrected_origin/
- classification: approximate_digitized_publication_reference

## Runnable

- H0: true
- H1: true
- H2-PUB: true

Scientific convergence: pending after job completion.
