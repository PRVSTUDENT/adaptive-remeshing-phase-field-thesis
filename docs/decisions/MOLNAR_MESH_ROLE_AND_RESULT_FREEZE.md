# Mesh Role and Result Freeze — Molnar lc015 H0 / H1 / H2-PUB

Status: `frozen`  
Freeze date: 2026-07-21  
Supervisor decisions: **1A** and **2B**  
Authority: `docs/decisions/MOLNAR_GATE_A3_SUPERVISOR_DECISION_1A_2B.md`

Do not overwrite frozen solver ODBs, RF–U CSVs, generation manifests, or scientific-input revisions listed here. New work creates new paths.

---

## Mesh roles (frozen)

| Mesh | Role after 1A | Local \(h\) | Physical elements | Layered elements |
|---|---|---:|---:|---:|
| H0 | Development / testing / debug | ≈ 0.00494 mm | 3930 | 11790 |
| H1 | Production / thesis / report; Stage C primary comparison reference | 0.0025 mm | 12064 | 36192 |
| H2-PUB | Fine RF–U validation reference only | 0.001 mm | 33852 | 101556 |

---

## Solver and postprocess jobs (frozen)

| Case | Solver job | CAE RF–U package | Scientific-input revision |
|---|---|---|---|
| H0 | `1376154.mmaster02` | `1376236.mmaster02` | `58d7e3102d76fe0e70e6729457e2c7e90ad131bb` |
| H1 | `1376185.mmaster02` | `1376236.mmaster02` | `58d7e3102d76fe0e70e6729457e2c7e90ad131bb` (scientific inputs); recovery infra `26b7b70832b2e1ae74c54abb7599cbe553aa1bad` |
| H2-PUB | `1376186.mmaster02` | `1376236.mmaster02` | same as H1 |

Analysis commit for formal RF–U decision: `db4c1fadfb3a4f7b33b6b653c261e6da90036c48`.

---

## Generated deck / source hashes (study family)

From `models/generated/molnar_gravouil_2017/h_convergence_lc015/*/input_hashes.sha256`:

| Case | Input | SHA-256 |
|---|---|---|
| H0 | `SingleNotch.inp` | `82c80c03c1b0b25131e9e0352502fb393bd593f9f07035c311f164ee9311f92e` |
| H0 | `SingleNotch.for` | `516e5ce9a405c30e9d4b45f919f8c22e39cd36bcce102ca065837b81a1405088` |
| H1 | `H1_h0025.inp` | `90a305ef29714a6ee795e6b2fd9ef53856141f2ef66928665b5640422d12c35b` |
| H1 | `H1_h0025.for` | `745db8fcfb612895e0289f4533c90d204cc9b2ade3678a035614feeb308b5ead` |
| H2-PUB | `H2_pub_h0010.inp` | `f32d4954d0770935d223ce5625370142b9c40b97aeb65974eb5b71dc20754947` |
| H2-PUB | `H2_pub_h0010.for` | `49c9054ab5faec9e069e0a9149af5058e6f1e11ab164c2a0e318f60282309b37` |

## Preserved original supplementary hashes (immutable baseline)

From `models/baseline_original/molnar_gravouil_2017/README.md`:

| File | SHA-256 |
|---|---|
| `02_Single_Notch_Tension/SingleNotch.inp` | `89ce3f32e396b0e484be6753a272dd6bbb2a2f9daff426d6a57419f57d665b72` |
| `02_Single_Notch_Tension/SingleNotch.for` | `18944e5bb2a3b7973fd0d4bff03f8e078eef667965343d8a29156d093f53f5f1` |

## RF–U CSV hashes (CAE job 1376236 package)

From `results/processed/molnar_lc015_h_convergence/source_hashes.sha256`:

| Case | SHA-256 |
|---|---|
| H0 RF2–U2 | `a0196294625df62c1fbb247ac9d6002617d86f0859d1cdc673e966df8294b4f5` |
| H1 RF2–U2 | `48f2358c1672b5d2a9be22209a43b781ee7ef022b8aeec14f723a6f92545149c` |
| H2-PUB RF2–U2 | `148bfc09d016491ed819f569c30071e53a6aedd381c69b26eff94e257c16dd8d` |
| Fig.7 lc015 corrected origin | `915aad72541f123088dd529c9b6bf411c4e6e931513690e0132e2dac087f0096` |

## Peak response freeze (for Stage C comparison)

| Case | peak RF2 [kN] | U_peak [mm] | walltime [s] | peak memory [kB] |
|---|---:|---:|---:|---:|
| H0 | 0.727608 | 0.00610 | 989 | 691652 |
| H1 | 0.699604 | 0.00580 | 2786 | 928364 |
| H2-PUB | 0.696336 | 0.00580 | 7958 | 1802776 |

Source: `runs/hpc/molnar_lc015_h_convergence/comparison/H_CONVERGENCE_DECISION.json`.

---

## Freeze rules

1. Do not resubmit H0/H1/H2-PUB solvers for the purpose of replacing frozen RF–U evidence.
2. Do not edit CSVs under the CAE `1376236` postprocessing tree.
3. Do not regenerate H1/H2-PUB decks over the existing generation paths if that would change hashes; create a new generation root for new generators.
4. New MISESERI-related decks live under new paths (e.g. `models/generated/.../miseseri_*`).
5. Contour export recovery on existing ODBs, if ever authorized, is a separate CAE-only task and does not unfreeze RF–U numbers.
