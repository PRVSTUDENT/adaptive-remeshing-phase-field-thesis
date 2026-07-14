# Codex Workspace Setup

This file is a practical bootstrap guide for the thesis repository. Adapt paths to the actual workspace rather than moving an established project blindly.

## Recommended initial files

```text
.agent.md                         Agent policy and current handoff
THESIS_PLAN.md                    Scientific execution plan and gates
WORKSPACE_STRUCTURE.md            Repository organization and workflows
README.md                         Human entry point
scripts/sync_agent_handoff.py    Flat handoff mirror helper
docs/EXPERIMENT_RECORD_TEMPLATE.md
```

## Recommended folder roles

```text
references/papers/       Original papers; preserve filenames/checksums
references/notes/        Reading notes and equation/variable maps
src/uel/                 UEL sources
src/umat/                UMAT/visualization bridge sources
src/abaquser/            IMFD/ABAQUSER integration
src/shared/              Shared constants and interface definitions
models/baseline_original Original examples, never silently edited
models/<benchmark>/      Geometry/input-generation source for each case
scripts/preprocessing/   Model/input generation and keyword transforms
scripts/remeshing/       MISESERI/remeshing automation
scripts/postprocessing/  ODB extraction and plotting
scripts/validation/      Curve/path/energy comparison
tests/                   Pure-code, deck-integrity, and regression tests
configs/                 Run parameters
runs/                    Immutable run directories or lightweight indexes
results/processed/       Derived numeric data
results/figures/         Script-generated figures
results/tables/          Script-generated tables
docs/experiment_records One record per important run/comparison
docs/decisions/          Scientific/implementation decision records
docs/methods/            Stable procedures
docs/handoffs/           Current state for the next session
agent_handoff/           Flat snapshot of files touched in the latest operation
```

## Bootstrap sequence for Codex

1. Read `.agent.md` and the latest `docs/handoffs/` file.
2. Inspect the repository with targeted commands; avoid scanning large Abaqus outputs.
3. Locate the original UEL/UMAT/source examples and calculate checksums.
4. Create an environment record before compiling.
5. Run only the smallest baseline test first.
6. Add automated extraction before changing the numerical method.
7. Mirror touched files at the end of the operation.

## Suggested environment record

Create `docs/methods/ENVIRONMENT.md` containing:

```text
Date:
Machine/cluster:
Operating system:
Abaqus release/hotfix:
Abaqus Python version:
Fortran compiler and version:
Linker/toolchain:
Precision:
Solver procedure:
CPUs / MPI ranks / threads:
Memory:
License notes:
Reference source checksum:
Known warnings:
```

## Run manifest minimum fields

A JSON/YAML/TOML manifest should include:

```text
run_id
benchmark
method
parent/reference run
geometry source
input deck
UEL/UMAT/ABAQUSER source hashes
Abaqus/compiler versions
material parameters
fracture parameters
phase-field convention
mesh sizes and h/l
load steps/increments
remeshing-rule parameters
output requests
CPU/memory/walltime request
status and validation classification
```

## Input-deck integrity checks

Automate checks for:
- duplicate node/element labels;
- missing `*User Element` and `*UEL Property` blocks;
- expected nodal DOFs;
- material/section assignments;
- required sets (`umatelem`, `All_elem`, reference-point sets, boundary sets);
- matching facsimile connectivity where required;
- output requests (`MISESERI`, `MISESAVG`, `S`, `EVOL`, `U`, `RF`, `SDV`);
- boundary conditions and amplitudes;
- expected element counts before and after transformation;
- local minimum/maximum element size after remeshing.

## Safe Codex command style

Prefer:

```bash
find src scripts docs -maxdepth 3 -type f
rg "MISESERI|All_elem|umatelem" src scripts models
 git status --short --untracked-files=no
 git diff -- path/to/file
python scripts/sync_agent_handoff.py path/to/changed_file
```

Avoid broad recursive scans across `runs/` and raw ODB/scratch folders during interactive work.

## Naming recommendations

Source variants:
```text
uel_molnar_original.for
uel_molnar_baseline_verified.for
uel_remesh_integration_v001.for
```

Run IDs:
```text
modeI__uniform__hOverL-0p5__20260714-1530
modeI__miseseri_preRefine__errTarget-3__20260715-1015
```

Do not use ambiguous names such as `final`, `new`, `working2`, or `latest` for scientific evidence.
