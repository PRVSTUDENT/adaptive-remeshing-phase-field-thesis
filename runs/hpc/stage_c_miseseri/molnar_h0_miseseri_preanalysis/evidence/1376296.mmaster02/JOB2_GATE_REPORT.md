# Stage C Job 2 Gate Report

Job: `1376296.mmaster02`  
Name: `molnar_h0_miseseri_preanalysis`  
Revision: `2eb63c69d4c64117cc18cfa9770750a6d2464908`  
Host: `mnode104.cluster`  
ODB: `/scratch/pr21vyci/adaptive-remeshing/runs/molnar_h0_miseseri_preanalysis_1376296.mmaster02/molnar_h0_miseseri_preanalysis.odb`

## Queue wait

| Instant | Time |
|---|---|
| `qtime` | 2026-07-21 09:02:53 |
| `stime` | 2026-07-21 09:02:54 |
| Wait | **≈ 1 s** |
| Submit route | `entry_imfdfkmq` |
| Execution queue | `normal_imfdfkmq` (after routing) |
| Wall used | 00:01:30 |
| Exit_status | **0** |

Compare to Job 1 wait ≈ 11.6 min on the same route→normal path.

---

## Technical gate

| Check | Result |
|---|---|
| PBS Exit_status = 0 | **pass** |
| Abaqus STA success | **pass** — `THE ANALYSIS HAS COMPLETED SUCCESSFULLY` |
| Abaqus return code | **0** |
| Classification | `molnar_h0_miseseri_preanalysis_technical_pass` |
| ODB readable | **pass** |
| Final U2 | **0.004640 mm** (target 0.00464; within 1e-4) |
| Final RF2 | 0.588340 kN |
| MISESERI / MISESAVG / S / EVOL / U / RF present | **pass** |
| MISESERI values | **3930** |
| Layered instance elements | **11790** = 3×3930 |
| Finite MISESERI values | **pass** |
| Mapping valid | **pass** |

```text
technical_gate = pass
```

Evidence: `JOB2_TECHNICAL_SUMMARY.json`

---

## Scientific gate

### Scalars

| Quantity | Value |
|---|---:|
| MISESERI min | 1.28e-18 |
| MISESERI mean | 4.93e-16 |
| MISESERI max | **8.88e-14** |
| MISESAVG max | 2.97e-13 |
| von Mises max (from S on umatelem) | **3.15e-13** |
| SDV15 max | 0.205 |
| n SDV15 ≥ 0.5 | 0 |
| n SDV15 ≥ 0.95 | 0 |
| n marked by absolute errorTarget=0.05 | **0** |

### Spatial ranking (normalized \(\hat e\); top 5% by MISESERI)

| Metric | Value |
|---|---:|
| Top-5% fraction in notch_corridor | 0.411 |
| Top-5% fraction on boundaries | 0.000 |
| Top-5% fraction far_field | 0.589 |
| Top-1% notch_corridor | 0.725 |
| Mass fraction in top 5% | 0.587 |

Phase field has **not** developed a meaningful crack (SDV15 max 0.205, zero elements ≥0.5).

### Classification

Despite a non-uniform ranking pattern (top 1% prefers the notch corridor), **all absolute MISESERI and continuum stress magnitudes on `umatelem` are machine-noise level** (\(\max\sim10^{-13}\)–\(10^{-14}\)).

Raising elastic displacement further would only scale an effectively zero estimator and would **not** create a useful remeshing signal on this visualization layer.

```text
scientific_classification = miseseri_output_available_but_scientifically_inactive
scientific_gate = FAIL
job3_release = NO
```

### Root-cause interpretation (engineering)

The Molnár layered model carries the real mechanical response in **U2 UEL** elements. The CPS4 **UMAT facsimile** layer (`umatelem`) uses residual stiffness \(k\sim10^{-11}\) for visualization of SDVs. Abaqus `S` / `MISESERI` / `MISESAVG` are recovered from continuum (CPS4) response, so they remain essentially zero even when the UEL stress state is nontrivial.

Therefore Job 2 demonstrates:

1. the **output route** for MISESERI exists and is complete (technical pass);
2. the **scientific stress-error field on umatelem is inactive** for remeshing (scientific fail).

This is **not** a solver crash and **not** a reason to retune `errorTarget` or automatically resubmit Job 2.

---

## Figures

Under `figures/`:

1. `01_miseseri_contour.png` (log10)
2. `02_normalized_miseseri_contour.png`
3. `03_von_mises_contour.png`
4. `04_top5pct_marked_elements.png`
5. `05_phase_field_sdv15.png`

## Data products

| File | Role |
|---|---|
| `JOB2_MISESERI_ELEMENT_DATA.csv` | annotated element table |
| `JOB2_FIELD_SUMMARY.json` | machine-readable gate summary |
| `JOB2_TECHNICAL_SUMMARY.json` | ODB technical extract |
| `JOB2_GATE_REPORT.md` | this report |

CSV columns include: `physical_element_label`, `centroid_x/y`, `MISESERI`, `MISESAVG`, `EVOL`, `von_mises`, `normalized_MISESERI`, `region_classification`, top-percentile flags.

---

## Decision (stop before Job 3)

```text
technical_gate = pass
scientific_classification = miseseri_output_available_but_scientifically_inactive
Job 3: NOT RELEASED
No automatic retry of Job 2
No errorTarget retuning
No additional remeshing pass
```

**Next action requires an engineering design choice** (user-directed, not automatic):

- redesign pre-analysis so continuum stress (and MISESERI) is carried on stress-bearing elements, or
- recover a stress-error indicator from UEL state / an auxiliary continuum model that does not use the \(10^{-11}\) residual UMAT layer as the sole stress path, or
- document that pure Abaqus MISESERI on Molnár facsimile CPS4 is not viable and adopt an alternative pre-refinement driver.

Do **not** submit Job 3 on the present ODB.
