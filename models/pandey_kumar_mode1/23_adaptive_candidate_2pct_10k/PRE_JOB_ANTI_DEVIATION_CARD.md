# Pre-Job Anti-Deviation & Governance Verification Card

**Candidate Name**: `PK_MODE1_ADAPT_2PCT_10K_ENERGY`  
**Package Path**: `models/pandey_kumar_mode1/23_adaptive_candidate_2pct_10k/`  
**Timestamp**: 2026-10-02T14:40:00+02:00  
**Phase / Gate**: Gate-6B Mode-I Adaptive Candidate Qualification  
**Classification**: `DATACHECK_PASSED_READY_AFTER_CORRECTED_S1_ENERGY_QUALIFICATION`  
**Authorization Status**: `authorized: false` (strictly unsubmitted; awaiting post-1409734 review)

---

## 1. Governance Invariant Checklist

| Invariant Item | Target Specification | Candidate Specification | Audit Result |
| :--- | :--- | :--- | :---: |
| **Physical Geometry** | $1.0 \times 1.0\,\text{mm}$ square plate, slit $y=0.5, x \in [0.0, 0.5]$ | $1.0 \times 1.0\,\text{mm}$ square plate, slit $y=0.5, x \in [0.0, 0.5]$ | **MATCH** |
| **Mesh Provenance** | Mode-I Step-1 Pre-Analysis Remesh ($\text{errorTarget}=2.0\%$) | 10,253 finite elements (9,952 quads, 301 tris) | **MATCH** |
| **User Subroutine** | `f42_mixed_uel.for` (`CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6`) | `f42_mixed_uel.for` (`CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6`) | **MATCH** |
| **Constitutive & PFM Parameters** | $E=210\,\text{GPa}, \nu=0.3, G_c=2.7\times 10^{-3}\,\text{kN/mm}, l_0=0.0075\,\text{mm}, \eta=10^{-7}$ | $E=210\,\text{GPa}, \nu=0.3, G_c=2.7\times 10^{-3}\,\text{kN/mm}, l_0=0.0075\,\text{mm}, \eta=10^{-7}$ | **MATCH** |
| **Physical Quad Count $N_{\text{phys}}$** | $10253.0$ passed into UEL & UMAT PROPS | `10253.0` in UEL PROPERTY & UMAT constants | **MATCH** |
| **Solution Variables** | `*DEPVAR 20` (SDV17: $E_{\text{frac}}$, SDV18: $E_{\text{elas}}$, SDV19: $E_{\text{tot}}$, SDV20: status) | `*DEPVAR 20` | **MATCH** |
| **Element Output** | `*ELEMENT OUTPUT, ELSET=All_elem` -> `SDV` | `*ELEMENT OUTPUT, ELSET=All_elem` -> `SDV` | **MATCH** |
| **Boundary Conditions** | Bottom $u_2=0$, Pin $(0,0)$ $u_1=0$, Top $u_1=0$, RP kinematic coupling to Top $u_2$ | Bottom $u_2=0$, Pin $(0,0)$ $u_1=0$, Top $u_1=0$, RP kinematic coupling to Top $u_2$ | **MATCH** |
| **Loading Steps** | Step-1: $u \to 0.0050\,\text{mm}$ ($\Delta u = 5\times 10^{-4}$), Step-2: $u \to 0.0100\,\text{mm}$ ($\Delta u = 2\times 10^{-4}$) | Step-1: $u \to 0.0050\,\text{mm}$ ($\Delta u = 5\times 10^{-4}$), Step-2: $u \to 0.0100\,\text{mm}$ ($\Delta u = 2\times 10^{-4}$) | **MATCH** |
| **Execution Architecture** | 1-CPU serial shared-memory thread (`cpus=1`, `memory=16gb`) | 1-CPU serial shared-memory thread (`cpus=1`, `memory=16gb`) | **MATCH** |
| **Dual-Channel Notifications** | `#PBS -m abe` + `job_notifications.sh` terminal traps | `#PBS -m abe` + `job_notifications.sh` terminal traps | **MATCH** |

---

## 2. File Verification Hashes

- `PK_MODE1_ADAPT_2PCT_10K_ENERGY.inp`: `F9B9BB907DA83AFCADCF50D58528BDE8029D5C4277D5012967940A04C653EBA9`
- `f42_mixed_uel.for`: `CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6`
- `extract_authoritative_mode1_energy_complete.py`: `C064C4D789547565985FB5E72E0124D9FD35B57A2DBB9D6E7711B8006E1B6B22`

---

## 3. Post-Qualification Execution Gate

1. This candidate has successfully passed preflight datacheck qualification.
2. It remains **strictly unsubmitted** (`authorized: false`).
3. Execution authorization will only be considered after completion and scientific review of baseline reference Job `1409734.mmaster02` (`PK_M1_REF15K_ENERGY`).
