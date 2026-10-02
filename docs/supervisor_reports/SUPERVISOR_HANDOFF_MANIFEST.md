# Mode-I Supervisor Handoff Deliverable Manifest

**Document Identifier**: `docs/supervisor_reports/SUPERVISOR_HANDOFF_MANIFEST.md`  
**Date**: September 10, 2026  
**Author**: Pruthviraja Reddy Vandavagali (Matriculation No. 68865)  
**Supervisors**: Prof. Dipl.-Ing. Björn Kiefer, Ph.D., and Dr.-Ing. Stephan Roth  
**Institution**: Institute of Mechanics and Fluid Dynamics (IMFD), TU Bergakademie Freiberg  
**Overall Package Status**: `MODE1_GATES0_TO_6_SUPERVISOR_HANDOFF_PACKAGE_VERIFIED`  

---

## 1. Master Supervisor Deliverables & Evidence Classification

| Relative Path | Primary Purpose | Full SHA-256 Checksum | Evidence Level | Required for Reproduction? | Generated From |
| :--- | :--- | :--- | :--- | :---: | :--- |
| `docs/supervisor_reports/SUPERVISOR_EXECUTIVE_BRIEF_MODE1.md` | 1-Page High-Level Executive Summary for Supervisors | `905e94b150ce124806a8ab1b764bf3507cf2700e57f208447ce730a91be527fa` | Executive Synthesis | Yes (Primary Brief) | Synthesis of Gates 0–6 |
| `docs/supervisor_reports/CONDENSED_MODE1_BENCHMARK_SUPERVISOR_REPORT.md` | Condensed 5-Chapter Scientific Benchmark Report | `9ed55d5221218f5c10a65eabdc1ff38e296c6be59f798e6fedf59e45a4a03426` | Formal Benchmark Report | Yes (Primary Document) | Benchmark Physics & Extractions |
| `docs/supervisor_reports/GATE6_FIELD_EXTRACTION_PROVENANCE_AUDIT.md` | Raw Field Extraction Provenance, SDV Lineage & Checkpoints | `b78e390c2130e6e788ee591f868d407eb42323e6fcf645feaeefd478cf3f2257` | Forensic Field Audit | Yes (Audit Dossier) | ODB Lineage & Fortran Traces |
| `docs/supervisor_reports/GATE6_REFERENCE_REPRODUCTION_REPORT.md` | Standalone Gate-6 Scientific Qualification Report | `cbc3e1bffa889078ff68036a02da39e6649b0f2c6b17d4b6298f69d3dc62c511` | Gate-Level Evidence | Yes (Scientific Dossier) | Full Solver Evaluations |
| `docs/supervisor_reports/MODE1_SUPERVISOR_MASTER_GATES_0_TO_6_SYNTHESIS.md` | Master Synthesis of Gates 0 through 6 | `948f208ea271907863dcfe6cacc19bfc8e39003355effd94c9011e1c54c2a3eb` | Master Gate Synthesis | Yes (Complete Dossier) | Gates 0–6 Evidence Base |
| `docs/supervisor_reports/gate6_full_fu_comparison.png` | Figure 1: Full Load-Displacement Curves with Peak Markers | `f8ceb2315ba243087936414aa8d7afab357d21e54bbb05d5312fb01da2259dce` | Publication Asset | Yes (Figure 1) | Canonical F–u CSVs |
| `docs/supervisor_reports/gate6_error_summary_metrics.png` | Figure 2: Relative Errors & Normalized L2 Trajectory Error Norms | `ac124de0a7802465013b57fb5b54ef9ccbb2b29d728318b182651ff7d1a2bb48` | Publication Asset | Yes (Figure 2) | Canonical F–u CSVs |
| `docs/supervisor_reports/gate6_computational_cost_comparison.png` | Figure 3: Walltime (Hours) vs Finite Element Count Scaling | `b3d4a14ecde7b48aceadd8edafb3fdc17e4b4196626160eb3be1db729364b50e` | Publication Asset | Yes (Figure 3) | Solver STA & Timing Logs |
| `docs/supervisor_reports/gate6_interval_disaggregated_curve_audit.png` | Figure 4: 3-Panel Trajectory, Force Discrepancy & Accumulation | `5a5c59f0fe84ae1ccc3e7ca82f3bc059b08f5e4cc7a40dedb99943288e7d76d0` | Publication Asset | Yes (Figure 4) | Canonical F–u CSVs |
| `docs/supervisor_reports/gate6_matched_phase_field_contours.png` | Figure 5: 4x3 Matched Displacement Phase-Field Damage Contours | `8645f507bff11fdac2c25de8e0b8d964eac4dddc880a86b5ec351b95e3a3326b` | Publication Asset | Yes (Figure 5) | `gate6_matched_phase_field_data.json` |
| `docs/supervisor_reports/gate6_ligament_damage_profiles.png` | Figure 6: Quantitative Ligament Damage Profiles d(x, y=0.500) | `6ef255bad729783f18a376f2a1a61f5e33a791dc8538d84404d2b210dcbb0db0` | Publication Asset | Yes (Figure 6) | `gate6_ligament_damage_profiles.csv` |
| `docs/supervisor_reports/gate6_master_fracture_comparison_metrics.json`| Authoritative Reconciled Master Fracture Comparison Data | `dc698bb25964d709a9b29d49ee746cdfe17eb6d56f488b7f5497239eb4edc117` | Machine-Readable Truth | Yes (Data Registry) | `analyze_gate6_master_fracture.py` |
| `docs/supervisor_reports/gate6_matched_phase_field_data.json` | Extracted Checkpoint Field Data & Spatial Statistics | `981a03fd49e8dfe858fab271a8deec347bc2ba597372f21905e25b9aa7a604a1` | Machine-Readable Truth | Yes (Data Registry) | `extract_gate6_field_profiles.py` |
| `docs/supervisor_reports/gate6_ligament_damage_profiles.csv` | 151-Point Ligament Damage Profile CSV Dataset | `235ef809ba6b20445b089452c331df6c376f92dcc5dd0fc2b1329139f9c3f12d` | Machine-Readable Truth | Yes (Data Registry) | `export_field_and_ridge_data.py` |
| `docs/supervisor_reports/gate6_crack_path_2d_ridge_audit.csv` | 2D Transverse Ridge Extraction Candidate Evaluation CSV | `c3d656221cfdcbc43673959a875ca40c87d2de8c4e9877cd17a17a87ce46cfa3` | Machine-Readable Truth | Yes (Data Registry) | `export_field_and_ridge_data.py` |
| `docs/supervisor_reports/gate6_crack_path_2d_ridge_audit.json` | 2D Transverse Ridge Extraction Candidate Evaluation JSON | `a61bbf49494e1f2b156c3092bf7f9d7d4f0b8adf245a784cba4620e0aed3ad65` | Machine-Readable Truth | Yes (Data Registry) | `export_field_and_ridge_data.py` |
| `results/pandey_kumar_mode1/master_fracture_curves/curve_standard_1398090.csv` | Canonical Fixed-Mesh Reference F–u Curve (7,000 Points) | `780d05d39532e778802cdd8503cdd0df25568e412c3d4a51c50f4e001febede6` | Baseline Data Truth | Yes (Core Baseline) | Job `1398090.mmaster02` DAT File |
| `results/pandey_kumar_mode1/master_fracture_curves/curve_harmonized_1401091.csv` | Harmonized Top-Roller Reference F–u Curve (7,000 Points) | `dd617eca6a7aedbf19265721dbc75a1bdbd8deb343c76a4f7c58d60c8112524b` | Comparative Data Truth | Yes (BVP Sensitivity) | Job `1401091.mmaster02` DAT File |
| `results/pandey_kumar_mode1/master_fracture_curves/curve_adaptive_1399632.csv` | Nominal 1% Adaptive F–u Curve (7,000 Points) | `ec816efa15f0f4b7548d0efbc5cf84d4d69b4ad29aaf386253f7eb0601e1600b` | Adaptive Run Truth | Yes (1% Failure Case) | Job `1399632.mmaster02` DAT File |
| `results/pandey_kumar_mode1/master_fracture_curves/curve_adaptive_1400395_2pct.csv` | Empirical 2% Adaptive F–u Curve (7,028 Points) | `f0e5ac9229b38eb94c3e8fe08729108d0a2a748a4bb21a9e8e162ad70f6899ce` | Adaptive Run Truth | Yes (2% Partial Match) | Job `1400395.mmaster02` DAT File |
| `results/pandey_kumar_mode1/master_fracture_curves/curve_adaptive_1400396_5pct.csv` | Empirical 5% Adaptive F–u Curve (7,000 Points) | `b62dd0ddcc387567ddd17bede9e98471f2aaf9b9e17bc5c592d138ed1cda013e` | Adaptive Run Truth | Yes (5% Coarse Case) | Job `1400396.mmaster02` DAT File |
| `ModeI_Supervisor_Report_Reproduction_Package/commands.txt` | Complete End-to-End Command & Workflow Instructions | `1f0b7371a58738337cc71d0480278d7693eb6f11e7e9f237946d33424a506e09` | Operational Instruction | Yes (Workflow Guide) | Real HPC & Local Shell Syntax |
| `ModeI_Supervisor_Report_Reproduction_Package/MANIFEST.sha256` | Complete 114-File Package Cryptographic Checksum Manifest | `1b47d4d2fec5dabbd4c295bc4959c7fb9ad84356edf42f104e48db0c2f134424` | Cryptographic Proof | Yes (Package Integrity) | `generate_reproduction_manifest.py` |
| `CURRENT_STATE.md` | Authoritative Project Coordination State | `cee76c055d50dbb1ee405dfec9d6e61bafcb37f0cf53366091045806692dde58` | Project Coordination | Yes (Root Ledger) | Active Turn Sync |
| `ACTIVE_TASK.json` | Machine-Readable Active Task Ledger | `7d9b70bdf6b163ff26a953f380e6bffb11c98990223a046aa30a0adb46748bd9` | Project Coordination | Yes (Root Ledger) | Active Turn Sync |

---

## 2. Package Size Verification & Top 10 Largest Files

- **Total Reproduction Package Size**: **$50,228,595\,\text{bytes}$ ($47.90\,\text{MB}$ across 115 files)**.
- **Large ODB Verification**: **CONFIRMED 0 MULTI-GB ODB FILES INCLUDED**. (Raw multi-gigabyte ODB files remain safely archived on TUBAF HPC; reproduction is fully enabled via compact `.inp`, `.for`, `.py`, and canonical `.csv`/`.json` outputs).

### Top 10 Largest Files in the Package:
1. `images/figure_mesh_spatial_density_maps_cases80_81_61.png` — $7.01\,\text{MB}$ (`9f79fa4deeff...`)
2. `04_state_transfer_and_restart/checkpoint_files/D3A3_STATE_BY_FRAME.csv` — $5.39\,\text{MB}$ (`cabf4937ead1...`)
3. `03_miseseri_native_refinement/refined_mesh/PK_MODE1_PROPOSED_PFM_PHYS_1PCT_71320.inp` — $4.97\,\text{MB}$ (`e463a0dd25ec...`)
4. `04_state_transfer_and_restart/checkpoint_files/D3A3_PHASE_NODE_RECOVERY_BY_FRAME.csv` — $4.68\,\text{MB}$ (`074378720541...`)
5. `04_state_transfer_and_restart/checkpoint_files/D3_TRANSFERRED_IP_H.csv` — $4.63\,\text{MB}$ (`a67bf29ce900...`)
6. `images/figure_preanalysis_stress_error_comparison_cases80_81.png` — $2.15\,\text{MB}$ (`cd68cd56a59d...`)
7. `02_pandey_kumar_fixed_mesh_modeI/input/PK_MODE1_STANDARD_PFM.inp` — $1.94\,\text{MB}$ (`c1773707d2f1...`)
8. `04_state_transfer_and_restart/restart_inputs/D3A3_R4_compatible_hold.inp` — $1.86\,\text{MB}$ (`59ef7003560f...`)
9. `04_state_transfer_and_restart/restart_inputs/D3A3_R3_compatible_hold.inp` — $1.70\,\text{MB}$ (`fb27c3a18c1d...`)
10. `01_phase_field_source_verification/improved_molnar_modeI/H1_fullgen.inp` — $1.42\,\text{MB}$ (`426ca363d557...`)
