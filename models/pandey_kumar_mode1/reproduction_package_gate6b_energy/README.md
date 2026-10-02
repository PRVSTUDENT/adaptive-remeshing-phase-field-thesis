# Gate-6B Mode-I Energy Convergence Reproduction Package

- **Protocol Version**: 2
- **Governing Directive**: *"We need to have understood everything related to the first model before we increase complexity."*
- **Active Phase**: `MODE1_GATE6B_ENERGY_CONVERGENCE_AND_STEP2_RECONCILIATION_ACTIVE`
- **Target Solver**: Abaqus 2023 / Intel Fortran Classic 2021.13.0 (OneAPI 2024.2.0)
- **Execution Architecture**: Single-Rank 1-CPU Serial (Shared-Memory Reference Baseline)
- **Production Source SHA-256**: `CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6`

---

## 1. Scientific Overview & Scope

This reproduction package provides the complete, self-contained, and lightweight deliverables required to reproduce the Mode-I phase-field fracture energy convergence sequence across three spatial discretizations:

1. **Candidate $S_1$ (Reference Baseline)**: 15,192 finite elements ($h_{\min} = 0.0030\,\text{mm} = 0.40 l_0$), $N_{\text{phys}} = 15192.0$.
2. **Candidate $S_2$ (Intermediate Discretization)**: 32,130 finite elements ($h_{\min} = 0.0020\,\text{mm} = 0.267 l_0$), $N_{\text{phys}} = 32130.0$.
3. **Candidate $S_3$ (Fine Discretization)**: 41,912 finite elements ($h_{\min} = 0.0015\,\text{mm} = 0.20 l_0$), $N_{\text{phys}} = 41912.0$.

In accordance with supervisor instructions, this package eliminates the need for multi-gigabyte binary `.odb` transfers by delivering exact input decks (`.inp`), the verified single user subroutine (`f42_mixed_uel.for`), extraction scripts (`.py`), execution scripts (`.pbs`), step-by-step shell commands (`commands.txt`), and automated self-verification (`verify_reproduction_package.py`).

---

## 2. Corrected Energy-Output Architecture & Dimensional Rigor

### A. Three-Layer Co-Located Element Architecture & Companion Index Mapping ($\text{PHYSIDX}$)
In the three-layer co-located finite-element architecture:
- **Layer 1 (Phase-Field Mixed UEL Elements)**: Element labels $\text{NOEL} \in [1, N_{\text{phys}}]$. Coupled user elements solving mechanical displacements ($\mathbf{u}$, DOFs 1–2) and phase-field damage ($d$, DOF 3).
- **Layer 2 (Mechanical Continuum Elements)**: Element labels $\text{NOEL} \in [N_{\text{phys}}+1, 2N_{\text{phys}}]$. Standard continuum elements solving mechanical equilibrium.
- **Layer 3 (Companion Visualization Elements)**: Element labels $\text{NOEL} \in [2N_{\text{phys}}+1, 3N_{\text{phys}}]$. Visualization CPE4 elements assigned to dummy material `DUMMY_MAT` evaluated via `SUBROUTINE UMAT` with low visualizer stiffness $E_{\text{comp}} = 10^{-11}\,\text{GPa}$ to prevent mechanical interference.

To map Layer-3 companion elements back to their underlying physical finite-element index without race conditions or memory faults, `SUBROUTINE UMAT` computes the physical element index via:
$$\text{PHYSIDX} = \text{NOEL} - 2 N_{\text{phys}}$$
mapping companion labels $2N_{\text{phys}}+1, \dots, 3N_{\text{phys}}$ to physical indices $1, \dots, N_{\text{phys}}$.

In the corrected input decks, `*User Material, constants=3` explicitly defines $N_{\text{phys}}$ as `PROPS(3)`:
- $S_1$ Reference (15k): `210.0, 0.3, 15192.0`
- $S_2$ Candidate (32k): `210.0, 0.3, 32130.0`
- $S_3$ Candidate (42k): `210.0, 0.3, 41912.0`

This resolves the companion indexing defect where omitting `PROPS(3)` caused Fortran to fall back to a hardcoded default (71,320), resulting in invalid/negative array lookups for smaller meshes.

### B. Element-Field SDV Output & Three-Way Dimensional Framework
Companion Layer-3 elements request state variable output via `*Element Output, elset=All_elem` specifying `SDV` (with `*Depvar 20`).
The exact companion state variable assignments in `SUBROUTINE UMAT` are:
- `SDV1` / `SDV14`: Phase-field damage $d$ (`SV_PHASE_TRIAL(PHYSIDX)`).
- `SDV15`: Degradation function $g(d) = (1-d)^2 + 10^{-7}$.
- `SDV2` / `SDV16`: Historical maximum crack driving energy $\mathcal{H}$ (`SV_H_TRIAL(PHYSIDX, KPT)`).
- `SDV17`: Element-integrated phase-field / fracture surface energy $E_{\text{frac}}$ (`SV_E_FRAC(PHYSIDX)`, units: $\text{kN}\cdot\text{mm} \equiv \text{J} = 1000\,\text{mJ}$).
- `SDV18`: Element-integrated elastic strain energy $E_{\text{elas}}$ (`SV_E_ELAS(PHYSIDX)`, units: $\text{kN}\cdot\text{mm} \equiv \text{J} = 1000\,\text{mJ}$).
- `SDV19`: Local volumetric fracture-surface energy density $\psi_f$ (`SV_PSI_F(PHYSIDX)`, units: $\text{kN/mm}^2 \equiv \text{GPa} = 1000\,\text{MPa} \equiv \text{J/mm}^3 = 10^3\,\text{mJ/mm}^3$; point field variable, never directly summed).
- `SDV20`: Local volumetric elastic strain energy density $\psi_e$ (`SV_PSI_E(PHYSIDX)`, units: $\text{kN/mm}^2 \equiv \text{GPa} = 1000\,\text{MPa} \equiv \text{J/mm}^3 = 10^3\,\text{mJ/mm}^3$; point field variable, never directly summed).

**Dimensional Units Consistency in $\text{kN}-\text{mm}$**:
1. $1\,\text{kN/mm}^2 = 10^3\,\text{N}/(10^{-3}\,\text{m})^2 = 10^9\,\text{Pa} = 1000\,\text{MPa} = 1\,\text{GPa}$ (strictly rejecting $1\,\text{kN/mm}^2 = 1\,\text{MPa}$).
2. Volumetric energy density: $1\,\text{kN/mm}^2 = 1\,(\text{kN}\cdot\text{mm})/\text{mm}^3 \equiv 1\,\text{J/mm}^3 = 10^3\,\text{mJ/mm}^3$ (strictly rejecting $1\,\text{kN/mm}^2 = 1\,\text{J/mm}^2$).
3. Fracture toughness: $G_c = 0.0027\,\text{kN/mm} = 2.7\,\text{N/mm} = 2700\,\text{N/m} = 2700\,\text{J/m}^2 = 0.0027\,\text{J/mm}^2 = 2.7\times 10^{-3}\,\text{J/mm}^2$ (not $2.7\,\text{J/mm}^2$). Local density $\psi_f = G_c [\frac{d^2}{2l_0} + \frac{l_0}{2}|\nabla d|^2]$ has dimensions $(\text{kN/mm}) \times (1/\text{mm}) = \text{kN/mm}^2 \equiv \text{J/mm}^3 = 1000\,\text{MPa} = 1\,\text{GPa}$.

**Three-Way Dimensional & Provenance Framework for 2D Out-of-Plane Thickness**:
1. **Literature Formulation (Pandey & Kumar, 2025, Section 4.1)**:
   - In Pandey & Kumar (2025, CMES 144(3), 3251–3276), Section 4.1 (pages 3264–3265) formulates the Mode-I benchmark strictly as a 2D problem ($\Omega = 1.0 \times 1.0\,\text{mm}$, $a_0 = 0.5\,\text{mm}$, $E = 210\,\text{GPa}$, $\nu = 0.3$, $l_0 = 0.0075\,\text{mm}$, $G_c = 2.7\times 10^{-3}\,\text{kN/mm}$).
   - The primary literature publication **omits any out-of-plane thickness specification $t$** for the Mode-I benchmark (unlike Section 4.4 which explicitly specifies $t = 100\,\text{mm}$ for the 3D/plane-stress L-panel).
   - Statements attributing $t = 1.0\,\text{mm}$ to literature prescription are strictly rejected as unsupported.
2. **Tier 1 (Native 2D UEL Assembly)**:
   - In `f42_mixed_uel.for`, all quadratures evaluate pure 2D area integrals $\int_A \cdot \, dA$ with differential $\text{CJAC} = \det(J) \cdot \text{WT} \sim \text{mm}^2$.
   - Mechanical internal force is force per unit thickness: $F_{\text{int}} = \int_A B^T \sigma \, dA \sim \text{mm}^2 \cdot (1/\text{mm}) \cdot (\text{kN/mm}^2) = \text{kN/mm}$.
   - Tangent stiffness is stiffness per unit thickness: $K = \int_A B^T D B \, dA \sim \text{kN/mm}^2$.
   - Energy quadrature is energy per unit thickness: $E = \int_A \psi \, dA \sim \text{mm}^2 \cdot (\text{kN/mm}^2) = \text{kN} \equiv \text{J/mm}$.
   - Both mechanical residual and energy quadrature evaluate 2D area integrals without hardcoded thickness factors in Fortran, exhibiting 100% internal mutual dimensional parity at Tier 1 ($[F_{\text{int}}] \equiv [E_{\text{elem}}] \equiv [M L^1 T^{-2}]$).
3. **Tier 2 (Project Implementation Normalization Convention $t_{\text{ref}} = 1.0\,\text{mm}$)**:
   - The project adopts the convention $t_{\text{ref}} = 1.0\,\text{mm}$ to convert native per-unit-thickness UEL quantities into reported resultant tensile force ($F = F_{\text{raw}} \cdot t_{\text{ref}}$ in $\text{kN}$) and total scalar energy ($E = E_{\text{raw}} \cdot t_{\text{ref}}$ in $\text{kN}\cdot\text{mm} \equiv \text{J} = 1000\,\text{mJ}$) for a $1.0\text{-mm}$ slice.
   - Resultant physical tensile force: $F = F_{\text{int}} \cdot t_{\text{ref}} = F_{\text{int}} \cdot 1.0\,\text{mm} \sim \text{kN}$.
   - Total scalar energy: $E_{\text{model}} = E \cdot t_{\text{ref}} = E \cdot 1.0\,\text{mm} \sim \text{kN}\cdot\text{mm} \equiv \text{J} = 1000\,\text{mJ}$.
   - External boundary work: $W_{\text{ext}} = \int F \, du \sim \text{kN}\cdot\text{mm} \equiv \text{J} = 1000\,\text{mJ}$.
   - Numerically neutral (multiplying by 1.0 preserves all digits), but restores exact physical dimensions and eliminates any dimensional ambiguity.
4. **Epistemological Status of Companion Layer (`*Solid Section ... 1.0`)**:
   - The card `*Solid Section, elset=All_elem, material=DUMMY_MAT` with explicit `1.0` thickness is project-level evidence that the Layer-3 companion visualization layer adopts the same 1.0 mm convention.
   - It is strictly rejected as proof of a literature thickness prescription or UEL dimensionality.
5. **Historical Reference Anchor Contextualized**:
   - Initial stiffness: $K_0 = 137.945520\,\text{kN/mm}$ is structural stiffness for the 1-mm slice (or $137.945520\,\text{kN/mm}^2$ per unit thickness).
   - Peak force: $F_{\max} = 0.757778\,\text{kN}$ is resultant peak force for the 1-mm slice (or $0.757778\,\text{kN/mm}$ per unit thickness).

**Single-IP Deduplication Rule**: In Layer 3, whole-element scalar energies ($E_{\text{frac}}$ and $E_{\text{elas}}$) are assigned uniformly across all 4 Gauss integration points. Summing across all 4 integration points naively creates an unphysical $4\times$ overcounting artifact. Post-processors strictly extract **Integration Point 1 (`IP1`) only** (or compute whole-element centroid values once per unique finite element), perfectly recovering the global energy balance without overcounting.

### C. Persistent Working Directory CSV Output (`GETOUTDIR`)
- In `f42_mixed_uel.for`, `SUBROUTINE UEXTERNALDB` tracks global energy integrals across all increments:
  $$E_{\text{elas}}(t) = \int_\Omega \psi_e \, d\Omega, \quad E_{\text{frac}}(t) = \int_\Omega \psi_f \, d\Omega, \quad W_{\text{ext}}(t) = \int_0^u F(\tilde{u}) \, d\tilde{u}$$
- The output CSV `uel_energy_balance.csv` is created directly inside the simulation working directory using the standard Abaqus utility:
  ```fortran
  CHARACTER*512 OUTDIR_STR
  INTEGER L_OUTDIR
  CALL GETOUTDIR(OUTDIR_STR, L_OUTDIR)
  ```
- This resolves output file loss caused by relative path truncation or remote scratch redirect.

### D. Proof of Mathematical Invariance
Line-by-line diff audits between corrected production source `CE8D5EDC...` and baseline `5CD0D2C0...` / `C540B54A...` prove:
- **0 diff lines in `SUBROUTINE UEL`**: Residual vector `RHS` and tangent matrix `AMATRX` are bit-for-bit identical.
- **0 diff lines in `SUBROUTINE UMAT`**: Elasticity tensor, constitutive relations, and state variable updates are bit-for-bit identical.
- **Zero changes** to phase-field degradation $g(d) = (1-d)^2 + k$, history update $\mathcal{H}_{n+1} = \max(\mathcal{H}_n, \psi_0^+)$, or energy balance definitions.
- The modification is purely localized to file path construction in `UEXTERNALDB`.

---

## 3. Package File Structure & SHA-256 Manifest

| File Name | Description | SHA-256 Checksum |
| :--- | :--- | :--- |
| `PK_MODE1_REF15K_ENERGY.inp` | Candidate $S_1$ 15,192-element energy reference deck ($N_{\text{phys}}=15192.0$) | `EC560A4C265730647B43DAB125D166EBC57CAC285D574D38222A498A967535D9` |
| `PK_MODE1_FIX_H0020_ENERGY.inp` | Candidate $S_2$ 32,130-element energy input deck ($N_{\text{phys}}=32130.0$) | `9A5C3BD7EA9AF8CD38715FAC9FB062B1590766B7A7CF3A800D2F8C9E95C3767F` |
| `PK_MODE1_FIX_H0015_ENERGY.inp` | Candidate $S_3$ 41,912-element energy input deck ($N_{\text{phys}}=41912.0$) | `1500ECA5028660045789AF04AD3112E26CA76BBF7BFAC6437A42008A4307408F` |
| `f42_mixed_uel.for` | Single Gate-6B production Fortran source with `CALL GETOUTDIR` | `CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6` |
| `extract_authoritative_mode1_energy_complete.py` | Complete Mode-I energy extraction pipeline with flexible `--job-id` | `9270C0F2DC77F84799E2B6435E2D5BCB4FF693204A08EF76BD815D6414332E8A` |
| `handle_job_1409705_terminal_qualification.py` | 12-rule evidence-based qualification handler (Job 1409734 target) | `6F5FF44E218FEAF6F200827AF6E48C27AB77980E3CFD99C558521C45091326F7` |
| `spatial_convergence_pipeline.py` | Multi-quantity spatial convergence postprocessing pipeline | `CC413266FF7E97523756918C1933CF4F945E75CB7CABA082A2DDAF4CD0A18E2D` |
| `submit_s1_ref15k_energy.pbs` | PBS execution script for Candidate $S_1$ (1-CPU serial, `entry_imfdfkmq`) | `C26427E54FC1D91D53BE7C98FFBA0DCCDD2A241EC3C047860050C0A4DB676E1C` |
| `submit_s2_h0020_energy.pbs` | PBS execution script for Candidate $S_2$ (1-CPU serial, `entry_imfdfkmq`) | `207623D697D7F469BD27E7F75867B4C74CF27793A76F2B2DADE96801A366702E` |
| `submit_s3_h0015_energy.pbs` | PBS execution script for Candidate $S_3$ (1-CPU serial, `entry_imfdfkmq`) | `3595AAB6DF979B1AFEFB79A5217A81C3B1937A51877D65AEF0280C593CFD6CC6` |
| `commands.txt` | Complete step-by-step verified cluster commands | `60A7CD83CD46BE4181BBC3233A653A9F7ABA0A1ECDB8207ACAE8659C5B08E975` |
| `README.md` | Comprehensive architectural documentation & user guide (Updated with Three-Way Thickness Provenance Framework) | (Current Document) |
| `verify_reproduction_package.py` | Automated self-checking verification script | `34353B977FE8FA212EE75077381DD4AA7AAB4A5EBB1FB03D485A2D839077FDAD` |
| `MODE1_ENERGY_EQUATION_CODE_OUTPUT_MAP.md` | Authoritative Equation-to-Code-to-Output Map Specification | `F1CF6571AC3E21974491B13A99E0D7B402C6E6D92A2A452D2885926A9E3B6522` |

---

## 4. Verification & Execution Instructions

### A. Run Self-Check Verification
```bash
python3 verify_reproduction_package.py
```
This script confirms 18 / 18 checks (100.0% Exit 0):
1. Exact SHA-256 match for all 4 core simulation files.
2. Semantic mapping in `f42_mixed_uel.for`:
   - `PHYSIDX = NOEL - 2 * NPHYS_VAL` (Layer 3 index mapping).
   - Exact `STATEV(17..20)` assignments ($E_{\text{frac}}, E_{\text{elas}}, \psi_f, \psi_e$).
   - Presence of `CALL GETOUTDIR` in `SUBROUTINE UEXTERNALDB`.
3. Input decks define the exact mesh-specific constants:
   - S1: `constants=3` with `15192.0`
   - S2: `constants=3` with `32130.0`
   - S3: `constants=3` with `41912.0`
4. All input decks contain `*Element Output, elset=All_elem` requesting `SDV` and `*Depvar 20`.
5. Exact presence and non-emptiness across all 9 supporting deliverables.
6. Three-way thickness provenance consistency:
   - Literature Formulation: 2D Mode-I benchmark formulation documented by Pandey & Kumar (2025, Sec. 4.1) omits out-of-plane thickness $t$ (unlike Sec. 4.4 L-panel which specifies $t = 100\,\text{mm}$).
   - Tier 1: Source-level UEL area quadrature in `f42_mixed_uel.for` (`CJAC`) evaluates 2D integrals with zero explicit thickness factors (native per-unit-thickness assembly, $[F_{\text{int}}] \sim \text{kN/mm}$, $[E] \sim \text{J/mm} \equiv \text{kN}$).
   - Tier 2 Project Convention: $t_{\text{ref}} = 1.0\,\text{mm}$ adopted by the project converts native per-unit-thickness values to resultant physical force ($\text{kN}$) and total scalar energy ($\text{kN}\cdot\text{mm} \equiv \text{J} = 1000\,\text{mJ}$) for a 1.0-mm slice.
   - Companion Section: `*Solid Section ... 1.0` in input decks is project-level evidence that Layer 3 adopts the same convention; strictly rejected as proof of literature prescription or UEL dimensionality.

### B. Run Preflight Datacheck
```bash
abaqus job=PK_M1_REF15K_DC user=f42_mixed_uel.for input=PK_MODE1_REF15K_ENERGY.inp datacheck interactive
abaqus job=PK_M1_S2_DC user=f42_mixed_uel.for input=PK_MODE1_FIX_H0020_ENERGY.inp datacheck interactive
abaqus job=PK_M1_S3_DC user=f42_mixed_uel.for input=PK_MODE1_FIX_H0015_ENERGY.inp datacheck interactive
```

### C. Launch Solver (Batch Queue)
```bash
qsub submit_s1_ref15k_energy.pbs
```

### D. Extract & Qualify Energy Results
```bash
python3 extract_authoritative_mode1_energy_complete.py --job-id 1409734 --sim-dir . --output-json MODE1_AUTHORITATIVE_ENERGY_EVALUATION.json
python3 handle_job_1409705_terminal_qualification.py --job-id 1409734 --sim-dir .
```
