# Abaqus Python Compatibility Note

## Problem observed

Job `1376154.mmaster02` completed Abaqus/Standard successfully and retained an
ODB, but Abaqus/CAE postprocessing failed at parse time:

```text
SyntaxError: f-string ... postprocess_molnar_h_convergence_case.py
```

The installed Abaqus/CAE Python interpreter rejected f-string syntax.

## Rules for scripts run under `abaqus python` or `abaqus cae noGUI=`

Do not use:

- f-strings;
- variable/function type annotations;
- `from __future__ import annotations`;
- `pathlib`;
- `dataclasses`;
- `os.makedirs(..., exist_ok=True)`;
- `subprocess.run`;
- `open(..., encoding=...)`;
- other Python-3-only APIs unsupported by the site Abaqus interpreter.

Prefer:

- `"{0}".format(...)`;
- `os.path`;
- explicit `os.path.isdir` / `os.makedirs`;
- simple `open` modes;
- CSV writing compatible with older csv modules.

## Validation

Static scan:

```bash
python scripts/validation/check_abaqus_python_compatibility.py
```

Cluster compile proof (authoritative):

```bash
module load abaqus/2023
abaqus python -c "import py_compile; py_compile.compile('scripts/abaqus_cae/postprocess_molnar_h_convergence_case.py', doraise=True)"
```

System `python3` compile success is not sufficient evidence of Abaqus Python
compatibility.

## Path passing

Mandatory ODB/output/case identifiers must be supplied through environment
variables (`MOLNAR_CASE_ID`, `MOLNAR_ODB_PATH`, `MOLNAR_OUTPUT_DIR`), not
through positional `sys.argv`. See `ABAQUS_CAE_ENV_VAR_IO_NOTE.md`.

## Scientific scope

Compatibility repairs must not change RF2/U2 selection, RP identification,
origin handling, SDV15 selection, contour intent, metrics, or model inputs.
