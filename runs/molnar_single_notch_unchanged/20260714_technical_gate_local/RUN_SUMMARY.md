# Molnar Single-Notch Unchanged Technical Gate

Date: 2026-07-14

Classification: `technical_pass_scientific_unchecked`

## Scope

This run uses the original Molnar and Gravouil single-edge-notched tension source and input deck unchanged. This is the first unchanged notched-benchmark gate. The first classification is technical only, not scientific validation of the RF-U curve, crack path, or energy response.

## Source Provenance

Preserved originals:

- `models/baseline_original/molnar_gravouil_2017/02_Single_Notch_Tension/SingleNotch.for`
- `models/baseline_original/molnar_gravouil_2017/02_Single_Notch_Tension/SingleNotch.inp`

Run copies:

- `runs/molnar_single_notch_unchanged/20260714_technical_gate_local/work/SingleNotch.for`
- `runs/molnar_single_notch_unchanged/20260714_technical_gate_local/work/SingleNotch.inp`

SHA-256:

| File | SHA-256 |
|---|---|
| `SingleNotch.for` | `18944e5bb2a3b7973fd0d4bff03f8e078eef667965343d8a29156d093f53f5f1` |
| `SingleNotch.inp` | `89ce3f32e396b0e484be6753a272dd6bbb2a2f9daff426d6a57419f57d665b72` |

## Command

```bat
set "VS2022INSTALLDIR=C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools"
call "%VS2022INSTALLDIR%\VC\Auxiliary\Build\vcvars64.bat"
call "C:\Program Files (x86)\Intel\oneAPI\setvars.bat" intel64
where ifx
where link
where abaqus
ifx --version
cd /d "D:\Master thesis\Adaptive remeshing\runs\molnar_single_notch_unchanged\20260714_technical_gate_local\work"
abaqus job=SingleNotch input=SingleNotch.inp user=SingleNotch.for cpus=1 interactive
```

## Technical Result

Passed technical checks:

- `ifx.exe`, `link.exe`, and `abaqus.bat` were discoverable in the clean shell.
- Abaqus compiled the unchanged `SingleNotch.for`.
- Abaqus linked the user subroutine library.
- Abaqus input file processor completed.
- Abaqus/Standard analysis completed.
- Abaqus SIM wrap-up completed.
- `.sta` reports successful completion.
- ODB opened successfully with Abaqus Python.

Terminal sequence:

```text
End Compiling Abaqus/Standard User Subroutines
End Linking Abaqus/Standard User Subroutines
Begin Analysis Input File Processor
Begin Abaqus/Standard Analysis
Abaqus JOB SingleNotch COMPLETED
```

Status file:

```text
THE ANALYSIS HAS COMPLETED SUCCESSFULLY
```

Model and output summary from the read-only ODB extraction:

- Nodes: `3998`
- Elements: `11790`
- RF-U/phase summary rows: `72`
- Field outputs in both steps: `RF`, `U`, and `SDV1`-`SDV16`
- History outputs: none found in ODB history regions
- Final extracted RP displacement: `U2 = 0.007000000216066837`
- Final extracted RP reaction: `RF2 = 0.0013952305307611823`
- Final extracted maximum `SDV15`: `1.0104930400848389`

This remains `technical_pass_scientific_unchecked`: the RF-U curve, crack/phase-field evolution, and the raw `SDV15 > 1` visualization value still require comparison against Molnar reference behavior before scientific promotion.

## Evidence

Evidence directory:

- `runs/molnar_single_notch_unchanged/20260714_technical_gate_local/evidence/`

Preserved locally:

- `run_molnar_single_notch_clean_env.cmd`
- `terminal_output.txt`
- `SingleNotch.com`
- `SingleNotch.dat`
- `SingleNotch.msg`
- `SingleNotch.prt`
- `SingleNotch.sta`
- `work_file_sha256.txt`

The generated `SingleNotch.odb` is kept in the local `work/` directory and excluded from handoff/Git due to size.

## Extraction

Extraction script:

- `scripts/postprocessing/extract_molnar_single_notch.py`

Derived outputs:

- `runs/molnar_single_notch_unchanged/20260714_technical_gate_local/extracted/SINGLE_NOTCH_EXTRACTION.md`
- `runs/molnar_single_notch_unchanged/20260714_technical_gate_local/extracted/single_notch_extraction_summary.json`
- `runs/molnar_single_notch_unchanged/20260714_technical_gate_local/extracted/single_notch_rf_u_phase_summary.csv`
- `runs/molnar_single_notch_unchanged/20260714_technical_gate_local/extracted/single_notch_matched_displacement_states.csv`
- four matched-state contour CSV files for `SDV14`, `SDV15`, and `SDV16`

Matched displacement states:

| Target abs U2 | Matched step | Frame | U2 | RF2 | Max SDV15 | Max SDV16 |
|---:|---|---:|---:|---:|---:|---:|
| `0.002` | `Step-1` | `20` | `0.0020000000949949026` | `0.2668120265007019` | `0.03597792237997055` | `0.0207978542894125` |
| `0.005` | `Step-1` | `50` | `0.004999999888241291` | `0.626645028591156` | `0.2755390405654907` | `0.21282818913459778` |
| `0.006` | `Step-2` | `10` | `0.006000000052154064` | `0.7214059233665466` | `0.5367832779884338` | `0.6453214883804321` |
| `0.007` | `Step-2` | `20` | `0.007000000216066837` | `0.0013952305307611823` | `1.0104930400848389` | `337.7801818847656` |

Warnings recorded in `.dat`:

- one distorted element warning;
- direct-incrementation exact-time output warnings;
- unsupported `*ELEMENT OUTPUT` warnings for user elements;
- linker `LNK4210` warnings in terminal output.

## Next Gate

Compare the extracted RF-U curve and phase-field/crack evolution against Molnar reference behavior before scientific promotion. Do not start benchmark modification, MISESERI pre-refinement, or state-transfer work before this unchanged benchmark is scientifically reviewed or explicitly waived.
