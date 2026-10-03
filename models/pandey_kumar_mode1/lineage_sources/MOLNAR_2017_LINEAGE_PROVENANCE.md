# Primary-Source Provenance: Molnár & Gravouil (2017) Supplementary Codebase

**Document:** `MOLNAR_2017_LINEAGE_PROVENANCE.md`  
**Location:** `models/pandey_kumar_mode1/lineage_sources/`  
**Date Archived:** `2026-10-03`  
**Classification:** `PRIMARY_LITERATURE_LINEAGE_ARCHIVE`  

---

## 1. Bibliographic & Source Metadata

- **Authors:** Gergely Molnár, Anthony Gravouil
- **Title:** *2D and 3D Abaqus implementation of a robust staggered phase-field solution for finite strain brittle fracture*
- **Journal:** *Computer Methods in Applied Mechanics and Engineering*, Vol. 320, pp. 41–75 (2017)
- **DOI:** [`10.1016/j.cma.2017.03.011`](https://doi.org/10.1016/j.cma.2017.03.011)
- **Supplementary File:** `SingleNotch.for` (from Supplementary Material `mmc1.zip`, `02_Single_Notch_Tension/`)
- **Archived Path in Repository:** `models/pandey_kumar_mode1/lineage_sources/SingleNotch.for`
- **SHA-256 Checksum:** `18944E5BB2A3B7973FD0D4BFF03F8E078EEF667965343D8A29156D093F53F5F1`

---

## 2. Line References & Subroutine Mechanics

The companion user material (`UMAT`) is defined in `SingleNotch.for` at **Lines 519–584**:

1. **Material Properties Read:**
   - Line 539: `EMOD = PROPS(1)` ($E_{\text{dummy}} = 10^{-11}$)
   - Line 540: `ENU = PROPS(2)` ($\nu = 0.3$)
2. **Elastic Moduli & Tangent Calculation:**
   - Lines 541–562: Calculates Lamé constants $\mu = \text{EG}$, $\lambda = \text{ELAM}$ and populates `DDSDDE(NTENS, NTENS)` for isotropic linear elasticity.
3. **Incremental Cauchy Stress Update:**
   - Lines 566–570:
     ```fortran
            DO K1=1, NTENS
             DO K2=1, NTENS
              STRESS(K2)=STRESS(K2)+DDSDDE(K2, K1)*DSTRAN(K1)
             END DO
            END DO
     ```
4. **State Variable Exchange from UEL Common Block:**
   - Lines 579–581: Transfers state variables from `COMMON/KUSER/USRVAR` to `STATEV(I)` for standard visualization.

---

## 3. Role in Thesis & Diagnostic Governance

In the Mode-I benchmark investigation (Pandey & Kumar, 2025, Section 3), the authors adopt this 3-layer architecture.
- Package 93 (`f42_mixed_uel_inf_stress.for`) implements this exact linear elastic stress update as a project diagnostic (`MOLNAR_GRAVOUIL_LINEAGE_SUPPORTED_PROJECT_DIAGNOSTIC`).
- The exact companion-UMAT implementation inside Pandey & Kumar (2025) is maintained as `UNRESOLVED_REFERENCE_DETAIL`.
