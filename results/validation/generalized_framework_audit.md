# Generalized 2D Field-Driven Adaptive Remeshing Framework Audit

## 1. Case 1 Executive Integrity (Mode-I Off-Axis Hole Plate)
- **Physical Deck:** `models/pandey_kumar_mode1/176_method_a_plate_with_hole/PK_HOLE_METHOD_A_GEN_PHYS.inp`
- **Production UEL Deck:** `models/pandey_kumar_mode1/176_method_a_plate_with_hole/PK_HOLE_METHOD_A_GEN_PROD.inp`
- **Physical Elements:** 54604 (52789 quads [96.68%], 1815 tris [3.32%])
- **Nodes:** 54129
- **Layered UEL Elements:** 163812 (Exact 3-layer parity: **PASS**)
- **Non-Positive Element Areas (Jacobians):** 0 (**PASS**)

## 2. Regional Resolution Metrics ($h_{\max} \le 1.5\,\mu\text{m}$ Target)

| Physical Region | Element Count ($N$) | $h_{\max} \le 1.5\,\mu\text{m}$ (%) | Median $h_{\max}$ [$\mu$m] | 95th % $h_{\max}$ [$\mu$m] | Max $h_{\max}$ [$\mu$m] | $h_{\text{equiv}} \le 1.5\,\mu\text{m}$ (%) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **Initial Crack Zone** | 6155 | **83.8%** | 1.291 | 1.692 | 7.442 | 98.2% |
| **Ligament Zone** | 12435 | **72.9%** | 1.343 | 1.900 | 3.093 | 91.7% |
| **Hole Left Flank** | 4106 | **53.3%** | 1.474 | 2.109 | 2.950 | 81.6% |
| **Hole Right Flank** | 3850 | **45.3%** | 1.535 | 2.165 | 2.799 | 75.6% |
| **Left Support Interior** | 16603 | **83.7%** | 1.291 | 1.654 | 2.138 | 99.2% |
| **Right Support Interior** | 5553 | **73.3%** | 1.356 | 1.729 | 2.239 | 96.7% |
| **Outer Bulk Domain** | 13235 | **12.7%** | 4.366 | 20.000 | 29.955 | 22.3% |
| **Entire Plate** | 54604 | **49.4%** | 1.507 | 12.607 | 29.955 | 66.5% |

## 3. Unresolved Violations in Active Fracture Supports

### Left Support
- **Total Elements:** 16603
- **Compliant Elements ($h_{\max} \le 1.5\,\mu\text{m}$):** 13889 (83.7%)
- **Violations ($h_{\max} > 1.5\,\mu\text{m}$):** 2714 (16.4%)
- **Maximum Violation Edge:** 2.138 $\mu$m (95th percentile: 1.818 $\mu$m)
- **Root Cause:** Outer perimeter buffer transition elements grading smoothly toward coarse bulk domain (h_bulk = 20 um)
- **Top 5 Largest Violation Elements:**

  | Element ID | Centroid (x, y) [mm] | Longest Edge $h_{\max}$ [$\mu$m] | Equivalent $h_{\text{equiv}}$ [$\mu$m] |
  | :---: | :---: | :---: | :---: |
  | 9517 | (0.5503, 0.6250) | 2.138 | 1.653 |
  | 16292 | (0.5506, 0.6237) | 2.138 | 1.633 |
  | 7149 | (0.5430, 0.6728) | 2.074 | 1.479 |
  | 7178 | (0.5441, 0.6737) | 2.074 | 1.597 |
  | 6799 | (0.5677, 0.5624) | 2.068 | 1.364 |

### Right Support
- **Total Elements:** 5553
- **Compliant Elements ($h_{\max} \le 1.5\,\mu\text{m}$):** 4068 (73.3%)
- **Violations ($h_{\max} > 1.5\,\mu\text{m}$):** 1485 (26.7%)
- **Maximum Violation Edge:** 2.239 $\mu$m (95th percentile: 1.887 $\mu$m)
- **Root Cause:** Outer perimeter buffer transition elements grading smoothly toward coarse bulk domain (h_bulk = 20 um)
- **Top 5 Largest Violation Elements:**

  | Element ID | Centroid (x, y) [mm] | Longest Edge $h_{\max}$ [$\mu$m] | Equivalent $h_{\text{equiv}}$ [$\mu$m] |
  | :---: | :---: | :---: | :---: |
  | 478 | (0.7454, 0.6169) | 2.239 | 1.544 |
  | 482 | (0.7450, 0.6157) | 2.239 | 1.653 |
  | 469 | (0.7509, 0.6485) | 2.203 | 1.546 |
  | 1208 | (0.7510, 0.6471) | 2.203 | 1.696 |
  | 506 | (0.7299, 0.5871) | 2.144 | 1.365 |

## 4. Software Generality Suite Verification

| Benchmark Case | Geometry Specimen | Indicator Source | Physical Elements | Nodes | Jacobians Quality |
| :--- | :--- | :--- | :---: | :---: | :---: |
| **Case 1** | Mode-I Off-Axis Hole Plate | Authentic F1642 Precritical Damage ($d \ge 0.05$) | 54604 | 54129 | 100% Positive (**PASS**) |
| **Case 2** | Shifted Hole Plate ($(0.60, 0.40)$) | Multi-Hotspot Test Field [SYNTHETIC TEST FIELD] | 40940 | 40560 | 100% Positive (**PASS**) |
| **Case 3** | Pure Edge-Notched Plate (No Hole) | Crack Band Test Field [SYNTHETIC TEST FIELD] | 31675 | 31345 | 100% Positive (**PASS**) |
