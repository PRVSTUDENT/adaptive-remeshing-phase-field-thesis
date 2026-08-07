# F42C Quadrilateral CPE4 / UMAT Facsimile Contract Audit

## 1. Element Layering Architecture
The established 3-layer formulation (Molnár et al. baseline & Stage F models) uses three overlapping element layers sharing identical nodal coordinates:
- **Layer 1 (Phase UEL, `U1` / `U3`)**: Computes phase field evolution $\phi$. Element labels $1 \dots N_{phys}$.
- **Layer 2 (Displacement UEL, `U2` / `U4`)**: Computes degraded mechanical displacement $\mathbf{u}$ and stiffness. Element labels $N_{phys}+1 \dots 2 N_{phys}$.
- **Layer 3 (Facsimile Layer, `CPE4` / `CPE3`)**: Standard Abaqus element layer assigned a `*USER MATERIAL`. Element labels $2 N_{phys}+1 \dots 3 N_{phys}$.

## 2. Element Label Index Mapping
- **Phase UEL Index**: $\text{PHYSIDX} = \text{JELEM}$
- **Displacement UEL Index**: $\text{PHYSIDX} = \text{JELEM} - N_{phys}$
- **Facsimile UMAT Index**: $\text{PHYSIDX} = \text{NOEL} - 2 N_{phys}$

## 3. Quadrilateral Integration-Point Mapping (CPE4)
- **Quad UEL Integration Points**: 4 Gauss points ($\pm 1/\sqrt{3}, \pm 1/\sqrt{3}$).
- **CPE4 Facsimile Integration Points**: 4 Gauss points.
- **Mapping**: Direct 1-to-1 ordering (`NPT_IDX = NPT` for $NPT \in [1, 4]$).
- **COMMON Storage**: `USRVAR(PHYSIDX, SDV_ID, NPT)` shared directly via `COMMON /KUSER/ USRVAR(N_CAPACITY, 18, 4)`.

## 4. Mechanical Role of CPE4 Facsimile
- **Mechanical Role**: **Mechanically Passive (Dummy Stiffness)**.
- **Material Parameters**: `*USER MATERIAL, CONSTANTS=2` with $E_{facsimile} = 1.0 \times 10^{-11}$ GPa and $\nu = 0.3$.
- **Stiffness & Force Impact**: The facsimile layer contributes negligible stiffness ($\sim 10^{-16} \times \mathbf{K}_{real}$) and negligible internal nodal forces. Layer 2 (`U2` / `U4`) provides 100% of the true physical mechanical stiffness and degradation.
- **Primary Purpose**: Facilitates ODB field output, visualization of state variables (SDVs), stress/strain tensor output, and integration with post-processing tools.
