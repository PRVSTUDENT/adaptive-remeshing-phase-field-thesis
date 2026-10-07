# MODE-II SOURCE PROVENANCE TABLE
## Pandey & Kumar (2025) Pure Shear Specimen Re-Analysis & Pre-Analysis Verification

**Governing Literature Source**: Pandey, V., & Kumar, S. (2025). "An External Driver-Based Implementation of Adaptive Mesh Refinement in Abaqus for Phase-Field Modeling of Fracture." *Computer Modeling in Engineering & Sciences* (CMES), 144(3), 3255–3283. DOI: [10.32604/cmes.2025.067858](https://doi.org/10.32604/cmes.2025.067858).

---

### Epistemic Classification Scheme:
- **`SOURCE_VERIFIED`**: Explicitly stated or unambiguously defined in Pandey & Kumar (2025) text, listings, tables, or figure captions.
- **`PROJECT_CHOICE`**: Methodological or numerical configuration explicitly chosen by the project team to resolve underspecified aspects, guided by foundational PFM literature.
- **`INFERRED`**: Mathematically or topologically derived from published graphical/numerical data (e.g., digitized coordinates, colorbar bounds).
- **`NOT_REPORTED`**: Parameter or configuration omission in the paper text/listings.

---

### 1. Specimen Geometry & Domain Topology

| Parameter / Feature | Value / Specification | Epistemic Classification | Source Provenance & Evidence Basis |
| :--- | :--- | :--- | :--- |
| **Domain Geometry** | $1.0 \times 1.0$ mm square plate | `SOURCE_VERIFIED` | Sec. 4.2 & Fig. 4(b), p. 3264 ("Single edge crack specimen geometry, dimensions and boundary conditions for (b) Mode-II loading") |
| **Initial Crack Length** | $a_0 = 0.5$ mm along mid-plane $y = 0.5$ mm ($0.0 \le x \le 0.5$ mm) | `SOURCE_VERIFIED` | Sec. 4.1 & 4.2 ("edge crack of length 0.5 mm", Fig. 4b) |
| **Crack Representation** | Zero-thickness sharp seam crack with duplicate coincident node pairs on upper/lower crack faces | `SOURCE_VERIFIED` | Sec. 2 & 4.2; CAE partition line assigned as Seam; crack tip at $(0.5, 0.5)$ |
| **Coordinate System** | Origin $(0.0, 0.0)$ at bottom-left corner; $x \in [0, 1]$, $y \in [0, 1]$ mm | `SOURCE_VERIFIED` | Figs. 4(b), 6(b), 12(b); crack notch starts at $x=0, y=0.5$ and terminates at $x=0.5, y=0.5$ |

---

### 2. Material & Phase-Field Properties

| Parameter / Feature | Value / Specification | Epistemic Classification | Source Provenance & Evidence Basis |
| :--- | :--- | :--- | :--- |
| **Young's Modulus ($E$)** | $210$ GPa ($210.0$ kN/mm$^2$) | `SOURCE_VERIFIED` | Sec. 4.1 & 4.2, p. 3264 ("Young’s modulus, E = 210 GPa") |
| **Poisson's Ratio ($\nu$)** | $0.3$ | `SOURCE_VERIFIED` | Sec. 4.1 & 4.2, p. 3264 ("Poisson’s ratio, ν = 0.3") |
| **Length Scale ($l_0$)** | $0.015$ mm ($15\,\mu\text{m}$) | `SOURCE_VERIFIED` | Sec. 4.2, p. 3270 ("length scale, l0 = 0.015 mm") |
| **Critical Fracture Energy ($G_c$)** | $2.7 \times 10^{-3}$ kN/mm ($2,700$ J/m$^2$) | `SOURCE_VERIFIED` | Sec. 4.2, p. 3270 ("fracture energy, Gc = 2.7 × 10−3 KN/mm") |
| **Degradation Function** | $g(d) = (1-d)^2 + k$ | `SOURCE_VERIFIED` | Sec. 2.1, Eq. (3); standard quadratic degradation |
| **Residual Stiffness ($k$)** | $1.0 \times 10^{-7}$ | `INFERRED` / `PROJECT_CHOICE` | Standard numerical parameter in staggered Miehe PFM implementations [Miehe 2010, Molnar 2017]; ensures well-posedness in fully damaged cells |
| **Energy Split** | Miehe anisotropic tensile/compressive strain energy decomposition | `SOURCE_VERIFIED` | Sec. 4.2, p. 3270 ("Anisotropic split by Miehe et al. [41] is employed in this problem") |

---

### 3. Boundary & Loading Conditions

| Parameter / Feature | Value / Specification | Epistemic Classification | Source Provenance & Evidence Basis |
| :--- | :--- | :--- | :--- |
| **Bottom Boundary ($y=0$)** | Fixed: $u_x = 0, u_y = 0$ along $x \in [0, 1]$ | `SOURCE_VERIFIED` | Sec. 4.2, p. 3270 ("The bottom edge is kept fixed ($u_x = u_y = 0$)") |
| **Top Boundary ($y=1$) Horizontal** | Monotonic shear displacement $u_x$ applied via Reference Point | `SOURCE_VERIFIED` | Sec. 4.2, p. 3270 ("horizontal displacement is applied at the top edge of the plate") |
| **Top Boundary ($y=1$) Vertical ($u_y$)** | Restrained $u_y = 0$ (Pure macroscopic shear $\gamma = u_x / H$) | `PROJECT_CHOICE` / `NOT_REPORTED` | Paper text does not state vertical condition on top; $u_y = 0$ is the standard definition of pure shear benchmark in PFM literature [Miehe 2010, Ambati 2015, Molnar 2017] |
| **Lateral Boundaries ($x=0, x=1$)** | Traction-free | `SOURCE_VERIFIED` | Fig. 4(b); standard boundary conditions |

---

### 4. Coarse Pre-Analysis Model (`Job-1_UEL.inp`)

| Parameter / Feature | Value / Specification | Epistemic Classification | Source Provenance & Evidence Basis |
| :--- | :--- | :--- | :--- |
| **Pre-Analysis Job Name** | `Job-1_UEL.inp` | `SOURCE_VERIFIED` | Sec. 4.2, p. 3271 ("The pre-adaptive ‘Job-1_UEL.inp’ is submitted...") & Fig. 6(b) caption |
| **Formulation Architecture** | 3-Layer Mixed UEL/UMAT: Layer 1 UEL phase (U1/U3), Layer 2 UEL mech (U2/U4), Layer 3 Companion (`All_elem` / `umatelem`) | `SOURCE_VERIFIED` | Sec. 3.2, 3.3, 4.2, Listings 1–3 |
| **Initial Mesh Global Size** | $h_{\text{cms}} = 0.02$ mm | `SOURCE_VERIFIED` | Sec. 4.2, p. 3271 ("The initial mesh with the global mesh size of 0.02 mm is analyzed...") |
| **Element & Node Counts** | $N_{\text{phys}} = 2,960$ elements ($2,860$ CPE4 quads, $100$ CPE3 tris), $3,036$ nodes | `PROJECT_CHOICE` / `INFERRED` | Exact discretization produced by Abaqus CAE 0.02 mm uniform seeding on partitioned $1\times 1$ mm square plate with seam |
| **Fortran Subroutine ABI** | `PROPS(1..6)` = $(l_0, G_c, E, \nu, k, N_{\text{phys}}) = (0.015, 0.0027, 210.0, 0.3, 10^{-7}, 2960.0)$ | `SOURCE_VERIFIED` | Authoritative `f42_mixed_uel.for` (SHA-256: `ce8d5edcd2911dcb018bb15275271f874e7ea62b8fb48cf4a8297469a83acdd6`) |
| **Step 1 Increments** | 2,100 increments at $\Delta u_1 = 5 \times 10^{-4}$ mm ($u \to 0.0105$ mm) | `SOURCE_VERIFIED` | Sec. 4.2, p. 3271 ("submitted for 2100 increments of size $\Delta u_1 = 5 \times 10^{-4}$") |
| **Step 2 Increments** | 5,000 increments at $\Delta u_2 = 10^{-5}$ mm ($u \to 0.0600$ mm) | `SOURCE_VERIFIED` | Sec. 4.2, p. 3271 ("and then at $\Delta u_2 = 10^{-5}$ for a further 5000 increments") |
| **Output Variables** | `MISESERI, MISESAVG, S, EVOL` on `All_elem`; `SDV` on `umatelem`; `U, RF` on `N_RP` | `SOURCE_VERIFIED` | Sec. 3.3, Listings 2 & 3 |
| **Figure 6(b) Colorbar Bounds** | $10^{-19}$ to $10^{-12}$ | `INFERRED` | Fig. 6(b) colorbar; represents small-strain elastic stress discrepancy on dummy facsimile elements ($E_{\text{UMAT}} = 10^{-11}$) |

---

### 5. Native Remeshing Rule & Adaptive Corridor

| Parameter / Feature | Value / Specification | Epistemic Classification | Source Provenance & Evidence Basis |
| :--- | :--- | :--- | :--- |
| **Remeshing Error Indicator** | `MISESERI` | `SOURCE_VERIFIED` | Sec. 3.1, 4.2, Listing 1 |
| **Remeshing Function** | `mdb.models[model_name].adaptiveRemesh(odb=o1)` | `SOURCE_VERIFIED` | Listing 4, p. 3263 |
| **Target Element Set** | Part/Assembly set `All_elem` | `SOURCE_VERIFIED` | Sec. 3.3, Listing 1 & 2 ("crucial for establishing the remeshing rule in Abaqus") |
| **Target Error (`errorTarget`)** | Not reported in Mode-II text (Listing 1 shows `1.0%`, Sec. 3.3 states `1%–5%`, Sec. 4.1.3 tests `2, 5, 10, 20%`) | `NOT_REPORTED` (`PROJECT_CHOICE`: sweep $\{1.0, 2.0, 3.0, 5.0\%\}$) | Section 4.2 omits explicit `errorTarget` for Mode-II; must be systematically evaluated against published target mesh |
| **Refinement Factor** | $10$ | `SOURCE_VERIFIED` | Listing 1; Sec. 4.1.3 ("refinementFactor = 10 is adopted for the rest of the simulations") |
| **Coarsening Factor** | `NOT_ALLOWED` | `SOURCE_VERIFIED` | Listing 1 |
| **Maximum Element Size** | $0.02$ mm | `SOURCE_VERIFIED` | Sec. 4.2 |
| **Minimum Element Size** | $0.001$ mm or $0.003$ mm | `NOT_REPORTED` (`PROJECT_CHOICE`: test $0.001$ and $0.003$ mm) | Sec. 4.1 Mode-I used $0.001$ mm, while Sec. 4.2 standard Mode-II mesh used $0.003$ mm |
| **Target Adapted Elements** | $19,963$ elements | `SOURCE_VERIFIED` | Sec. 4.2, Fig. 12(b) caption ("Proposed PFM ... with 19,963 elements") |
| **Corridor Trajectory** | Origin $(0.50, 0.50) \to$ Bottom boundary $(0.868 - 0.930, 0.000)$; chord angle $\theta \approx -49.74^\circ$ to $-53.65^\circ$ | `SOURCE_VERIFIED` | Digitized from Fig. 6(b) and Fig. 12(b); zero spurious branching |

---

### 6. Summary of Corrections to Prior Working Assumptions
1. **Control vs Phase-Field Pre-Analysis**: The pure-elastic linear pre-analysis (`JOB_MODE2_UNIFORM_COARSE`) has been formally downgraded to control evidence. It concentrates error purely at the static slit tip and horizontal boundaries ($\theta \approx -2.53^\circ$). The publication's Fig. 6(b) was explicitly obtained from `Job-1_UEL.inp` where phase-field damage propagates along the inclined shear corridor.
2. **Removal of Post-Hoc Tolerances**: Arbitrary thresholds ($<8\%$, $<2.5 l_0$, $>65\%$) have been removed. Qualification is judged strictly on physical corridor tracking, absence of spurious branching, and numerical convergence.
3. **Mode-II `errorTarget` Classification**: Classifying `errorTarget` as `NOT_EXPLICITLY_REPORTED` in Section 4.2; exploring $\{1, 2, 3, 5\%\}$ as a controlled sensitivity sweep.
