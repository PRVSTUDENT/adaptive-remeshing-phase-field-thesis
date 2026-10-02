# Supervisor Meeting Talk Track: Mode-I Benchmark Reproduction

**Date:** Thursday, 17 September 2026  
**Speaker:** Pruthviraja Reddy Vandavagali (Candidate)  
**Audience:** Prof. Dipl.-Ing. Björn Kiefer, Ph.D. & Dr.-Ing. Stephan Roth (IMFD, TU Bergakademie Freiberg)  
**Target Duration:** 5–7 Minutes  
**Speaking Architecture:** Problem $\to$ Expected Physical Response $\to$ Fixed-Mesh Reference Anchor $\to$ Adaptive Workflow $\to$ Corrected Nominal-1% Result $\to$ Discrepancy Audit $\to$ Decision Required

---

### 1. Problem Definition (0:00 – 0:45)
"Good morning, Professor Kiefer, Dr. Roth. 

Today I am presenting the conclusive status of our reproduction of the fundamental Mode-I phase-field fracture benchmark from Pandey & Kumar (2025). In strict accordance with our governing directive—*to understand everything related to the first model before increasing complexity*—all secondary tracks (Mode-II, state transfer, and external ABAQUSER coupling) remain on formal hold.

The benchmark boundary value problem is a $1.0 \times 1.0\,\text{mm}$ square plate loaded in uniaxial tension, containing an initial sharp horizontal crack of length $a_0 = 0.5\,\text{mm}$ along the symmetry line $y = 0.5\,\text{mm}$. The bottom boundary is on roller supports with the origin pinned against rigid body motion, and the top boundary is subjected to monotonic tensile displacement."

---

### 2. Expected Physical Response (0:45 – 1:30)
"From the variational theory of phase-field fracture, the expected physical response follows four distinct regimes:
1. An initial linear elastic range governed by the plate geometry and material constants ($E = 210\,\text{GPa}$, $\nu = 0.3$), giving a global structural stiffness near $138\,\text{kN/mm}$.
2. Sub-critical damage localization ahead of the crack tip, where the phase field $d$ transitions smoothly from 0 to 1 over the regularization length scale $\ell_0 = 7.5\,\mu\text{m}$.
3. A peak tensile reaction force $F_{\max} \approx 0.758\,\text{kN}$ at an applied stroke of approximately $5.86\,\mu\text{m}$.
4. A steep post-peak load drop as the crack propagates horizontally along the symmetry line to fully sever the specimen."

---

### 3. The Fixed-Mesh Reference Anchor (1:30 – 2:30)
"To establish an authoritative standard against which every adaptive result must be judged, I reconstructed the conventional fixed-mesh baseline (Job `1398090`). The mesh contains $15{,}192$ linear quadrilateral finite elements (`CPE4`), uniformly refined across the crack corridor with an element size $h \approx 1.5\,\mu\text{m}$, guaranteeing $h \le \ell_0 / 5$.

This fixed reference reproduces the published benchmark with exceptional fidelity:
- Peak force $F_{\max} = 0.757778\,\text{kN}$ (within $-0.029\%$ of the literature value $0.7580\,\text{kN}$);
- Displacement at peak $u(F_{\max}) = 0.005857\,\text{mm}$ (within $-0.051\%$ of $0.005860\,\text{mm}$);
- Authoritative unconstrained ordinary least-squares initial structural stiffness $K_0 = 137.945520\,\text{kN/mm}$ ($R^2 = 0.99999960$, fitted over the first 400 uniform increments up to $u = 1.0\,\mu\text{m}$).

*This fixed-mesh solution is the reference response that any adaptive solution must reproduce to an acceptable accuracy.*"

---

### 4. Pandey–Kumar Native Adaptive Workflow & Sizing Indicator (2:30 – 3:30)
"Pandey & Kumar's methodology is an automated two-job pre-refinement procedure:
- In Job 1, an initial coarse mesh ($h_{\mathrm{cms}} = 0.020\,\text{mm}$, $2{,}906$ finite elements) undergoes a fast linear elastic solve.
- Abaqus evaluates the recovered stress discretization error indicator, `MISESERI`. I want to be very precise here: `MISESERI` is the Abaqus stress discretization error indicator associated with the recovered von Mises stress field; it is not a phase-field or damage error indicator.
- In our canonical Mode-I pre-analysis, `MISESERI` contains exactly $2{,}906$ scalar values at the `WHOLE_ELEMENT` position, sharply peaked at the crack tip ($\max = 1.007\,\text{MPa}$) and low in the far field ($5.78 \times 10^{-3}\,\text{MPa}$).
- An Abaqus Python script applies the published `RemeshingRule` with $\texttt{errorTarget}=1.0$ across the whole domain (`All_elem`), generating an adapted mesh. Dual co-located UEL and companion visualization UMAT elements are reconstructed, and the nonlinear fracture solve is executed as Job 2."

---

### 5. Resolution of the 71,320-Element Stiffness Defect (Priority Question A) (3:30 – 4:30)
"In earlier preliminary runs, our nominal 1% adaptive model exhibited an alarming $-11.3\%$ initial stiffness loss ($K_0 \approx 122.38\,\text{kN/mm}$).

Through equation-level diagnostics, I definitively isolated the root cause:
- Under free-format `*NSET` cards without `GENERATE`, the Abaqus input preprocessor (`pre`) enforces a limit of 16 node entries per line.
- In our generated deck, all 150 bottom nodes were written on a single line. Abaqus issued preprocessing warnings, parsed only the first 16 entries, and deleted the remaining 134 entries.
- Consequently, $89\%$ of the bottom boundary was left vertically unconstrained, allowing bottom-edge lift up to approximately $48.34\%$ of the applied stroke and artificially softening the specimen.
- Formatting `*NSET` records to $\le 16$ entries per line completely resolved the issue:
  * Exact frozen requalification (Job `1405044`) restored stiffness to $K_0 = 138.021013\,\text{kN/mm}$ ($+0.05\%$ vs reference), with all 150 nodes constrained and zero lift.
  * The corrected full-fracture simulation (Job `1404933`) achieves initial stiffness $K_0 = 137.820804\,\text{kN/mm}$ ($K_0 \approx 137.821\,\text{kN/mm}$, within $-0.09\%$ of reference) and peak force $F_{\max} = 0.745325\,\text{kN}$ (within $-1.64\%$).
- **Priority Question A is therefore resolved and closed.** Earlier conjectures regarding solver asymmetry are formally retracted."

---

### 6. The Reproduction Discrepancy: 71,320 vs ~13,941 Finite Elements (Priority Question B) (4:30 – 5:45)
"The remaining question in Gate 5 is why our publication-literal reconstruction yields $71{,}320$ finite elements while Pandey & Kumar report approximately $13{,}941$.

To investigate this:
1. I conducted a multi-release audit across four major Abaqus Linux versions: 2019 GA, 2021.HF26, 2022 GA, and 2023.HF4. All four releases produce $100.000\%$ bitwise identical $71{,}320$-element meshes with identical SHA-256 hashes. Version shifts are ruled out.
2. An exhaustive 15-factor One-Factor-At-A-Time audit eliminated load scaling, output frequency, coarsening, and mesher algorithms.
3. A spatial decomposition of our $71{,}320$-element mesh reveals that the crack process corridor ($|y| \le 0.05\,\text{mm}$) contains only $9{,}061$ elements ($12.7\%$). The far field ($41{,}986$ elements) and transition zones ($20{,}273$ elements) account for $62{,}259$ elements—$87.3\%$ of the entire mesh.
4. Under the literal whole-domain rule with $\texttt{errorTarget}=1.0$, Abaqus inevitably refines the elastic far-field to meet the 1% stress error threshold. The accessible evidence does not identify which unpublished implementation detail accounts for the reported $\approx 13{,}941$-element mesh. Possible distinctions such as call-site parameter linkage or an unstated region definition remain hypotheses requiring author information; neither is established."

---

### 7. Supervisor Decision Required (5:45 – 6:30)
"This brings us to the decision required today. I present two concrete pathways:

- **Option A (Recommended):** We accept Gate 5 as externally under-specified. We retain $71{,}320$ finite elements as the verified publication-literal reconstruction, document $\approx 13{,}941$ as an unresolvable literature gap, and proceed directly to Mode-I thesis synthesis and documentation.
- **Option B:** You authorize transmitting our finalized 6-question reproducibility inquiry to Dr. Pandey and Dr. Kumar, and we keep Gate 5 open pending their reply. In strict accordance with your instructions, this inquiry is currently held **strictly UNSENT**.

Under both options, Gate 7 (ABAQUSER), Mode-II, and state transfer remain explicitly on hold until you authorize their release.

Thank you, and I look forward to your decision and questions."
