# Decision Questions for the Supervisor

**Meeting Date:** Thursday, 17 September 2026  
**Candidate:** Pruthviraja Reddy Vandavagali (Matr. Nr. 68865)  
**Supervisors:** Prof. Dipl.-Ing. Björn Kiefer, Ph.D. & Dr.-Ing. Stephan Roth (IMFD)  
**Subject:** Closure of Gate 5 (Mode-I Benchmark Reproduction)

---

### Context Summary
1. **Priority Question A (Stiffness Defect):** Definitive root cause isolated (Abaqus `pre` 16-entry `*NSET` card limit deleting 134 bottom nodes, allowing up to $\approx 48.34\%$ stroke vertical lift). Resolved by card line wrapping. Full-fracture nominal 1% (Job `1404933`) recovers reference stiffness within $-0.09\%$ ($K_0 \approx 137.821\,\text{kN/mm}$ vs $137.946\,\text{kN/mm}$) and peak load within $-1.64\%$ ($F_{\max} = 0.745325\,\text{kN}$). **Status: RESOLVED AND CLOSED.**
2. **Priority Question B (Element Count Discrepancy):** The literal published rule (`errorTarget=1.0`, `All_elem`) yields $71{,}320$ finite elements identically across Abaqus 2019–2023. Spatial decomposition proves $87.3\%$ of elements ($62{,}259$) are placed in transition and far-field regions to meet the 1% error target. An exhaustive 15-factor audit eliminates all accessible software parameters. The cause of the reported $\approx 13{,}941$ mesh is an unpublished implementation detail. **Status: AUDIT COMPLETE / EXTERNAL INFO REQUIRED.**

---

### Decisions Required

We request your decision on the preferred scientific pathway to conclude Gate 5:

#### **Option A: Accept Gate 5 as Externally Under-Specified (Recommended)**
- Accept Gate 5 as externally under-specified based on our exhaustive 15-factor OFAT audit.
- Retain $71{,}320$ finite elements as the verified publication-literal reconstruction under $\texttt{errorTarget}=1.0$ and whole-specimen remeshing.
- Document $\approx 13{,}941$ as unresolved due to missing publication information.
- Document the regional distribution ($87.3\%$ outside the crack corridor) as an authentic finding on native Abaqus `UNIFORM_ERROR` refinement.
- Proceed strictly with Mode-I thesis synthesis and documentation pending further supervisor direction.

#### **Option B: Authorize Transmission of Author Reproducibility Inquiry**
- Approve sending our finalized 6-question reproducibility inquiry to the authors (Dr. Anshul Pandey and Dr. Sachin Kumar).
- Keep Gate 5 open pending the author response.
- Note: No further target-tuning exercises are authorized; $\texttt{errorTarget}=1.0$ remains the publication-literal reference and numerical proximity at 2% is not evidence of parameter identity.

---

### Mandatory Scope Freeze Notice
Under **both** Option A and Option B, Gate 7 (ABAQUSER integration), Mode-II shear benchmarks, multi-step state transfer, and higher-complexity modeling remain **explicitly ON HOLD** unless separately authorized by the supervisors.

The author inquiry letter remains **strictly UNSENT** awaiting your written approval.
