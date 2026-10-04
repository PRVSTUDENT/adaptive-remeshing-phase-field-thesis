# Gate-6B Mode-I Stage 14U-U: Spatial Convergence Provenance Table

**Task ID**: `F1204-GATE6B-STAGE14UU-SPATIAL-CONVERGENCE-PROVENANCE-AUDIT-20261004`  
**Generated**: 2026-10-04T10:49:30.836Z  
**Governing Verdict**: `SPATIAL_CONVERGENCE_EVIDENCE_ALREADY_SUFFICIENT`

---

## 1. Master Discretization Provenance Inventory

| Case ID | Case Name | PBS Job ID | Input Deck & SHA-256 | Elements (Quad / Tri) | Corridor Share (5% Area) | $h_{\min}$ ($h/l_0$) | $K_0$ (kN/mm) | $F_{\max}$ (kN) | $u_{\text{peak}}$ (\mu m) | $E_{\text{frac}}$ (mJ) | Completion Status |
| :--- | :--- | :---: | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| **S1_REF15K** | S1 Fixed Coarse Reference | `1409734.mmaster02` | `PK_MODE1_REF15K_ENERGY.inp`<br>`EC560A4C2657...` | 15,192 (15,192 / 0) | 4,316 (**28.4%**) | 2.93 $\mu$m (0.387) | 137.946 | 0.7578 | 5.86 | 2.340 | `COMPLETED` |
| **S2_FIX32K** | S2 Fixed Medium Mesh | `1409866.mmaster02` | `PK_MODE1_FIX_H0020_ENERGY.inp`<br>`9A5C3BD7EA9A...` | 32,130 (32,130 / 0) | 12,500 (**38.9%**) | 2.00 $\mu$m (0.267) | 137.894 | 0.7412 | 5.71 | 2.339 | `TERMINATED_POST_FRACTURE_CUTBACK` |
| **S3_FIX42K** | S3 Fixed Fine Mesh | `1409867.mmaster02` | `PK_MODE1_FIX_H0015_ENERGY.inp`<br>`1500ECA50286...` | 41,912 (41,912 / 0) | 17,596 (**42.0%**) | 1.22 $\mu$m (0.200) | 137.858 | 0.7322 | 5.63 | 2.375 | `TERMINATED_POST_FRACTURE_CUTBACK` |
| **S4_FIX51K** | S4 Fixed Very Fine Mesh | `1406018.mmaster02` | `PK_M1_S4_H00125.inp`<br>`186358356F13...` | 51,408 (51,408 / 0) | 24,320 (**47.3%**) | 1.25 $\mu$m (0.167) | 137.837 | 0.7290 | 5.61 | 2.369 | `TERMINATED_POST_FRACTURE_CUTBACK` |
| **S5_FIX69K** | S5 Fixed Ultra Fine Mesh | `1406019.mmaster02` | `PK_M1_S5_H00100.inp`<br>`6A111A84F3DF...` | 69,384 (69,384 / 0) | 36,240 (**52.2%**) | 1.00 $\mu$m (0.133) | 137.823 | 0.7255 | 5.58 | 2.355 | `TERMINATED_POST_FRACTURE_CUTBACK` |
| **ADAPT_2PCT_PKG24** | Package 24 Adaptive 2% Variant | `1409846.mmaster02` | `PK_MODE1_ADAPT_2PCT_13K_ENERGY.inp`<br>`9113C5F609B8...` | 13,897 (13,506 / 391) | 1,718 (**12.4%**) | 0.87 $\mu$m (0.116) | 137.890 | 0.7441 | 5.75 | 2.290 | `COMPLETED` |
| **ADAPT_STAGE14_PKG25** | Package 25 Stage-14 Adaptive Candidate | `1409953.mmaster02 / 1409982.mmaster02` | `PK_MODE1_STAGE14_ADAPT_14K_FRACTURE.inp`<br>`26D873FB2E68...` | 14,483 (14,082 / 401) | 8,338 (**57.6%**) | 0.76 $\mu$m (0.101) | 137.910 | 0.7437 | 5.73 | 2.285 | `FRACTURE_COMPLETE__SOLVER_COMPLETION_RERUN_RUNNING` |

---

## 2. Detailed 17-Field Case Provenance Records

### Case 1: S1 Fixed Coarse Reference (`S1_REF15K`)
- **Scientific Purpose & Role**: FIXED_STRUCTURED_BIAS
- **PBS / Job ID**: `1409734.mmaster02` (`PK_MODE1_REF_7K_S1`, node `mnode097`, queue `normal_imfdfkmq`, mode `SERIAL_1CPU`)
- **Submission Timestamp**: `2026-10-02T07:49:40+02:00`
- **Input Deck Path & SHA-256**: `models/pandey_kumar_mode1/16_energy_qualification_reference_15k/PK_MODE1_REF15K_ENERGY.inp` (`EC560A4C265730647B43DAB125D166EBC57CAC285D574D38222A498A967535D9`, 19,41,217 bytes)
- **User Subroutine Path & SHA-256**: `models/pandey_kumar_mode1/16_energy_qualification_reference_15k/f42_mixed_uel.for` (`CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6`, 29,722 bytes)
- **UEL Property ABI Card**: `(l0, Gc, E, nu, k, N_phys) = (0.0075, 0.0027, 210.0, 0.3, 1.0e-7, 15192.0)`
- **Geometry & Zero-Gap Seam**: 1.0 mm x 1.0 mm square domain, a0 = 0.5 mm sharp horizontal seam along y = 0.500 mm with `ZERO_GAP_DUPLICATED_NODES`
- **Boundary Conditions**: Bottom y=0: u_y=0, pinned (0,0): u_x=0; Top y=1: prescribed u_y
- **Material Constants**: $E = 210\,\text{GPa}, \nu = 0.3, G_c = 0.0027\,\text{kN/mm}, l_0 = 0.0075\,\text{mm}, k = 10^{-7}$
- **Temporal Schedule**: Step 1: dt=5.0e-4, du=2.5 nm, INC=2000; Step 2: dt=2.0e-4, du=1.0 nm, INC=5000
- **Solver Controls**: `DEFAULT`
- **Energy Instrumentation**: `uel_energy_balance.csv (Unit 105, IP-consistent, Trap Int W_ext)`
- **Output Definitions**: RP RF/U every 1 inc; Companion SDV14/SDV1 frame intervals 100/50
- **Mesh Generation Method**: Structured rectilinear bias with graded refinement toward ligament
- **Element Topology**: Total Nodes = 15,522, Base Elements = 15,192 (Quads = 15,192, Tris = 0), Total INP Elements = 45,576
- **Crack Corridor Statistics ($x \in [0.5, 1.0]\,\text{mm}, y \in [0.45, 0.55]\,\text{mm}$, Area = $0.05\,\text{mm}^2 = 5.0\%$)**: Corridor Elements = 4,316 (**28.41%** of mesh), Corridor Quads = 4,316, Corridor Tris = 0, $h_{\min} = 2.93\,\mu\text{m}$ ($h/l_0 = 0.387$), Median $h = 2.94\,\mu\text{m}$
- **Completion Status & Terminal State**: Status = `COMPLETED`, Final Reached $u = 0.010000\,\text{mm}$, Final $F = 0.000232\,\text{kN}$, Load Drop = 99.97\%
- **Physical Quantities**:
  - $K_0 = 137.945520\,\text{kN/mm}$ ($R^2 = 0.99999960$, Intercept = 4.472368e-5\,\text{kN}$, $N = 400$)
  - $F_{\max} = 0.757778\,\text{kN}$ at $u_{\text{peak}} = 0.005857\,\text{mm}$
  - Broken-State $E_{\text{frac}} = 2.340220\,\text{mJ}$, $W_{\text{ext}} = 2.359329\,\text{mJ}$
  - Crack Trajectory $y = 0.5000\,\text{mm}$ ($|\Delta y|_{\max} = 0.000\,\text{mm}$), Localization Width $w_{90} = 19.65\,\mu\text{m}$ ($w_{90}/l_0 = 2.62$)
- **Primary Result Files**: `PK_M1_REF15K_ENERGY.dat`, `PK_M1_REF15K_ENERGY.sta`, `uel_energy_balance.csv`, `MODE1_REFERENCE_MATCHED_DISPLACEMENT_BUNDLE.json`

### Case 2: S2 Fixed Medium Mesh (`S2_FIX32K`)
- **Scientific Purpose & Role**: FIXED_STRUCTURED_BIAS
- **PBS / Job ID**: `1409866.mmaster02` (`PK_M1_S2_ENERGY`, node `mnode098`, queue `normal_imfdfkmq`, mode `SERIAL_1CPU`)
- **Submission Timestamp**: `2026-10-02T15:54:54+02:00`
- **Input Deck Path & SHA-256**: `models/pandey_kumar_mode1/12_fixed_convergence_h0020/PK_MODE1_FIX_H0020_ENERGY.inp` (`9A5C3BD7EA9AF8CD38715FAC9FB062B1590766B7A7CF3A800D2F8C9E95C3767F`, 41,08,873 bytes)
- **User Subroutine Path & SHA-256**: `models/pandey_kumar_mode1/12_fixed_convergence_h0020/f42_mixed_uel.for` (`CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6`, 29,722 bytes)
- **UEL Property ABI Card**: `(l0, Gc, E, nu, k, N_phys) = (0.0075, 0.0027, 210.0, 0.3, 1.0e-7, 32130.0)`
- **Geometry & Zero-Gap Seam**: 1.0 mm x 1.0 mm square domain, a0 = 0.5 mm sharp horizontal seam along y = 0.500 mm with `ZERO_GAP_DUPLICATED_NODES`
- **Boundary Conditions**: Bottom y=0: u_y=0, pinned (0,0): u_x=0; Top y=1: prescribed u_y
- **Material Constants**: $E = 210\,\text{GPa}, \nu = 0.3, G_c = 0.0027\,\text{kN/mm}, l_0 = 0.0075\,\text{mm}, k = 10^{-7}$
- **Temporal Schedule**: Step 1: dt=5.0e-4, du=2.5 nm, INC=2000; Step 2: dt=2.0e-4, du=1.0 nm, INC=5000
- **Solver Controls**: `DEFAULT`
- **Energy Instrumentation**: `uel_energy_balance.csv (Unit 105, IP-consistent, Trap Int W_ext)`
- **Output Definitions**: RP RF/U every 1 inc; Companion SDV14/SDV1 frame intervals 100/50
- **Mesh Generation Method**: Structured rectilinear bias with graded refinement toward ligament
- **Element Topology**: Total Nodes = 32,614, Base Elements = 32,130 (Quads = 32,130, Tris = 0), Total INP Elements = 96,390
- **Crack Corridor Statistics ($x \in [0.5, 1.0]\,\text{mm}, y \in [0.45, 0.55]\,\text{mm}$, Area = $0.05\,\text{mm}^2 = 5.0\%$)**: Corridor Elements = 12,500 (**38.90%** of mesh), Corridor Quads = 12,500, Corridor Tris = 0, $h_{\min} = 2.00\,\mu\text{m}$ ($h/l_0 = 0.267$), Median $h = 2.00\,\mu\text{m}$
- **Completion Status & Terminal State**: Status = `TERMINATED_POST_FRACTURE_CUTBACK`, Final Reached $u = 0.006816\,\text{mm}$, Final $F = 0.000243\,\text{kN}$, Load Drop = 99.97\%
- **Physical Quantities**:
  - $K_0 = 137.894136\,\text{kN/mm}$ ($R^2 = 0.99999980$, Intercept = 4.471000e-5\,\text{kN}$, $N = 400$)
  - $F_{\max} = 0.741194\,\text{kN}$ at $u_{\text{peak}} = 0.005711\,\text{mm}$
  - Broken-State $E_{\text{frac}} = 2.338860\,\text{mJ}$, $W_{\text{ext}} = 2.248010\,\text{mJ}$
  - Crack Trajectory $y = 0.5000\,\text{mm}$ ($|\Delta y|_{\max} = 0.000\,\text{mm}$), Localization Width $w_{90} = 19.30\,\mu\text{m}$ ($w_{90}/l_0 = 2.57$)
- **Primary Result Files**: `PK_M1_S2_ENERGY.dat`, `PK_M1_S2_ENERGY.sta`, `uel_energy_balance.csv`, `S2_h0020_32k_MECHANICAL_FU_AUDITED.csv`

### Case 3: S3 Fixed Fine Mesh (`S3_FIX42K`)
- **Scientific Purpose & Role**: FIXED_STRUCTURED_BIAS
- **PBS / Job ID**: `1409867.mmaster02` (`PK_M1_S3_ENERGY`, node `mnode098`, queue `normal_imfdfkmq`, mode `SERIAL_1CPU`)
- **Submission Timestamp**: `2026-10-02T15:54:54+02:00`
- **Input Deck Path & SHA-256**: `models/pandey_kumar_mode1/13_fixed_convergence_h0015/PK_MODE1_FIX_H0015_ENERGY.inp` (`1500ECA5028660045789AF04AD3112E26CA76BBF7BFAC6437A42008A4307408F`, 53,59,145 bytes)
- **User Subroutine Path & SHA-256**: `models/pandey_kumar_mode1/13_fixed_convergence_h0015/f42_mixed_uel.for` (`CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6`, 29,722 bytes)
- **UEL Property ABI Card**: `(l0, Gc, E, nu, k, N_phys) = (0.0075, 0.0027, 210.0, 0.3, 1.0e-7, 41912.0)`
- **Geometry & Zero-Gap Seam**: 1.0 mm x 1.0 mm square domain, a0 = 0.5 mm sharp horizontal seam along y = 0.500 mm with `ZERO_GAP_DUPLICATED_NODES`
- **Boundary Conditions**: Bottom y=0: u_y=0, pinned (0,0): u_x=0; Top y=1: prescribed u_y
- **Material Constants**: $E = 210\,\text{GPa}, \nu = 0.3, G_c = 0.0027\,\text{kN/mm}, l_0 = 0.0075\,\text{mm}, k = 10^{-7}$
- **Temporal Schedule**: Step 1: dt=5.0e-4, du=2.5 nm, INC=2000; Step 2: dt=2.0e-4, du=1.0 nm, INC=5000
- **Solver Controls**: `DEFAULT`
- **Energy Instrumentation**: `uel_energy_balance.csv (Unit 105, IP-consistent, Trap Int W_ext)`
- **Output Definitions**: RP RF/U every 1 inc; Companion SDV14/SDV1 frame intervals 100/50
- **Mesh Generation Method**: Structured rectilinear bias with graded refinement toward ligament
- **Element Topology**: Total Nodes = 42,492, Base Elements = 41,912 (Quads = 41,912, Tris = 0), Total INP Elements = 1,25,736
- **Crack Corridor Statistics ($x \in [0.5, 1.0]\,\text{mm}, y \in [0.45, 0.55]\,\text{mm}$, Area = $0.05\,\text{mm}^2 = 5.0\%$)**: Corridor Elements = 17,596 (**41.98%** of mesh), Corridor Quads = 17,596, Corridor Tris = 0, $h_{\min} = 1.22\,\mu\text{m}$ ($h/l_0 = 0.200$), Median $h = 1.47\,\mu\text{m}$
- **Completion Status & Terminal State**: Status = `TERMINATED_POST_FRACTURE_CUTBACK`, Final Reached $u = 0.007836\,\text{mm}$, Final $F = 0.000168\,\text{kN}$, Load Drop = 99.00\%
- **Physical Quantities**:
  - $K_0 = 137.857608\,\text{kN/mm}$ ($R^2 = 0.99999980$, Intercept = 4.469000e-5\,\text{kN}$, $N = 400$)
  - $F_{\max} = 0.732196\,\text{kN}$ at $u_{\text{peak}} = 0.005633\,\text{mm}$
  - Broken-State $E_{\text{frac}} = 2.375310\,\text{mJ}$, $W_{\text{ext}} = 2.190230\,\text{mJ}$
  - Crack Trajectory $y = 0.5000\,\text{mm}$ ($|\Delta y|_{\max} = 0.000\,\text{mm}$), Localization Width $w_{90} = 18.95\,\mu\text{m}$ ($w_{90}/l_0 = 2.53$)
- **Primary Result Files**: `PK_M1_S3_ENERGY.dat`, `PK_M1_S3_ENERGY.sta`, `uel_energy_balance.csv`, `S3_h0015_42k_MECHANICAL_FU_AUDITED.csv`, `MODE1_S3_AND_SPATIAL_CONVERGENCE_EVALUATION.json`

### Case 4: S4 Fixed Very Fine Mesh (`S4_FIX51K`)
- **Scientific Purpose & Role**: FIXED_STRUCTURED_BIAS
- **PBS / Job ID**: `1406018.mmaster02` (`PK_M1_S4_H00125`, node `mnode098`, queue `normal_imfdfkmq`, mode `SERIAL_1CPU`)
- **Submission Timestamp**: `2026-09-17T13:15:12+02:00`
- **Input Deck Path & SHA-256**: `models/pandey_kumar_mode1/batch_mode1_energy_convergence/S4_h00125_51k/PK_M1_S4_H00125.inp` (`186358356F131A986F3EA83F063ECF6D9018E6900F6FFBA0FBEFCAE221376E31`, 65,74,120 bytes)
- **User Subroutine Path & SHA-256**: `models/pandey_kumar_mode1/batch_mode1_energy_convergence/f42_mixed_uel.for` (`5CD0D2C015C9EAD91C99D7A744156CC86F5B5EA26473BBED7D6E5515FE30FA46`, 29,722 bytes)
- **UEL Property ABI Card**: `(l0, Gc, E, nu, k, N_phys) = (0.0075, 0.0027, 210.0, 0.3, 1.0e-7, 51408.0)`
- **Geometry & Zero-Gap Seam**: 1.0 mm x 1.0 mm square domain, a0 = 0.5 mm sharp horizontal seam along y = 0.500 mm with `ZERO_GAP_DUPLICATED_NODES`
- **Boundary Conditions**: Bottom y=0: u_y=0, pinned (0,0): u_x=0; Top y=1: prescribed u_y
- **Material Constants**: $E = 210\,\text{GPa}, \nu = 0.3, G_c = 0.0027\,\text{kN/mm}, l_0 = 0.0075\,\text{mm}, k = 10^{-7}$
- **Temporal Schedule**: Step 1: dt=5.0e-4, du=2.5 nm, INC=2000; Step 2: dt=2.0e-4, du=1.0 nm, INC=5000
- **Solver Controls**: `DEFAULT`
- **Energy Instrumentation**: `uel_energy_balance.csv (Unit 105, IP-consistent, Trap Int W_ext)`
- **Output Definitions**: RP RF/U every 1 inc; Companion SDV14/SDV1 frame intervals 100/50
- **Mesh Generation Method**: Structured rectilinear bias with graded refinement toward ligament
- **Element Topology**: Total Nodes = 52,126, Base Elements = 51,408 (Quads = 51,408, Tris = 0), Total INP Elements = 1,54,224
- **Crack Corridor Statistics ($x \in [0.5, 1.0]\,\text{mm}, y \in [0.45, 0.55]\,\text{mm}$, Area = $0.05\,\text{mm}^2 = 5.0\%$)**: Corridor Elements = 24,320 (**47.31%** of mesh), Corridor Quads = 24,320, Corridor Tris = 0, $h_{\min} = 1.25\,\mu\text{m}$ ($h/l_0 = 0.167$), Median $h = 1.25\,\mu\text{m}$
- **Completion Status & Terminal State**: Status = `TERMINATED_POST_FRACTURE_CUTBACK`, Final Reached $u = 0.007208\,\text{mm}$, Final $F = 0.000163\,\text{kN}$, Load Drop = 99.00\%
- **Physical Quantities**:
  - $K_0 = 137.836814\,\text{kN/mm}$ ($R^2 = 0.99999985$, Intercept = 4.468000e-5\,\text{kN}$, $N = 400$)
  - $F_{\max} = 0.729041\,\text{kN}$ at $u_{\text{peak}} = 0.005606\,\text{mm}$
  - Broken-State $E_{\text{frac}} = 2.368500\,\text{mJ}$, $W_{\text{ext}} = 2.170210\,\text{mJ}$
  - Crack Trajectory $y = 0.5000\,\text{mm}$ ($|\Delta y|_{\max} = 0.000\,\text{mm}$), Localization Width $w_{90} = 18.70\,\mu\text{m}$ ($w_{90}/l_0 = 2.49$)
- **Primary Result Files**: `PK_M1_S4_H00125.sta`, `PK_M1_S4_H00125_CURVES.csv`, `PK_M1_S4_H00125_SUMMARY.json`, `S4_h00125_51k_MECHANICAL_FU_AUDITED.csv`

### Case 5: S5 Fixed Ultra Fine Mesh (`S5_FIX69K`)
- **Scientific Purpose & Role**: FIXED_STRUCTURED_BIAS
- **PBS / Job ID**: `1406019.mmaster02` (`PK_M1_S5_H00100`, node `mnode098`, queue `normal_imfdfkmq`, mode `SERIAL_1CPU`)
- **Submission Timestamp**: `2026-09-17T13:15:14+02:00`
- **Input Deck Path & SHA-256**: `models/pandey_kumar_mode1/batch_mode1_energy_convergence/S5_h00100_69k/PK_M1_S5_H00100.inp` (`6A111A84F3DF917594BF2AE16FE04787A2754E588448EB97E68CF18D227C88B7`, 88,72,500 bytes)
- **User Subroutine Path & SHA-256**: `models/pandey_kumar_mode1/batch_mode1_energy_convergence/f42_mixed_uel.for` (`5CD0D2C015C9EAD91C99D7A744156CC86F5B5EA26473BBED7D6E5515FE30FA46`, 29,722 bytes)
- **UEL Property ABI Card**: `(l0, Gc, E, nu, k, N_phys) = (0.0075, 0.0027, 210.0, 0.3, 1.0e-7, 69384.0)`
- **Geometry & Zero-Gap Seam**: 1.0 mm x 1.0 mm square domain, a0 = 0.5 mm sharp horizontal seam along y = 0.500 mm with `ZERO_GAP_DUPLICATED_NODES`
- **Boundary Conditions**: Bottom y=0: u_y=0, pinned (0,0): u_x=0; Top y=1: prescribed u_y
- **Material Constants**: $E = 210\,\text{GPa}, \nu = 0.3, G_c = 0.0027\,\text{kN/mm}, l_0 = 0.0075\,\text{mm}, k = 10^{-7}$
- **Temporal Schedule**: Step 1: dt=5.0e-4, du=2.5 nm, INC=2000; Step 2: dt=2.0e-4, du=1.0 nm, INC=5000
- **Solver Controls**: `DEFAULT`
- **Energy Instrumentation**: `uel_energy_balance.csv (Unit 105, IP-consistent, Trap Int W_ext)`
- **Output Definitions**: RP RF/U every 1 inc; Companion SDV14/SDV1 frame intervals 100/50
- **Mesh Generation Method**: Structured rectilinear bias with graded refinement toward ligament
- **Element Topology**: Total Nodes = 70,324, Base Elements = 69,384 (Quads = 69,384, Tris = 0), Total INP Elements = 2,08,152
- **Crack Corridor Statistics ($x \in [0.5, 1.0]\,\text{mm}, y \in [0.45, 0.55]\,\text{mm}$, Area = $0.05\,\text{mm}^2 = 5.0\%$)**: Corridor Elements = 36,240 (**52.23%** of mesh), Corridor Quads = 36,240, Corridor Tris = 0, $h_{\min} = 1.00\,\mu\text{m}$ ($h/l_0 = 0.133$), Median $h = 1.00\,\mu\text{m}$
- **Completion Status & Terminal State**: Status = `TERMINATED_POST_FRACTURE_CUTBACK`, Final Reached $u = 0.009580\,\text{mm}$, Final $F = 0.000153\,\text{kN}$, Load Drop = 99.90\%
- **Physical Quantities**:
  - $K_0 = 137.823267\,\text{kN/mm}$ ($R^2 = 0.99999990$, Intercept = 4.466000e-5\,\text{kN}$, $N = 400$)
  - $F_{\max} = 0.725460\,\text{kN}$ at $u_{\text{peak}} = 0.005575\,\text{mm}$
  - Broken-State $E_{\text{frac}} = 2.355000\,\text{mJ}$, $W_{\text{ext}} = 2.147920\,\text{mJ}$
  - Crack Trajectory $y = 0.5000\,\text{mm}$ ($|\Delta y|_{\max} = 0.000\,\text{mm}$), Localization Width $w_{90} = 18.45\,\mu\text{m}$ ($w_{90}/l_0 = 2.46$)
- **Primary Result Files**: `PK_M1_S5_H00100.dat`, `PK_M1_S5_H00100.sta`, `PK_M1_S5_H00100_CURVES.csv`, `PK_M1_S5_H00100_SUMMARY.json`, `S5_h00100_69k_MECHANICAL_FU_AUDITED.csv`

### Case 6: Package 24 Adaptive 2% Variant (`ADAPT_2PCT_PKG24`)
- **Scientific Purpose & Role**: ADAPTIVE_QUAD_DOMINATED_FREE
- **PBS / Job ID**: `1409846.mmaster02` (`PK_M1_ADAPT_2PCT_13K_ENERGY`, node `mnode097`, queue `normal_imfdfkmq`, mode `SERIAL_1CPU`)
- **Submission Timestamp**: `2026-10-02T15:08:44+02:00`
- **Input Deck Path & SHA-256**: `models/pandey_kumar_mode1/24_adaptive_candidate_2pct_13k/PK_MODE1_ADAPT_2PCT_13K_ENERGY.inp` (`9113C5F609B86DE03FD0AD4A18A971EC3ED5424664BFE44E695E96789D4D6ECC`, 17,88,875 bytes)
- **User Subroutine Path & SHA-256**: `models/pandey_kumar_mode1/24_adaptive_candidate_2pct_13k/f42_mixed_uel.for` (`CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6`, 29,722 bytes)
- **UEL Property ABI Card**: `(l0, Gc, E, nu, k, N_phys) = (0.0075, 0.0027, 210.0, 0.3, 1.0e-7, 13897.0)`
- **Geometry & Zero-Gap Seam**: 1.0 mm x 1.0 mm square domain, a0 = 0.5 mm sharp horizontal seam along y = 0.500 mm with `ZERO_GAP_DUPLICATED_NODES`
- **Boundary Conditions**: Bottom y=0: u_y=0, pinned (0,0): u_x=0; Top y=1: prescribed u_y
- **Material Constants**: $E = 210\,\text{GPa}, \nu = 0.3, G_c = 0.0027\,\text{kN/mm}, l_0 = 0.0075\,\text{mm}, k = 10^{-7}$
- **Temporal Schedule**: Step 1: dt=5.0e-4, du=2.5 nm, INC=2000; Step 2: dt=2.0e-4, du=1.0 nm, INC=5000
- **Solver Controls**: `DEFAULT`
- **Energy Instrumentation**: `uel_energy_balance.csv (Unit 105, IP-consistent, Trap Int W_ext)`
- **Output Definitions**: RP RF/U every 1 inc; Companion SDV14/SDV1 frame intervals 100/50
- **Mesh Generation Method**: Native Abaqus/CAE adaptiveRemesh (2% errorTarget on standard continuum pre-analysis)
- **Element Topology**: Total Nodes = 13,885, Base Elements = 13,897 (Quads = 13,506, Tris = 391), Total INP Elements = 41,691
- **Crack Corridor Statistics ($x \in [0.5, 1.0]\,\text{mm}, y \in [0.45, 0.55]\,\text{mm}$, Area = $0.05\,\text{mm}^2 = 5.0\%$)**: Corridor Elements = 1,718 (**12.36%** of mesh), Corridor Quads = 1,667, Corridor Tris = 51, $h_{\min} = 0.87\,\mu\text{m}$ ($h/l_0 = 0.116$), Median $h = 2.59\,\mu\text{m}$
- **Completion Status & Terminal State**: Status = `COMPLETED`, Final Reached $u = 0.010000\,\text{mm}$, Final $F = 0.000215\,\text{kN}$, Load Drop = 99.97\%
- **Physical Quantities**:
  - $K_0 = 137.890000\,\text{kN/mm}$ ($R^2 = 0.99999975$, Intercept = 4.470000e-5\,\text{kN}$, $N = 400$)
  - $F_{\max} = 0.744100\,\text{kN}$ at $u_{\text{peak}} = 0.005750\,\text{mm}$
  - Broken-State $E_{\text{frac}} = 2.290000\,\text{mJ}$, $W_{\text{ext}} = 2.278000\,\text{mJ}$
  - Crack Trajectory $y = 0.5000\,\text{mm}$ ($|\Delta y|_{\max} = 0.000\,\text{mm}$), Localization Width $w_{90} = 19.10\,\mu\text{m}$ ($w_{90}/l_0 = 2.55$)
- **Primary Result Files**: `PK_M1_ADAPT_2PCT_13K_ENERGY.dat`, `PK_M1_ADAPT_2PCT_13K_ENERGY.sta`, `uel_energy_balance.csv`, `ADAPT_13K_1409846_SCIENTIFIC_QUALIFICATION_REPORT.json`

### Case 7: Package 25 Stage-14 Adaptive Candidate (`ADAPT_STAGE14_PKG25`)
- **Scientific Purpose & Role**: ADAPTIVE_QUAD_DOMINATED_FREE
- **PBS / Job ID**: `1409953.mmaster02 / 1409982.mmaster02` (`PK_M1_ADAPT_14K_FRACTURE`, node `mnode097`, queue `normal_imfdfkmq`, mode `SERIAL_1CPU`)
- **Submission Timestamp**: `2026-10-03T22:29:29+02:00 (1409953) / 2026-10-04T11:20:33+02:00 (1409982)`
- **Input Deck Path & SHA-256**: `models/pandey_kumar_mode1/25_stage14_adaptive_candidate_14k/PK_MODE1_STAGE14_ADAPT_14K_FRACTURE.inp` (`26D873FB2E68055C80550D1DD981766BCAF46E13D3D0A7BA6411B63D9C382D35`, 18,69,997 bytes)
- **User Subroutine Path & SHA-256**: `models/pandey_kumar_mode1/25_stage14_adaptive_candidate_14k/f42_mixed_uel.for` (`CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6`, 29,722 bytes)
- **UEL Property ABI Card**: `(l0, Gc, E, nu, k, N_phys) = (0.0075, 0.0027, 210.0, 0.3, 1.0e-7, 14483.0)`
- **Geometry & Zero-Gap Seam**: 1.0 mm x 1.0 mm square domain, a0 = 0.5 mm sharp horizontal seam along y = 0.500 mm with `ZERO_GAP_DUPLICATED_NODES`
- **Boundary Conditions**: Bottom y=0: u_y=0, pinned (0,0): u_x=0; Top y=1: prescribed u_y
- **Material Constants**: $E = 210\,\text{GPa}, \nu = 0.3, G_c = 0.0027\,\text{kN/mm}, l_0 = 0.0075\,\text{mm}, k = 10^{-7}$
- **Temporal Schedule**: Step 1: dt=5.0e-4, du=2.5 nm, INC=2000; Step 2: dt=2.0e-4, du=1.0 nm, INC=6000
- **Solver Controls**: `*CONTROLS, PARAMETERS=TIME INCREMENTATION: 4, 10, 9, 20, 10, 4, 0, 10`
- **Energy Instrumentation**: `uel_energy_balance.csv (Unit 105, IP-consistent, Trap Int W_ext)`
- **Output Definitions**: RP RF/U every 1 inc; Companion SDV14/SDV1 frame intervals 100/50
- **Mesh Generation Method**: Native Abaqus/CAE adaptiveRemesh (Infinitesimal Companion Pre-Analysis with Kinematic Strain Localization)
- **Element Topology**: Total Nodes = 14,457, Base Elements = 14,483 (Quads = 14,082, Tris = 401), Total INP Elements = 43,449
- **Crack Corridor Statistics ($x \in [0.5, 1.0]\,\text{mm}, y \in [0.45, 0.55]\,\text{mm}$, Area = $0.05\,\text{mm}^2 = 5.0\%$)**: Corridor Elements = 8,338 (**57.57%** of mesh), Corridor Quads = 8,100, Corridor Tris = 238, $h_{\min} = 0.76\,\mu\text{m}$ ($h/l_0 = 0.101$), Median $h = 2.06\,\mu\text{m}$
- **Completion Status & Terminal State**: Status = `FRACTURE_COMPLETE__SOLVER_COMPLETION_RERUN_RUNNING`, Final Reached $u = 0.007889\,\text{mm}$, Final $F = 0.001764\,\text{kN}$, Load Drop = 99.76\%
- **Physical Quantities**:
  - $K_0 = 137.909558\,\text{kN/mm}$ ($R^2 = 0.99999960$, Intercept = 4.471205e-5\,\text{kN}$, $N = 400$)
  - $F_{\max} = 0.743701\,\text{kN}$ at $u_{\text{peak}} = 0.005733\,\text{mm}$
  - Broken-State $E_{\text{frac}} = 2.285469\,\text{mJ}$, $W_{\text{ext}} = 2.267380\,\text{mJ}$
  - Crack Trajectory $y = 0.5000\,\text{mm}$ ($|\Delta y|_{\max} = 0.000\,\text{mm}$), Localization Width $w_{90} = 19.05\,\mu\text{m}$ ($w_{90}/l_0 = 2.54$)
- **Primary Result Files**: `PK_M1_ADAPT_14K_FRACTURE.dat`, `PK_M1_ADAPT_14K_FRACTURE.sta`, `uel_energy_balance.csv`, `MODE1_STAGE14S_CLAIMS_DISCIPLINE_AND_PROVENANCE_CLOSURE_REPORT.json`, `MODE1_STAGE14T_TERMINAL_INTEGRITY_REPORT.json`

