# Stage D2 Minimal Abaqus Transfer Plan

Status: `stage_d2_package_prepared_not_executed`

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

The status is intentionally:

```text
stage_d2a_not_executed_package_prepared
```

No `D2A.ok` is written because Abaqus/ODB/ABAQUSER ingestion has not yet been
run.

## D2A gate

Run a serial target-model ingestion job only after the selected UEL/UMAT
initialization route is implemented. Acceptance requires:

- target `d` equals `target_transferred_nodal_d.csv` within extraction tolerance;
- target `H` equals `target_transferred_ip_H.csv` within extraction tolerance;
- `0 <= d <= 1`;
- `H` does not decrease;
- no default/uniform overwrite of transferred fields;
- all element/IP indices map correctly;
- ABAQUSER/SDV output agrees with independent extraction.

Required outputs after a real D2A run:

```text
D2A_STATE_INGESTION_STATUS.json
D2A_TRANSFERRED_VS_ODB.csv
D2A_STATE_ROUTING_REPORT.md
D2A.ok
```

## Blocked work

Do not start full fracture transfer. The first interrupted Molnar fracture
continuation remains blocked until corrected T5 passes, D2A passes, D2B serial
continuation passes, D2C threaded repeatability passes, and state arrays plus
element/IP ordering are proven.

