# F42-R1 Mixed 3-Node / 4-Node Element Mapping & Architecture Contract

Date: 2026-08-07  
Agent: Gemini Antigravity  
Status: `complete`  
Classification: `f42a_r1_mixed_uel_contract_corrected`  

---

## 1. Corrected User-Element Type Contract

To preserve the validated Molnár 4-node quad baseline ($U1, U2$) without breaking regression controls, the mixed-element architecture uses $U1..U4$:

| Element Role | Physics / DOFs | Node Count | Type Name | Abaqus Keyword Declaration |
|---|---|---|---|---|
| **Quad Phase Field** | Phase ($\phi$, DOF 3) | 4 | `U1` | `*User Element, nodes=4, type=U1, properties=3, coordinates=2, VARIABLES=8` |
| **Quad Displacement** | Displacement ($u_x, u_y$, DOFs 1,2) | 4 | `U2` | `*User Element, nodes=4, type=U2, properties=4, coordinates=2, VARIABLES=56` |
| **Triangle Phase Field** | Phase ($\phi$, DOF 3) | 3 | `U3` | `*User Element, nodes=3, type=U3, properties=3, coordinates=2, VARIABLES=6` |
| **Triangle Displacement**| Displacement ($u_x, u_y$, DOFs 1,2) | 3 | `U4` | `*User Element, nodes=3, type=U4, properties=4, coordinates=2, VARIABLES=42` |
| **Quad Facsimile** | Elastic / Output | 4 | `CPE4` | `*Element, type=CPE4, elset=UMAT_QUAD` |
| **Triangle Facsimile** | Elastic / Output | 3 | `CPE3` | `*Element, type=CPE3, elset=UMAT_TRI` |

### Abaqus Fortran `JTYPE` Dispatch Rules
- `type=U1` $\rightarrow$ `JTYPE = 1` (Quad Phase)
- `type=U2` $\rightarrow$ `JTYPE = 2` (Quad Displacement)
- `type=U3` $\rightarrow$ `JTYPE = 3` (Triangle Phase)
- `type=U4` $\rightarrow$ `JTYPE = 4` (Triangle Displacement)

---

## 2. 3-Point Symmetric Triangle Integration Rule (Degree-2 Exact)

To exactly integrate the quadratic phase-field reaction term $N_i N_j$, a symmetric 3-point quadrature rule is implemented for 3-node triangular elements:

| Point ($k$) | Natural Coords $(\xi_k, \eta_k)$ | Weight ($w_k$) | Physical Integration Weight ($w_{phys, k}$) |
|---|---|---|---|
| **1** | $(1/6, 1/6)$ | $1/6$ | $\frac{1}{6} \det(\mathbf{J}) t$ |
| **2** | $(2/3, 1/6)$ | $1/6$ | $\frac{1}{6} \det(\mathbf{J}) t$ |
| **3** | $(1/6, 2/3)$ | $1/6$ | $\frac{1}{6} \det(\mathbf{J}) t$ |

- **Sum of Weights**: $w_1 + w_2 + w_3 = 1/2$ (area of reference unit triangle).
- **State Slots**: $NPT = 1..3$. Slot 4 in `USRVAR(N_ELEM, NSTV, 4)` remains unused for triangles.
- `U3` `VARIABLES = 3 * NSTVTO = 6`.
- `U4` `VARIABLES = 3 * NSTVTT = 42`.

---

## 3. Physical Element Layer Offset Scheme

Let $N_{phys}$ be the total number of physical remeshed elements ($1 \le p \le N_{phys}$).
Three non-overlapping element label layers are created:

1. **Phase Layer**: `label = p` ($1 \le p \le N_{phys}$)
   - Quad $\rightarrow U1$, Triangle $\rightarrow U3$.
2. **Displacement Layer**: `label = N_phys + p`
   - Quad $\rightarrow U2$, Triangle $\rightarrow U4$.
3. **Facsimile Layer**: `label = 2 * N_phys + p`
   - Quad $\rightarrow CPE4$, Triangle $\rightarrow CPE3$.

### Subroutine Indexing Formulas
- Phase physical index: `NELEMAN = JELEM`
- Displacement physical index: `NELEMAN = JELEM - NPHYS`
- UMAT facsimile physical index: `NELEMAN = NOEL - 2 * NPHYS`

---

## 4. Aggregate Element Sets
- `PHASE`: All $U1$ and $U3$ element labels ($1 .. N_{phys}$)
- `DISP`: All $U2$ and $U4$ element labels ($N_{phys}+1 .. 2 N_{phys}$)
- `UMATELEM`: All $CPE4$ and $CPE3$ facsimile labels ($2 N_{phys}+1 .. 3 N_{phys}$)
- `All_elem`: Points to `UMATELEM` facsimile output layer.
