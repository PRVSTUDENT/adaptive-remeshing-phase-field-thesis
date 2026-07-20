# Abaqus/CAE Workflow - Molnar lc015 h-Convergence

## Principle

Abaqus/CAE is the principal postprocessor for ODB extraction and figure export.
Do not use system Python or cluster `python3` for ODB access.

Use:

```bash
abaqus cae noGUI=<script> -- <arguments>
```

or Abaqus Python only where CAE is not required for a specific retained
lightweight CSV already exported by CAE.

## Single-case postprocessing

Paths must be passed via environment variables (not argv):

```bash
export MOLNAR_CASE_ID=H0
export MOLNAR_ODB_PATH=/path/to/case.odb
export MOLNAR_OUTPUT_DIR=/path/to/case_post
abaqus cae noGUI=scripts/abaqus_cae/postprocess_molnar_h_convergence_case.py
```

Exports:

- RP U2 / RF2 XY report (`.rpt`)
- lightweight CSV copy
- explicit origin point `(0, 0)`
- peak force and peak displacement
- initial tangent stiffness
- final SDV contour / crack-path / mesh PNG when available
- postprocessing manifest and exact CAE command record

## Combined postprocessing

```bash
abaqus cae noGUI=scripts/abaqus_cae/postprocess_molnar_h_convergence_combined.py -- \
  H0.odb H1.odb H2.odb /path/to/combined_out
```

## Numerical comparison after CAE export

Only after CAE reports exist, system Python may compare curves:

```bash
python scripts/postprocessing/analyze_molnar_lc015_h_convergence.py \
  --study-root runs/hpc/molnar_lc015_h_convergence
```

## PBS integration

Each PBS job runs the single-case CAE postprocessor after technical Abaqus
success. Postprocessing failure is classified separately from solver failure.
