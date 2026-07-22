# D2D ABAQUSER Access Requirements

D2D is blocked because ABAQUSER was not found on the login node.

To unblock D2D, provide or enable:

- the ABAQUSER executable or source path;
- the module name and required module load order, if module-managed;
- version string or source commit/hash;
- command syntax for reading the D2C ODB or accepted export input;
- exact accepted input format;
- exact output format;
- element label and integration-point identification convention;
- coordinate export convention and precision;
- license, group, path, or permission requirements.

Once available, D2D must compare the real ABAQUSER export against the D2C ODB
reference and the transferred CSVs. A normal Abaqus Python extractor is not an
acceptable substitute for ABAQUSER verification.
