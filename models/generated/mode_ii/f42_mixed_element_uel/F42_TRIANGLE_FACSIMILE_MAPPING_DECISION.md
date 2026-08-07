# F42 Triangle Facsimile Mapping & Integration Point Architectural Decision Note

Date: 2026-08-07  
Agent: Gemini Antigravity  
Status: `documented_decision_pending_core_uel_verification`  
Classification: `f42_facsimile_integration_mismatch_architecture_design`  

---

## 1. Context & Technical Problem

In Task F42A-R1, the 3-node triangular phase-field UEL ($U3$) and displacement UEL ($U4$) were upgraded from a single centroidal point to a **3-point symmetric degree-2 exact quadrature rule** to integrate the quadratic phase-field reaction term $N_i N_j$ and consistent mass matrix $\frac{A_e}{12} \left[\begin{array}{ccc} 2 & 1 & 1 \\ 1 & 2 & 1 \\ 1 & 1 & 2 \end{array}\right]$ without approximation.

However, the standard Abaqus linear triangular continuum element (`CPE3`) is a constant-strain element that evaluates stress and state variables at **only 1 centroidal integration point** (`NPT=1`).

Therefore, a direct 1-to-1 mapping of integration point indices (`NPT=1..3`) between UEL and `UMAT` facsimile is physically and architecturally impossible.

---

## 2. Proposed Architecture Options for Future Facsimile Integration

To ensure the facsimile output layer (`CPE3` / `UMATELEM`) provides accurate post-processing visualization and `MISESERI` error indicators without contaminating the UEL numerical solution:

### Option A: Centroidal Element-Average State Slot (`USRVAR(..., ..., 4)`)
- Store the centroid-averaged state variables in slot 4 of `USRVAR`:
  $$\bar{\phi} = \frac{1}{3} \sum_{k=1}^3 \phi_k, \quad \bar{H} = \max_{k=1..3}(H_k) \text{ or } \frac{1}{3}\sum_{k=1}^3 H_k$$
- `UMAT` reads slot 4 when `NPT=1`.

### Option B: On-the-Fly Aggregation in `UMAT`
- `UMAT` reads all three quadrature point slots (`NPT=1..3`) from `USRVAR` and computes the element average directly during visualization output generation.

### Option C: Passive Facsimile Stiffness Layer
- Ensure the facsimile layer (`CPE3`) does not duplicate elastic stiffness $\mathbf{C}$ when solved alongside $U4$. In production, `UMATELEM` carries dummy/vanishing material stiffness or operates strictly as a visualization mesh.

---

## 3. Staging Sequence

To strictly separate physical UEL formulation correctness from output visualization mapping:

1. **Phase 1 (Task F42B)**: Qualify core $U3$ Phase and $U4$ Displacement UELs on a single triangle **without** `CPE3` or `UMAT`.
2. **Phase 2 (Task F42C)**: Implement and qualify the selected facsimile mapping option (Option A or B) after core UEL verification succeeds.
