# D2A state routing package

Classification: `stage_d2a_not_executed_package_prepared`

This package contains transferred nodal `d`, transferred integration-point `H`, raw values, bounded values, source-to-target support, and provenance. It does not claim state ingestion into Abaqus/UEL/UMAT yet.

## Required D2A verification

- target `d` equals transfer CSV within extraction tolerance;
- target `H` equals transfer CSV within extraction tolerance;
- `0 <= d <= 1`;
- `H` does not decrease;
- no default/uniform overwrite of transferred fields;
- all element/IP indices map correctly;
- ABAQUSER/SDV output agrees with independent extraction.
