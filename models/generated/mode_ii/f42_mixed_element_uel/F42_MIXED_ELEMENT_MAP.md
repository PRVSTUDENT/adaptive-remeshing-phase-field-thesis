# F42 Mixed 3-Node / 4-Node Element Mapping & Architecture Contract

Date: 2026-08-07  
Agent: Gemini Antigravity  
Status: `complete`  
Classification: `triangle_uel_reference_implementation_not_yet_resolved`  

---

## 1. Explicit User-Element Type Contract

To avoid collision with existing 4-node UEL declarations ($U1, U2, U3, U4$), the mixed-element architecture defines four distinct user element types:

| Element Role | Physics / DOFs | Node Count | Type Name | Abaqus Keyword Declaration |
|---|---|---|---|---|
| **Quad Phase Field** | Phase ($\phi$, DOF 3) | 4 | `U11` | `*User element, nodes=4, type=U11, properties=3, coordinates=2, VARIABLES=8` |
| **Quad Displacement** | Displacement ($u_x, u_y$, DOFs 1,2) | 4 | `U12` | `*User element, nodes=4, type=U12, properties=4, coordinates=2, VARIABLES=56` |
| **Triangle Phase Field** | Phase ($\phi$, DOF 3) | 3 | `U21` | `*User element, nodes=3, type=U21, properties=3, coordinates=2, VARIABLES=8` |
| **Triangle Displacement**| Displacement ($u_x, u_y$, DOFs 1,2) | 3 | `U22` | `*User element, nodes=3, type=U22, properties=4, coordinates=2, VARIABLES=56` |
| **Quad Facsimile** | Elastic / Output | 4 | `CPE4` | `*Element, type=CPE4, elset=All_elem_quad` |
| **Triangle Facsimile** | Elastic / Output | 3 | `CPE3` | `*Element, type=CPE3, elset=All_elem_tri` |

---

## 2. Mathematical Mapping: 4-Node Quad vs 3-Node Triangle

| Mathematical Quantity | Existing 4-Node Bilinear Quad (`U11`/`U12`) | Proposed 3-Node Linear Triangle (`U21`/`U22`) |
|---|---|---|
| **Nodes ($NNODE$)** | 4 | 3 |
| **DOFs per Node** | 1 (Phase) or 2 (Displacement) | 1 (Phase) or 2 (Displacement) |
| **Total DOFs ($NDOFEL$)** | 4 (Phase) or 8 (Displacement) | 3 (Phase) or 6 (Displacement) |
| **Natural Coordinates** | $\xi \in [-1, 1], \eta \in [-1, 1]$ | $L_1 = 1 - \xi - \eta, L_2 = \xi, L_3 = \eta, (\xi \ge 0, \eta \ge 0, \xi+\eta \le 1)$ |
| **Shape Functions ($N_i$)** | $N_1 = \frac{1}{4}(1-\xi)(1-\eta)$<br>$N_2 = \frac{1}{4}(1+\xi)(1-\eta)$<br>$N_3 = \frac{1}{4}(1+\xi)(1+\eta)$<br>$N_4 = \frac{1}{4}(1-\xi)(1+\eta)$ | $N_1 = 1 - \xi - \eta$<br>$N_2 = \xi$<br>$N_3 = \eta$ |
| **Derivatives ($\partial N_i / \partial \xi, \partial N_i / \partial \eta$)** | Bilinear functions of $(\xi, \eta)$ | Constant: $\left[\begin{array}{cc} -1 & -1 \\ +1 & 0 \\ 0 & +1 \end{array}\right]$ |
| **Jacobian ($\mathbf{J}$)** | $2 \times 2$ spatially variable | $2 \times 2$ constant: $J_{11} = x_2 - x_1, J_{12} = y_2 - y_1, J_{21} = x_3 - x_1, J_{22} = y_3 - y_1$<br>$\det(\mathbf{J}) = 2 A_e$ |
| **Integration Quadrature** | $2 \times 2 = 4$ Gauss points | 1-point centroidal $(\xi=1/3, \eta=1/3, w=1/2)$ |
| **Integration Weight** | $w_i = 1.0$ | $w = 0.5 \times \det(\mathbf{J}) \times \text{thickness} = A_e t$ |
| **B-Matrix Dimension** | Phase: $2 \times 4$<br>Displacement: $3 \times 8$ | Phase: $2 \times 3$<br>Displacement: $3 \times 6$ |
| **Stiffness Matrix ($AMATRX$)** | $4 \times 4$ (Phase) or $8 \times 8$ (Displacement) | $3 \times 3$ (Phase) or $6 \times 6$ (Displacement) |
| **Residual Vector ($RHS$)** | $4 \times 1$ (Phase) or $8 \times 1$ (Displacement) | $3 \times 1$ (Phase) or $6 \times 1$ (Displacement) |

---

## 3. State Variable Storage Scheme (`COMMON/KUSER` & `USRVAR`)

- **Array Dimension**: `COMMON/KUSER/USRVAR(N_ELEM, NSTV, 4)`
- **Indexing Rules**:
  - **4-Node Quads**: Use all 4 integration point slots (`NPT = 1..4`).
  - **3-Node Triangles**: Use slot 1 (`NPT = 1`) for centroidal integration point; slots 2..4 remain unused (zeroed).
- **Backwards Compatibility**: Guarantees that `USRVAR` memory allocation and indexing for existing quad elements remains 100% untouched.

---

## 4. Input Deck Rebuilder Specifications

The deck rebuilder parses `Job-2.inp` from Abaqus adaptive remeshing:
1. Identifies element sets:
   - Elements with 4 nodes $\rightarrow$ classified as `CPE4`.
   - Elements with 3 nodes $\rightarrow$ classified as `CPE3`.
2. Generates corresponding layered UEL definitions:
   - `U11` (Phase Quad) & `U12` (Disp Quad) for 4-node elements.
   - `U21` (Phase Tri) & `U22` (Disp Tri) for 3-node elements.
   - Facsimile output layers `All_elem_quad` (`CPE4`) and `All_elem_tri` (`CPE3`).
3. Re-applies boundary conditions, UEL properties, step controls, and `MISESERI` output requests.
