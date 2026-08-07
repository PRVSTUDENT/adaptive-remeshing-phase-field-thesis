# F43A Stage-C Two-Model Architecture & MISESERI Scientific Interpretation

## 1. Frozen Benchmark Baseline

- **Benchmark Name**: Pandey-Kumar Mode-II Asymmetric Shear Single-Edge Notch Benchmark
- **Source Deck**: [`models/generated/mode_ii/miseseri_preanalysis_corrected_pbs/ModeII_MISESERI_preanalysis.inp`](file:///d:/Master%20thesis/Adaptive%20remeshing/models/generated/mode_ii/miseseri_preanalysis_corrected_pbs/ModeII_MISESERI_preanalysis.inp)
- **Material**: Young's Modulus $E = 210000.0\text{ MPa}$, Poisson's Ratio $\nu = 0.3$, $G_c = 2.7\text{ N/mm}$
- **Length Scale**: $l_0 = 0.015\text{ mm}$
- **Loading & BCs**: Fixed bottom boundary ($u_x = u_y = 0$), shear displacement $u_x = 0.001\text{ mm}$ on top boundary. Pre-existing notch along $y = 0, x \in [-0.5, 0.0)\text{ mm}$.
- **Coarse Mesh**: $H_0$ coarse continuum mesh ($N_{\text{elem}} = 3930$ CPE4 elements).
- **Uniform Reference**: $H_1$ ($h = 0.01\text{ mm}$) and $H_2$ ($h = 0.0075\text{ mm}$) uniform reference meshes.

## 2. Two-Model Architecture Specification

```
                          STAGE-C WORKFLOW
                          
   [Model A: F43PRE1]                                [Model B: F43DRY1 / UEL Solve]
   Standard Continuum Mesh                           Layered Phase-Field UEL Mesh
   (CPE4 / CPE3 Elements)                            (U1/U3 + U2/U4 + CPE4/CPE3)
   Real Physical Stress & Stiffness                  Passive Facsimiles (E = 1e-11)
          |                                                       ^
          v                                                       |
   Outputs: S, MISESERI, MISESAVG, EVOL                           |
          |                                                       |
          +---> Abaqus Native Remesh Driver (F43REM1)             |
                         |                                        |
                         v                                        |
                  Refined Mixed Deck                              |
                         |                                        |
                         +---> Mixed UEL Rebuilder (f42_deck_rebuilder.py)
```

### Model A: Remeshing Indicator Model (`F43PRE1`)
- **Elements**: Standard Abaqus plane-strain continuum elements (`CPE4`, `CPE3`).
- **Material**: Real physical elasticity ($E = 210000.0\text{ MPa}$, $\nu = 0.3$).
- **Outputs**: `S`, `MISESERI`, `MISESAVG`, `EVOL`, `U`, `RF`.
- **Function**: Provide clean physical stress discretization error fields to Abaqus native adaptive-remeshing rules.

### Model B: Final Refined Phase-Field Model (`F43DRY1` / Phase-Field Solve)
- **Elements**: 3-layer architecture:
  - Layer 1 (Phase): `U1` (Quad) / `U3` (Triangle)
  - Layer 2 (Displacement): `U2` (Quad) / `U4` (Triangle)
  - Layer 3 (Facsimile): `CPE4` (Quad) / `CPE3` (Triangle) UMAT
- **Material**: Facsimile layer uses passive dummy stiffness ($E_{\text{dummy}} = 10^{-11}\text{ MPa}$). True mechanics provided by U2/U4.
- **Function**: Execute phase-field fracture solution on the refined mixed mesh.

## 3. MISESERI Scientific Interpretation

- **Definition**: `MISESERI` represents the Mises stress discretization error estimate computed by Abaqus from element-boundary stress misfits relative to `MISESAVG`.
- **Scope**: It is strictly a **mechanical stress-discretization error indicator**.
- **Prohibitions**:
  - `MISESERI` is **NOT** a phase-field damage variable $\phi$.
  - `MISESERI` is **NOT** a crack tip indicator or fracture evolution metric.
  - `MISESERI` must **NOT** be evaluated on passive facsimile elements (which have zero physical stress).
