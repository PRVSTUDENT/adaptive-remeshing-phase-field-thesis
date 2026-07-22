# Stage D2 Minimal Abaqus Transfer Plan

Status: `stage_d2a_state_ingestion_pass_d2b_attempted_solver_fail`

## Current interpretation

Stage D1 verified deterministic and physically guarded transfer mechanics. It
does not prove negligible transfer error. The D1 baseline errors remain:

| Quantity | Value |
| --- | ---: |
| Nodal `d` L2 error | 0.0270 |
| Nodal `d` maximum error | 0.0850 |
| Integration-point `H` L2 error | 0.0108 |
| Integration-point `H` maximum error | 0.0234 |
| Bounded transfer energy minus exact target energy | -0.00769 |

Defensible wording:

> The analytical harness verifies deterministic and physically guarded
> state-transfer mechanics; it establishes transfer-error and energy-jump
> baselines rather than proving negligible transfer error.

## D2 package

The tiny nonmatching source/target package is under:

```text
models/state_transfer/d2_tiny_transfer/
```

It contains:

- `source_nodes.csv`
- `source_elements.csv`
- `source_nodal_d.csv`
- `source_ip_state.csv`
- `target_nodes.csv`
- `target_elements.csv`
- `target_transferred_nodal_d.csv`
- `target_transferred_ip_H.csv`
- `source_to_target_support_map.csv`
- `transfer_provenance.json`
- `D2A_STATE_INGESTION_STATUS.json`
- `D2A_STATE_ROUTING_REPORT.md`
- `D2A_TARGET_INPUT_PACKAGE.inp`
- `executable/D2A_serial_ingestion.inp`
- `executable/D2B_serial_continuation.inp`
- `executable/d2_transfer_table.inc`
- `executable/d2_tiny_transfer_uel.for`
- `executable/PACKAGE_VALIDATION.json`

The original scaffold status was intentionally:

```text
stage_d2a_not_executed_package_prepared
```

The executable D2A package has now been generated, statically validated, run on
HPC, and accepted. Final accepted job: `1376785.mmaster02`; PBS
`Exit_status=0`; `D2A.ok` exists.

## D2A implementation route

The D2A route is a separate tiny UEL/UMAT source variant:

```text
src/state_transfer/d2_tiny_transfer_uel.for
```

It does not modify the frozen Molnar source or the accepted C2C-v3 mesh. The
preserved Molnar deck confirms that the U1 phase element declares Abaqus DOF
`3`; the D2A deck therefore prescribes transferred nodal phase values on DOF
`3`, rather than assuming that value without source/deck evidence.

The D2 source uses:

```text
TRANSFER_MODE = 1
```

only in this D2-only source variant. Normal production jobs keep transferred
history initialization disabled by not using this source. The generated include
file `d2_transfer_table.inc` is keyed by physical element label and integration
point number. The current tiny package has one reduced-integration visualization
point per target element, so every key is `(target_element, 1)`.

## D2A gate and result

Run a serial target-model ingestion job only after the selected UEL/UMAT
initialization route is implemented. Acceptance requires:

- transferred phase reaches UMAT `SDV15` as the independent interpolation of
  `target_transferred_nodal_d.csv` within extraction tolerance;
- transferred `H` reaches UMAT `SDV16` from `target_transferred_ip_H.csv`
  within extraction tolerance;
- `0 <= d <= 1`;
- `H` does not decrease beyond extraction tolerance;
- no default/uniform overwrite of transferred fields;
- all element/IP indices map correctly;
- ABAQUSER/SDV output agrees with independent extraction.

Final D2A result from job `1376785.mmaster02`:

| Quantity | Value |
| --- | ---: |
| Classification | `stage_d2a_state_ingestion_pass` |
| PBS exit status | `0` |
| Solver exit | `0` |
| ODB readable | `true` |
| Target element/IP coverage | `1.0` |
| Maximum `SDV15` interpolation error | `0.0` |
| Maximum `SDV16/H` error | `6.428999999030793e-09` |
| Failures | `0` |

Abaqus did not expose the UEL phase DOF as usable nodal `U` output in this
smoke deck (`target_node_coverage=0.0` in the ODB nodal-output diagnostic).
Therefore the accepted D2A proof is the element/IP UMAT mirror: `SDV15` proves
phase ingestion and `SDV16` proves history ingestion.

Required outputs after a real D2A run:

```text
D2A_STATE_INGESTION_STATUS.json
D2A_TRANSFERRED_VS_ODB.csv
D2A_NODE_COMPARISON.csv
D2A_IP_COMPARISON.csv
D2A_STATE_ROUTING_REPORT.md
D2A_JOB_RECORD.txt
D2A.ok
```

Prepared execution scripts:

```text
scripts/hpc/stage_d2/01_d2a_serial_ingestion.pbs
scripts/hpc/stage_d2/submit_d2a_serial_ingestion.sh
scripts/hpc/stage_d2/02_d2b_serial_continuation.pbs
scripts/hpc/stage_d2/03_d2c_threads4_repeatability.pbs
scripts/hpc/stage_d2/04_d2d_abaquser_verification.pbs
```

D2A has been submitted and accepted. D2B has been submitted once and has not
passed. D2C and D2D are present as guarded placeholders and were not submitted
in this closeout.

## D2B serial continuation attempt

D2B is designed to retain the accepted D2A initialization as Step 1, release
the phase initialization constraints in Step 2 with `*Boundary, op=NEW`, and
apply a tiny mechanical continuation displacement of `U2=1.0e-5 mm` in Step 3.
The transfer values, transfer table, labels, and D2-only source route remain
unchanged from the accepted D2A path.

The single submitted D2B job was:

| Quantity | Value |
| --- | ---: |
| Job ID | `1376819.mmaster02` |
| PBS exit status | `10` |
| Solver exit | `1` |
| Classification | `stage_d2b_solver_fail` |
| D2B marker | no `D2B.ok` |

The Abaqus message file reports:

```text
TOO MANY INCREMENTS NEEDED TO COMPLETE THE STEP
```

This is a technical continuation-control failure during the tiny continuation,
not an accepted state-persistence result. The corrective prepared deck increases
the D2B release and continuation step maximum increments from `inc=2` to
`inc=50`. This correction does not change transfer-field values, element/IP
keys, label mapping, or the D2-only state route. It has not been submitted.

## Blocked work

Do not start full fracture transfer. The first interrupted Molnar fracture
continuation remains blocked until corrected T5 passes, D2A passes, D2B serial
continuation passes, D2C threaded repeatability passes, and state arrays plus
element/IP ordering are proven.
