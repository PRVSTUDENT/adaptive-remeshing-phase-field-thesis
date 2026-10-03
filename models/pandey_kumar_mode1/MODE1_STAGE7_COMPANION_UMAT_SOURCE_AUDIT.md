# Gate-6B Stage 7 Source-Level Audit: Companion UMAT Implementation, Stress State, and Error-Indicator Semantics

**Document ID:** `MODE1-STAGE7-COMPANION-UMAT-SOURCE-AUDIT-20261003`  
**Task ID:** `F1183-GATE6B-ADAPTIVE-LOCALIZATION-STAGE7-LAYERED-COMPANION-DIAGNOSTIC-20261003`  
**Date:** October 3, 2026  
**Investigating Agent:** Gemini Antigravity  
**Governing Subroutine Source:** `models/pandey_kumar_mode1/f42_mixed_uel.for`  
**Authoritative SHA-256:** `CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6` (bit-identical to 044c0051 `f42_mixed_uel.for`)

---

## 1. Executive Summary & Objective

In Gate-6B Stage 7, the layered companion-element architecture (`Job-1_UEL` / `All_elem`) is audited at the Fortran source code level before execution. The objective is to determine:
1. Exactly what the companion UMAT subroutine does to `STRESS`, `DDSDDE`, `STATEV`, and the common block `/CB_STATE_TRANS/` at every solver call;
2. How the companion layer interacts mechanically and energetically with the co-located UEL Layer 1 (phase-field) and Layer 2 (mechanical displacement);
3. Whether and how the Abaqus Mises stress error indicator `MISESERI` can physically and numerically be evaluated on the companion element set `All_elem` from this implementation.

---

## 2. Line-by-Line Subroutine Analysis of Companion UMAT

From the authoritative `f42_mixed_uel.for` (lines 836–908):

```fortran
      SUBROUTINE UMAT(STRESS,STATEV,DDSDDE,SSE,SPD,SCD,
     1 RPL,DDSDDT,DRPLDE,DRPLDT,
     2 STRAN,DSTRAN,TIME,DTIME,TEMP,DTEMP,PREDEF,DPRED,CMNAME,
     3 NDI,NSHR,NTENS,NSTATV,PROPS,NPROPS,COORDS,DROT,PNEWDT,
     4 CELENT,DFGRD0,DFGRD1,NOEL,NPT,LAYER,KSPT,KSTEP,KINC)
      INCLUDE 'ABA_PARAM.INC'
      PARAMETER(N_CAPACITY=150000)
      CHARACTER*80 CMNAME
      DIMENSION STRESS(NTENS),STATEV(NSTATV),DDSDDE(NTENS,NTENS),
     1 STRAN(NTENS),DSTRAN(NTENS),TIME(2),PREDEF(1),DPRED(1),
     2 PROPS(NPROPS),COORDS(3),DROT(3,3),DFGRD0(3,3),DFGRD1(3,3)

      DOUBLE PRECISION SV_PHASE_COMMITTED(N_CAPACITY)
      DOUBLE PRECISION SV_PHASE_TRIAL(N_CAPACITY)
      DOUBLE PRECISION SV_H_COMMITTED(N_CAPACITY,4)
      DOUBLE PRECISION SV_H_TRIAL(N_CAPACITY,4)
      DOUBLE PRECISION SV_E_FRAC(N_CAPACITY)
      DOUBLE PRECISION SV_E_ELAS(N_CAPACITY)
      DOUBLE PRECISION SV_PSI_F(N_CAPACITY)
      DOUBLE PRECISION SV_PSI_E(N_CAPACITY)

      COMMON /CB_STATE_TRANS/ SV_PHASE_COMMITTED, SV_PHASE_TRIAL,
     1                        SV_H_COMMITTED, SV_H_TRIAL,
     2                        SV_E_FRAC, SV_E_ELAS,
     3                        SV_PSI_F, SV_PSI_E

      INTEGER I, J, NPHYS_VAL, PHYSIDX, KPT_IDX

      IF (NPROPS .GE. 3 .AND. PROPS(3) .GT. 0.D0) THEN
        NPHYS_VAL = INT(PROPS(3))
      ELSE
        NPHYS_VAL = 71320
      ENDIF

      PHYSIDX = NOEL - 2 * NPHYS_VAL
      IF (PHYSIDX .LE. 0) PHYSIDX = NOEL

      DO I=1, NTENS
        STRESS(I) = 0.D0
        DO J=1, NTENS
          DDSDDE(I,J) = 0.D0
        ENDDO
        DDSDDE(I,I) = 1.D-11
      ENDDO

      SSE = 0.D0
      SPD = 0.D0
      SCD = 0.D0

      IF (PHYSIDX .LE. N_CAPACITY .AND. PHYSIDX .GT. 0) THEN
        KPT_IDX = NPT
        IF (KPT_IDX .GT. 4) KPT_IDX = 4
        IF (KPT_IDX .LT. 1) KPT_IDX = 1

        IF (NSTATV .GE. 1)  STATEV(1)  = SV_PHASE_TRIAL(PHYSIDX)
        IF (NSTATV .GE. 2)  STATEV(2)  = SV_H_TRIAL(PHYSIDX, KPT_IDX)
        IF (NSTATV .GE. 14) STATEV(14) = SV_PHASE_TRIAL(PHYSIDX)
        IF (NSTATV .GE. 15) THEN
          STATEV(15) = (1.D0 - SV_PHASE_TRIAL(PHYSIDX))**2 + 1.D-7
        ENDIF
        IF (NSTATV .GE. 16) STATEV(16) = SV_H_TRIAL(PHYSIDX, KPT_IDX)
        IF (NSTATV .GE. 17) STATEV(17) = SV_E_FRAC(PHYSIDX)
        IF (NSTATV .GE. 18) STATEV(18) = SV_E_ELAS(PHYSIDX)
        IF (NSTATV .GE. 19) STATEV(19) = SV_PSI_F(PHYSIDX)
        IF (NSTATV .GE. 20) STATEV(20) = SV_PSI_E(PHYSIDX)
      ENDIF

      RETURN
      END
```

---

## 3. Quantitative Accounting of Variables at Each UMAT Call

| Variable | Implementation in Authoritative UMAT | Physical / Numerical Interpretation |
| :--- | :--- | :--- |
| `STRESS(1..NTENS)` | Identically set to `0.D0` | The companion standard element contributes **identically zero Cauchy stress** $\mathbf{\sigma} = \mathbf{0}$. Internal force vector $\mathbf{F}_{\text{int, UMAT}} = \int \mathbf{B}^T \mathbf{\sigma} d\Omega = \mathbf{0}$. |
| `DDSDDE(I,J)` | `DDSDDE(I,J) = 0.D0`, with `DDSDDE(I,I) = 1.D-11` | Infinitesimal dummy tangent stiffness ($10^{-11}\,\text{kN/mm}^2$). Ensures positive-definite local Jacobian without perturbing the global system stiffness ($\Delta K / K < 10^{-13}$). |
| `STATEV(1..NSTATV)` | Copies `SV_PHASE_TRIAL`, `SV_H_TRIAL`, `SV_E_FRAC`, `SV_E_ELAS`, etc. from `/CB_STATE_TRANS/` | Populates state variables `SDV1` ($d$), `SDV2` ($H$), `SDV14` ($d$), `SDV15` ($g(d)$), `SDV16` ($H$), `SDV17` ($E_{\text{frac}}$), `SDV18` ($E_{\text{elas}}$) for post-processing and visualization. |
| `SSE, SPD, SCD` | Identically set to `0.D0` | Zero specific elastic strain energy, zero plastic dissipation, zero creep dissipation contributed by the companion layer. |
| `PHYSIDX` | `NOEL - 2 * NPHYS_VAL` | Re-indexes companion element ID $e_{\text{companion}} \in [2 N_{\text{phys}}+1, 3 N_{\text{phys}}]$ back to the physical element index $i_{\text{phys}} \in [1, N_{\text{phys}}]$. |

---

## 4. Interaction with UEL Layers & Stress-Recovery Semantics

### 4.1 Mechanical Parity
In the 3-layer architecture:
- **Layer 1 (U1/U3):** Solves the phase-field Helmholtz equation, updating `SV_PHASE_TRIAL(PHYSIDX)`.
- **Layer 2 (U2/U4):** Evaluates degraded linear elasticity, forming $\mathbf{F}_{\text{int, UEL}} = \int \mathbf{B}^T \mathbf{\sigma}_{\text{mech}} d\Omega$ and $\mathbf{K}_{\text{UEL}} = \int \mathbf{B}^T \mathbf{D}_{\text{mech}} \mathbf{B} d\Omega$.
- **Layer 3 (CPE4/CPE3 Companion):** Because `STRESS = 0` and `DDSDDE = 1.D-11`, Layer 3 produces $\mathbf{F}_{\text{int, UMAT}} = \mathbf{0}$ and $\mathbf{K}_{\text{UMAT}} \approx \mathbf{0}$.
- **Net System Equilibrium:** Exactly corresponds to the single UEL formulation, guaranteeing quadratic Newton convergence without double-counting stiffness or internal forces.

### 4.2 Error-Indicator (`MISESERI`) Semantics on Companion Layer
In Abaqus:
- The error indicator `MISESERI` is defined as the Mises stress discretization error associated with the recovered stress solution:
  $$e_{\sigma} = \|\mathbf{\sigma}^* - \mathbf{\sigma}_h\|_{\text{vM}}$$
- Because the companion UMAT sets $\mathbf{\sigma}_h = \mathbf{0}$ at all integration points, the standard Abaqus stress recovery algorithm operating on `ELSET=All_elem` will encounter zero stress everywhere:
  $$\mathbf{\sigma}_h \equiv \mathbf{0} \implies \mathbf{\sigma}^* \equiv \mathbf{0} \implies \text{MISESERI} \equiv 0.0$$
- **Classification of Unresolved Reference Detail:**
  In Molnár & Gravouil (2017), the third UMAT layer was designed solely to transfer phase-field and history state variables (`SDV1..SDV20`) to standard Abaqus visualization fields. In Pandey & Kumar (2025), the paper mentions generating error indicators from an initial coarse mesh analysis. If Pandey & Kumar generated `MISESERI` directly from an Abaqus job containing the third layer, either:
  1. The pre-analysis was run as a standard continuum elastic solve without UELs (exactly as realized in our Package 90 control); OR
  2. An unpublished custom companion stress transfer mechanism was used in their private code.
  In accordance with project governance rules, this aspect is formally recorded as `UNRESOLVED_REFERENCE_DETAIL`.

---

## 5. Pre-Submission Comparison Contract

The proposed Package 92 (`PK_M1_JOB1_LAYERED_COMPANION_2906.inp`) is compared against the completed standard continuum control Package 90 (`PK_M1_JOB1_CONTINUUM_MATCHED_2906.inp`):

- **Geometry:** Identical $1.0\,\text{mm} \times 1.0\,\text{mm}$ square domain with $0.5\,\text{mm}$ zero-gap sharp slit.
- **Mesh Topology:** Identical 2,906 physical elements (2,818 quads, 88 triangles) and 2,988 mesh nodes.
- **Boundary Conditions:** Identical bottom-edge roller + pinned point, top-edge tied in DOF 2 to `N_RP` (lateral-free).
- **Loading History:** Identical Step 1 ($u=0.005\,\text{mm}$, 500 increments) and Step 2 ($u=0.010\,\text{mm}$, 1000 increments).
- **Material Constants:** Identical $E=210\,\text{kN/mm}^2$, $\nu=0.3$, $G_c=2.7\times 10^{-3}\,\text{kN/mm}$, $l_0=0.0075\,\text{mm}$.
- **Output Requests:** Identical frequency (1), requesting `MISESERI, MISESAVG, S, E, EVOL` on `All_elem` and `SDV` on `umatelem`.
- **Single Intended Difference:** 3-layer UEL/UMAT architecture vs single-layer standard continuum.
