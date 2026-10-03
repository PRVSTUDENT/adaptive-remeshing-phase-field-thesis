# Pre-Job Anti-Deviation Card: Stage 14 Reference-Fidelity 14k Adaptive Candidate

## 1. Proposal Task & Gate Mapping
- **Proposal Task:** Task 4 (Adaptive Remeshing Implementation) & Task 5 (Mode-I Fracture Validation).
- **Active Gate:** Gate 6B (Mode-I Energetic & Multi-Quantity Convergence Qualification).
- **Candidate Identifier:** `PK_M1_STAGE14_REFERENCE_FIDELITY_ADAPTIVE_CANDIDATE` (14,483 finite elements, 14,456 nodes).

## 2. Scientific Question & Hypothesis
- **Question:** Does the Stage-14 qualified 14,483-element native adaptive mesh (recovered directly from Step-2 phase-field pre-analysis under paper-literal 1.0% UNIFORM_ERROR remeshing) reproduce the qualified Mode-I reference fracture response ($F_{\max} = 0.757778\,\text{kN}$, $u_{\text{peak}} = 0.005857\,\text{mm}$, $K_0 = 137.945520\,\text{kN/mm}$)?
- **Hypothesis:** Because the 14,483 mesh preserves 59.39% coarse area in the far field while providing fine $h \in [1.0, 5.0]\,\mu\text{m}$ resolution along the complete crack path ($w(0.5) = 0.226\,\text{mm}, w(0.7) = 0.142\,\text{mm}, w(0.9) = 0.082\,\text{mm}$), it will reproduce the reference compliance, peak load, and crack propagation with high energetic fidelity while reducing computational cost relative to uniform fine meshes.

## 3. Frozen Parameters & Single Intended Change
- **Frozen Parameters:**
  - Specimen: $1.0 \times 1.0\,\text{mm}$ plate, $a_0 = 0.5\,\text{mm}$ sharp zero-gap seam.
  - Material: $E = 210\,\text{GPa}$, $\nu = 0.3$, $G_c = 2.7\times 10^{-3}\,\text{kN/mm}$, $l_0 = 0.0075\,\text{mm}$, $\eta = 10^{-7}$.
  - UEL Formulation: Authoritative 3-layer UEL+UMAT (`f42_mixed_uel.for`).
  - Loading: Displacement-controlled tensile pulling $u = 0.0100\,\text{mm}$ via Reference Point (RP).
- **Single Intended Change:** Mesh discretization changes from fixed uniform reference / provisional 2% candidate to the Stage-14 Step-2 recovered 14,483-element native adaptive mesh.

## 4. Pre-Declared Acceptance Criteria
- $K_0 \in [137.5, 138.5]\,\text{kN/mm}$ ($|\Delta K_0| < 0.5\%$ vs $137.945520\,\text{kN/mm}$).
- $F_{\max} \in [0.745, 0.765]\,\text{kN}$ ($|\Delta F_{\max}| < 1.7\%$ vs $0.757778\,\text{kN}$).
- $u(F_{\max}) \approx 0.00586\,\text{mm}$.
- Pure horizontal crack propagation along $y = 0.50\,\text{mm}$.
- Zero solver convergence cutbacks / divergence.
