# Postprocessing Starter Contract

Implementation is pending Abaqus ODB access and baseline decks. The first extraction implementation must satisfy `configs/postprocessing_contract.json`.

Required outputs:

- reaction force versus displacement;
- phase-field values with convention recorded;
- fracture or dissipated energy;
- element count and mesh identifiers;
- wall time and solver status;
- matched-state comparison metadata.

Do not compare crack paths or force-displacement curves without a declared comparison state and grid.
