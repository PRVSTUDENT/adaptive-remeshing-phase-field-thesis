# Molnar lc015 h-convergence STUDY MANIFEST

Status: `submitted_serial_dependency_chain`

Study family: `molnar_single_notch_lc015_h_convergence`

## Authorization

- Supervisor approved controlled h-convergence subset only
- Exactly three serial jobs submitted once: H0, H1, H2-PUB
- No length-scale, increment-sensitivity, MISESERI, remeshing, multi-CPU, GPU

## Submission

| Field | Value |
|---|---|
| Submission time | `20260720T134402+0200` |
| Revision | `58d7e3102d76fe0e70e6729457e2c7e90ad131bb` |
| H0 job | `1376154.mmaster02` |
| H1 job | `1376155.mmaster02` |
| H2-PUB job | `1376156.mmaster02` |
| Dependency | H0 -> H1 -> H2 afterok |
| Queue (scheduled) | `normal_imfdfkmq` via `entry_imfdfkmq` |
| Mail_Users | `pr21vyci@mailserver.tu-freiberg.de` |
| Mail_Points | `abe` |
| Prestage | `/scratch/pr21vyci/adaptive-remeshing/prestage/molnar_lc015_h_convergence_20260720T134402+0200_58d7e3102d76` |

## Cases

| Case | Folder | Physical elements | Layered | Target h [mm] | Measured corridor h median [mm] | h/lc median | Static class | Job |
|---|---|---:|---:|---:|---:|---:|---|---|
| H0 | H0_exact | 3930 | 11790 | 0.005 | 0.0049439 | 0.32959 | exact_author_inputs_verified | 1376154.mmaster02 |
| H1 | H1_h0025 | 12064 | 36192 | 0.0025 | 0.0025 | 0.16667 | h_convergence_static_validation_pass | 1376155.mmaster02 |
| H2-PUB | H2_pub_h0010 | 33852 | 101556 | 0.001 | 0.001 | 0.06667 | h_convergence_static_validation_pass + publication_resolution_verified | 1376156.mmaster02 |

## Scientific fixed settings

- lc = 0.015 mm
- E = 210, nu = 0.3, Gc = 2.7e-3, thickness = 1
- residual k = 1e-7, UMAT residual 1e-11
- exact supplementary Amp-1/Amp-2 and Step-1/Step-2

## Reference

- Fig. 7 lc=0.015 approximate digitized publication reference
- path: `references/derived/molnar_gravouil_2017/single_notch/fig7_lc015_corrected_origin/`
- classification: `approximate_digitized_publication_reference`

Scientific convergence remains pending after job completion.
