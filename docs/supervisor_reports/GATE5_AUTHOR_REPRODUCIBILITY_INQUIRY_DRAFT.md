# Gate 5: Corresponding-Author Reproducibility Inquiry Draft (Send-Ready, Unsent)

**Document Reference:** `GATE5_AUTHOR_REPRODUCIBILITY_INQUIRY_DRAFT.md`  
**Date:** September 14, 2026  
**Status:** `AUTHOR_INFORMATION_REQUEST_READY_FOR_HUMAN_APPROVAL_UNSENT`  
**Target Recipient:** Dr. Sachin Kumar (Corresponding Author, `sachin@iitrpr.ac.in`), Department of Mechanical Engineering, Indian Institute of Technology Ropar, Punjab, India  
**Primary Reference:** Pandey, A., & Kumar, S. (2025). "A Simple and Robust Mesh Refinement Implementation in Abaqus for Phase Field Modelling of Brittle Fracture." *Computer Modeling in Engineering & Sciences* (CMES), Vol. 144, No. 3, pp. 3251–3286. DOI: [10.32604/cmes.2025.067858](https://doi.org/10.32604/cmes.2025.067858)  
**Governing Directive:** This document is prepared strictly for internal thesis documentation and supervisor review. **DO NOT TRANSMIT** without prior explicit written human/supervisor authorization.

---

## 1. Executive Context & Purpose of Inquiry

In our master's thesis investigation into adaptive mesh refinement for phase-field fracture mechanics, we have systematically reconstructed and verified the native Abaqus Python adaptive remeshing workflow published in Pandey & Kumar (2025). 

While the qualitative refinement mechanisms, error indicator distributions (MISESERI), user-subroutine formulations (UEL/UMAT), and fixed-mesh benchmark anchors have been successfully verified, a systematic discrepancy remains between the published Mode-I nominal benchmark adapted element count ($\sim 13,941$ finite elements; Section 4.1, p. 3265, Line 1027, Fig. 5) and the literal execution of the published code (Listing 1, p. 3262), which deterministically produces **71,320 finite elements** (or **55,761 finite elements** under unconstrained top-edge $u_1$).

An exhaustive local and high-performance computing audit has demonstrated:
1. **Four-Generation Release Invariance:** Executing Listing 1 across Abaqus 2019 GA, 2021.HF26, 2022 GA, and 2023.HF4 on Linux generates bit-for-bit identical substantive mesh topology and geometry ($71,320$ finite elements: $69,443$ CPE4 + $1,877$ CPE3, $70,845$ nodes, with identical normalized coordinate hash `116f2e2042afddf8af2d38bd51147c2cd135ee93304d586b632cdb404fca8e4e`).
2. **Platform & Release Confounding:** Windows Abaqus 2024 GA produces $71,904$ finite elements (+0.82% variance vs Linux 2019–2023), confirming that accessible software version and platform variations do not explain the $\sim 13,941$ literature count (`RELEASE_PLUS_PLATFORM_CONFOUNDED`).
3. **Boundary Condition Sensitivity:** Unconstraining the top-edge horizontal displacement ($u_1 = \text{Free}$) reduces far-field refinement due to Poisson contraction relief, yielding $55,761$ elements ($-21.8\%$), which still remains $>4.0\times$ the published cardinality (`TESTED_NO_MATERIAL_EFFECT`).
4. **Publication Linkage:** Listing 1 hardcodes `errorTarget=1.0`, but the Section 4.1 text invokes the workflow without an explicit parameter override (`PUBLICATION_LINKAGE_AMBIGUOUS`).

Consequently, this minimal, professional technical inquiry has been prepared to request the specific execution details required for exact reproduction.

---

## 2. Accompanying Review Figure (For Human/Supervisor Review Only)

The following lightweight comparative figure has been generated and saved locally for supervisor inspection:
- **Image File:** [`docs/thesis/figures/figure_gate5_author_inquiry_mesh_comparison.png`](file:///D:/Master%20thesis/Adaptive%20remeshing/docs/thesis/figures/figure_gate5_author_inquiry_mesh_comparison.png)

![Gate 5 Author Inquiry Comparison Figure](file:///D:/Master%20thesis/Adaptive%20remeshing/docs/thesis/figures/figure_gate5_author_inquiry_mesh_comparison.png)

*Caption: Side-by-side comparison of the published Mode-I benchmark reported cardinality (~13,941 finite elements, Section 4.1 / Fig. 5) and the reconstructed Listing 1 execution (71,320 finite elements), alongside the numerical invariance audit across Abaqus releases (2019–2024).*

---

## 3. Unsent Plain-Text Email Draft to Corresponding Author

```text
Subject: Technical reproduction query regarding adaptive mesh refinement in 2D phase-field fracture (CMES 2025)

Dear Dr. Kumar,

I hope this email finds you well.

I am a graduate researcher at TU Bergakademie Freiberg working on adaptive remeshing formulations for phase-field fracture mechanics. We have been studying your recent paper with great interest:

"A Simple and Robust Mesh Refinement Implementation in Abaqus for Phase Field Modelling of Brittle Fracture" (Computer Modeling in Engineering & Sciences, vol. 144, no. 3, pp. 3251–3286, 2025, DOI: 10.32604/cmes.2025.067858).

Your work provides an elegant demonstration of using Abaqus' native adaptive remeshing framework for phase-field problems. In our work, we have reconstructed the complete workflow—including the coarse elastic pre-analysis, MISESERI stress recovery error estimation, and the layered UEL/UMAT implementation.

We have encountered a numerical reproduction question regarding the nominal Mode-I adaptive benchmark in Section 4.1 (Figure 5), where an adapted element count of approximately 13,941 finite elements is reported.

When we execute the native remeshing workflow following Listing 1 verbatim (errorTarget=1.0, errorIndicator='MISESERI', errorMeasure='UNIFORM_ERROR', minSize=0.001 mm, maxSize=0.020 mm, refinementFactor=10, coarseningFactor=NOT_ALLOWED, applied across the whole specimen geometry Plate.faces), the resulting adapted mesh deterministically contains exactly 71,320 finite elements (69,443 CPE4 + 1,877 CPE3 elements, 70,845 nodes).

We have verified that this 71,320-element mesh topology and geometry is invariant across Abaqus 2019 GA, 2021.HF26, 2022 GA, and 2023.HF4 on Linux (yielding identical node coordinates and element connectivities), and produces 71,904 elements on Abaqus 2024 GA under Windows (+0.82% variance). Furthermore, unconstraining the horizontal top-edge displacement yields 55,761 elements.

To help us establish an exact, rigorous scientific reproduction for our thesis, could you kindly clarify the following 6 specific configuration details used for the ~13,941-element Mode-I simulation:

1. What were the exact initial coarse-mesh element and node counts of the unrefined plate before remeshing?
2. Which Abaqus/CAE mesh controls and seeding settings were used for that initial coarse mesh (e.g., element shape, meshing technique/algorithm, and any non-default curvature or deviation factors)?
3. Which Abaqus release/hotfix version and operating system were used for the published calculations?
4. What were the precise boundary conditions applied during the pre-analysis step on the top and bottom edges (e.g., was horizontal displacement u1 constrained or free on the top edge)?
5. Was the RemeshingRule applied to the entire specimen (faces set 'All_elem') as shown in Listing 1, or was an unstated sub-domain partition or corridor used to restrict refinement?
6. In Section 3.3 (Listing 2, p. 3263), an illustrative UEL/UMAT deck snippet reports N_el = 14,804. Could you briefly clarify how this realization relates to the ~13,941-element mesh in Section 4.1?

Thank you very much for your time, assistance, and for publishing this valuable methodology.

Sincerely,

[Author Name / Research Group]
Institute of Mechanics and Fluid Dynamics (IMFD)
TU Bergakademie Freiberg, Germany
```

---

## 4. Epistemic Classification & Information Boundary

| Question # | Target Parameter | Status in Published Literature | Status in Our Reconstruction |
| :-: | :--- | :--- | :--- |
| **Q1** | Initial coarse element & node counts | Omitted from Section 4.1 text (only $h_{\text{cms}} = 0.02\,\text{mm}$ stated) | $N_{\text{el}} = 2,906$ ($2,818$ CPE4 + $88$ CPE3), $N_{\text{nod}} = 2,988$ |
| **Q2** | Coarse mesher algorithm & seed controls | Omitted from text and figures | Verified default: `QUAD_DOMINATED` + `ADVANCING_FRONT` ($minSizeFactor=0.1$, $devFactor=0.1$) |
| **Q3** | Software version & OS | Omitted (Abaqus version not identified in text) | Invariance across Linux 2019/2021/2022/2023 (71,320 el) verified; Windows 2024 GA confounded (71,904 el) |
| **Q4** | Boundary conditions in pre-analysis ($u_1$ top edge) | Omitted from Section 4.1 text | $u_1=0 \implies 71,320\,\text{el}$; $u_1=\text{Free} \implies 55,761\,\text{el}$ |
| **Q5** | Adaptive region definition | Listing 1 specifies `All_elem` (whole specimen) | $N_{\text{el}} = 71,320$; no partition stated in paper (0 hits) |
| **Q6** | Listing 2 (14,804 el) vs Sec 4.1 (13,941 el) | Listing 2 is an illustrative code snippet | Reconciled as distinct physical realizations |

---

## 5. Required Governance Action

- **Hold Condition:** This draft inquiry remains strictly in state `AUTHOR_INFORMATION_REQUEST_READY_FOR_HUMAN_APPROVAL_UNSENT`.
- **Transmission Action:** No email, message, or external transmission shall be made unless explicit written direction is provided by the human supervisor.
- **Scientific Integrity:** The thesis documentation maintains 71,320 elements as the publication-literal reconstruction of Listing 1 (`errorTarget=1.0`), while accurately reporting the literature ~13,941 cardinality as an under-specified external data point.
