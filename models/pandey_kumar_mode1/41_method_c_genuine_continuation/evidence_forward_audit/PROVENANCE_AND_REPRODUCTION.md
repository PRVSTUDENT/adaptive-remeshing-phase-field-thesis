# Mode-I Method C Forward Adaptive Refinement State Transfer Audit & Reproduction

**Provenance and Governance Record**  
**Directory:** `models/pandey_kumar_mode1/41_method_c_genuine_continuation/evidence_forward_audit/`  
**Protocol Version:** 2  
**Task Association:** Task F1451 / Task F1452 / Task F1453  

---

## 1. Executive Summary & Purpose

This directory contains the authoritative, version-controlled evidence and reproduction scripts for the **forward-refinement nonmatching state transfer** audit from the coarse 2,906-element donor mesh to the 14,677-element fine recipient mesh at $u = 0.0050\,\text{mm}$.

This package establishes:
1. **Mathematical Transfer Integrity:** Verification of displacement $L_2$ error ($0.1347\% \le 1.0\%$), peak damage fidelity ($\Delta d = 0.000000$), domain-integrated damage error ($0.1322\% \le 5.0\%$), history non-negativity ($\min(H) \ge 0$), and offline mesh compliance disparity ($1.6662\% \le 5.0\%$).
2. **Epistemic Separation:** Strict decoupling between verified offline transfer metrics and un-run recipient continuation solver metrics.
3. **Disentanglement of Three Damage Fields:** Resolving the distinction between coarse donor ($d_{\max} = 0.094910$), coarse projected on fine ($d_{\max} = 0.094910$), and independently solved fine reference ($d_{\max} = 0.319455$).
4. **Dimensional Correction of Interpolation Formulas:** Evaluation of the dimensionless chordal interpolation formula $\xi \coth(\xi) - 1$ and rectification of un-normalized length-dimensioned expressions.

---

## 2. File Inventory and SHA-256 Hashes

| File | Description | SHA-256 Hash |
| :--- | :--- | :--- |
| `coarse_donor_state_u0050.json` | Authentic extracted coarse donor field state at $u=0.0050\,\text{mm}$ | `3F9198CDE71F44DEFFEBD0E90CB1CD7D21F170FB09AAC472484B69C4E2C965E7` |
| `extract_coarse_donor_authentic.py` | Python/Abaqus script used to extract field state from cluster ODB | `6B502AA0F1AB4A6E28FAB6BB189ABB7C044F6529157AF9C99087A154DFFE25D9` |
| `audit_forward_transfer.py` | Self-contained independent audit and reproduction script | `76D939477498F1E3CDDE8F98F3E727B8B8BC0966F8F4926ED19CF4CFA5CB0F62` |
| `audit_forward_transfer_summary.json` | Generated audit metrics output | `29DF294A46B3064CCA7AE8834E46ECD4400578B2CCB2A2E8E7E688A7E5A20371` |

---

## 3. Donor ODB Extraction Lineage

- **Cluster ODB Source:** `/scratch9/pr21vyci/runs/mode1_method_b_f1408/01_pre_1s/M1_PRE_1S.odb`
- **HPC Job ID:** `1411891.mmaster02` (`M1_PRE_1S`, 1 CPU serial, PBS queue `normal_imfdfkmq`)
- **Donor Model Deck:** `models/pandey_kumar_mode1/method_b_inf_companion_decks/M1_MB_INF_1S.inp`
  - Elements: 2,906 physical FEs (CPE4/CPE3) / 8,718 element records (3-layer UEL/UMAT/dummy)
  - Nodes: 2,988 physical nodes / 3,037 total nodes
  - SHA-256: `927C159B5879A0F0DB9E6E123CD01B90FC819481818B9971BBF9702751BA0A08`
- **Step & Increment:** `Step-1`, Increment 500, Frame 500 (terminal state of pre-peak Step 1)
- **Kinematic State:** Prescribed displacement $u_y = 0.0050\,\text{mm}$, reaction force $RF_y = 653.088\,\text{N}$, internal energy $E_{\text{int}} = 1.66338\,\text{mJ}$.
- **Extraction Command:**
  ```bash
  abaqus python extract_coarse_donor_authentic.py
  ```

---

## 4. Recipient Mesh Specification

- **Recipient Model Deck:** `models/pandey_kumar_mode1/38_method_b_native_final_14k/M1_MB_NATIVE_FINAL_1S.inp`
  - Elements: 14,677 physical FEs / 44,031 element records
  - Nodes: 14,646 physical nodes / 14,845 total nodes
  - Minimum element size: $h_{\min} = 1.875\,\mu\text{m}$ ($h/l_0 = 0.25$)
  - SHA-256: `39CFD486C87A48A72F145919998E4FE698367DDA452B0F20C2E8F43EA13B0A6D`

---

## 5. Reproduction Instructions

To execute the complete independent audit and verify all 7 Gate 6C transfer criteria:

```bash
# From repository root:
python models/pandey_kumar_mode1/41_method_c_genuine_continuation/evidence_forward_audit/audit_forward_transfer.py
```

Expected output:
- `Displacement L2 error:` $0.134656\%$ (PASS $\le 1.0\%$)
- `Donor domain integral d:` $6.601722 \times 10^{-3}\,\text{mm}^2$
- `Recipient domain integral d:` $6.592993 \times 10^{-3}\,\text{mm}^2$
- `Integrated damage rel error:` $0.132223\%$ (PASS $\le 5.0\%$)
- `Minimum history min(H):` $1.579430 \times 10^{-9}\,\text{kN/mm}^2 \ge 0.0$ (PASS, 0 negative values)
- `Damage field difference |Field 2 - Field 1|:` $0.000000$ (Interpolation fidelity at crack-tip node 129)
- `Damage field disparity |Field 2 - Field 3|:` $0.224545$ (Physics solution discrepancy due to coarse crack pinning)
