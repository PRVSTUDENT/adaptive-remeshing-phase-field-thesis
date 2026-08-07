# F42C-R5 UEL Property Contract Audit

## 1. Subroutine Property Reference Audit

Audit of `f42c_mixed_uel.for` for `PROPS` and `JPROPS` index references:

| UEL/UMAT Branch | Element Type | PROPS Indices Referenced | Max PROPS Index | JPROPS Indices | Max JPROPS Index | Required `PROPERTIES` | Required `I PROPERTIES` |
| :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: |
| **JTYPE=1** | **U1** (Quad Phase) | 1 (`CLPAR`), 2 (`GCPAR`), 3 (`THCK`) | 3 | None | 0 | **3** | **0** |
| **JTYPE=2** | **U2** (Quad Disp) | 1 (`EMOD`), 2 (`ENU`), 3 (`THCK`), 4 (`PARK`), 5 (`NPHYS_VAL`) | 5 | None | 0 | **5** | **0** |
| **JTYPE=3** | **U3** (Tri Phase) | 1 (`CLPAR`), 2 (`GCPAR`), 3 (`THCK`) | 3 | None | 0 | **3** | **0** |
| **JTYPE=4** | **U4** (Tri Disp) | 1 (`EMOD`), 2 (`ENU`), 3 (`THCK`), 4 (`PARK`), 5 (`NPHYS_VAL`) | 5 | None | 0 | **5** | **0** |
| **UMAT** | **CPE4** Facsimile | 1 (`EMOD`), 2 (`ENU`), 3 (`NPHYS_VAL`), 4 (`TOPOMARK=4.0`) | 4 | None | 0 | **4** | **0** |
| **UMAT** | **CPE3** Facsimile | 1 (`EMOD`), 2 (`ENU`), 3 (`NPHYS_VAL`), 4 (`TOPOMARK=3.0`) | 4 | None | 0 | **4** | **0** |

## 2. Abaqus Keyword Contract Compliance

- **Abaqus Standard Keyword Syntax**:
  `*USER ELEMENT, TYPE=U3, NODES=3, COORDINATES=2, VARIABLES=18, PROPERTIES=3, UNSYMM`
  `*USER ELEMENT, TYPE=U4, NODES=3, COORDINATES=2, VARIABLES=18, PROPERTIES=5, UNSYMM`
- **Prohibited Keywords**:
  - `REAL PROPS` / `REALPROPS` (Invalid Abaqus parameters).
  - `IPROPS` (Invalid Abaqus parameter; omit or use `I PROPERTIES=0`).

## 3. Property Values Table for `F42TRI2.inp`

### U3 (`EL_PHASE`, 3-node Triangle Phase UEL): `PROPERTIES=3`
| Index | Symbol | Physical Meaning | Input Deck Value |
| :---: | :--- | :--- | :---: |
| 1 | `CLPAR` | Length scale parameter $l_0$ | `0.015` |
| 2 | `GCPAR` | Critical energy release rate $G_c$ | `0.0027` |
| 3 | `THCK` | Element thickness | `1.0` |

### U4 (`EL_DISP`, 3-node Triangle Disp UEL): `PROPERTIES=5`
| Index | Symbol | Physical Meaning | Input Deck Value |
| :---: | :--- | :--- | :---: |
| 1 | `EMOD` | Young's modulus $E$ | `210.0` |
| 2 | `ENU` | Poisson's ratio $\nu$ | `0.3` |
| 3 | `THCK` | Element thickness | `1.0` |
| 4 | `PARK` | Residual stiffness parameter $k$ | `1.0e-7` |
| 5 | `NPHYS_VAL` | Element offset for physical indexing | `1` |

### CPE3 (`EL_FACSIMILE`, 3-node Triangle Facsimile UMAT): `constants=4`
| Index | Symbol | Physical Meaning | Input Deck Value |
| :---: | :--- | :--- | :---: |
| 1 | `EMOD` | Dummy passive Young's modulus | `1.0e-11` |
| 2 | `ENU` | Dummy passive Poisson's ratio | `0.3` |
| 3 | `NPHYS_VAL` | Element offset for physical indexing | `1` |
| 4 | `TOPOMARK` | Topology marker for CPE3 centroid dispatch | `3.0` |
