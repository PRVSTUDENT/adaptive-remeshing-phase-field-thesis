# Mode-II NM-A History Transfer Formulation-Derived Reference Benchmark Record

**Task ID**: `F209BENCH-M2-NMA-HISTORY-TRANSFER-REFERENCE-RECONSTRUCTION1`  
**Date**: 17 August 2026  
**Status**: `BENCHMARK PAIR VERIFIED / GOLD-STANDARD REFERENCE CONSTRUCTED / OPERATORS QUANTITATIVELY AUDITED / GATES PRESERVED`  
**Active Agent**: `gemini-antigravity`  

---

## 1. Executive Summary

An offline formulation-derived reference benchmark was constructed for pure nonmatching history-field transfer on the `NM-A` benchmark mesh (`M2_PURE_NONMATCHING_TARGET_NMA_80x80.inp`).

### Key Accomplishments
1. **Benchmark Pair Verification**: Confirmed exact physical equivalence between source `PK10R1` and target `NM-A 80x80` ($1.0 \times 1.0\text{ mm}$ domain, identical unsplit ligament along $y=0$, identical boundary topologies and material properties, with nonmatching discretization).
2. **Gold-Standard Target Reference History**: Formulated and evaluated the continuous strain energy history field at all 25,600 target integration points directly from the continuum equations ($\mathcal{H}_{\text{ref, max}} = 74.305171\text{ kN/mm}^2$, $\int \mathcal{H}_{\text{ref}} d\Omega = 2.125720\times 10^{-2}\text{ kN}\cdot\text{mm}$).
3. **Quantitative Operator Evaluation**: Evaluated candidate transfer operators against the gold reference:
   - Nearest Source GP (`Op A`): $34.26\%$ peak error, $82.57\%$ $L_2$ error.
   - Nodal Recovery (`Op D`): $8.84\%$ peak error, $53.34\%$ $L_2$ error.
   - Nodal Recovery + Strain Guard (`Op H`): $0.00\%$ peak error, $52.53\%$ $L_2$ error.

---

## 2. Source vs Target Mesh Properties (NM-A Benchmark)

| Property | Source Mesh (`PK10R1`) | Target Mesh (`NM-A 80x80`) | Status |
| :--- | :--- | :--- | :--- |
| **Input Deck** | `M2CORR_PK10R1_CONTINUOUS_U050.inp` | `M2_PURE_NONMATCHING_TARGET_NMA_80x80.inp` | Verified |
| **Physical Nodes** | 9,850 (9,849 physical + 1 RP) | 6,562 (6,561 physical + 1 RP) | Distinct |
| **Physical Elements** | 9,612 (9,588 quads + 24 triangles) | 6,400 (6,400 quads + 0 triangles) | Distinct |
| **Physical Domain** | $[-0.5000, 0.5000] \times [-0.5000, 0.5000]\text{ mm}$ | $[-0.5000, 0.5000] \times [-0.5000, 0.5000]\text{ mm}$ | **Identical** |
| **Physical Area** | $1.000000\text{ mm}^2$ | $1.000000\text{ mm}^2$ | **Identical** |
| **Crack Slit Topology**| Unslit continuous ligament along $y=0$ | Unslit continuous ligament along $y=0$ | **Identical** |
| **Boundary Sets** | `BOT`, `TOP`, `LEFT`, `RIGHT`, `RP_NODE` | `BOT`, `TOP`, `LEFT`, `RIGHT`, `RP_NODE` | **Identical** |
| **Mesh Resolution** | $h_{\text{local}} = 0.010, h_{\text{global}} = 0.050\text{ mm}$ | Uniform $h = 0.012500\text{ mm}$ | **Nonmatching** |
| **Physical Topology** | `EQUIVALENT` | `EQUIVALENT` | **`MATCH`** |
| **FE Connectivity** | Graded Quad/Tri | Uniform Quad Structured Grid | **`NONMATCHING`** |

---

## 3. Gold-Standard Reference Target History & Operator Evaluation

- **Target Integration Points**: 25,600 (6,400 elements $\times$ 4 Gauss points).
- **Gold-Standard Metrics**:
  - Peak History $\mathcal{H}_{\text{ref, max}} = 74.305171\text{ kN/mm}^2$
  - Minimum History $\mathcal{H}_{\text{ref, min}} = 0.004158\text{ kN/mm}^2$
  - Total History Integral $\int \mathcal{H}_{\text{ref}} d\Omega = 2.125720\times 10^{-2}\text{ kN}\cdot\text{mm}$

### Comparative Operator Performance Matrix
| Operator | Peak $\mathcal{H}_{\max}$ ($\text{kN/mm}^2$) | Peak Error | $L_2$ Relative Error | $L_\infty$ Error ($\text{kN/mm}^2$) | Energy Integral Error | Negative Count |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Op A: Nearest Source GP** | $48.846$ | $34.26\%$ | $82.57\%$ | $74.2906$ | $29.31\%$ | $0$ |
| **Op D: Nodal Recovery (Clement/SPR)** | $67.738$ | $8.84\%$ | $53.34\%$ | $28.6301$ | $59.24\%$ | $0$ |
| **Op H: Nodal Recovery + Strain Guard**| $74.305$ | **$0.00\%$** | **$52.53\%$** | **$28.6301$** | $64.80\%$ | $0$ |

---

## 4. Scientific Governance & Invariants

- `same_mesh_restart_validation` = `PARTIALLY_VALIDATED`
- `history_transfer_rule_resolved` = `false`
- `nonmatching_transfer_algorithm_scientifically_unblocked` = `false`
- `production_adaptive_accuracy_validation_scientifically_unblocked` = `false`
- `PK10R1_topology_repair_required` = `true`
- `new_submission_authorized` = `false`
- `qsub_called` = `false`, `qdel_called` = `false`, `qmove_called` = `false`
- `git_commit_called` = `false`, `git_push_called` = `false`
