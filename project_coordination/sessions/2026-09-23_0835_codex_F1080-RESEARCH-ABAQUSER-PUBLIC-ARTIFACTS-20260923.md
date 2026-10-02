# Session Report: F1080 ABAQUSER Public-Artifact Research

## Session

- Agent: `codex`
- Task: `F1080-RESEARCH-ABAQUSER-PUBLIC-ARTIFACTS-20260923`
- Started: `2026-09-23T08:35:23+02:00`
- Ended: `2026-09-23T08:48:56+02:00`
- Starting commit: `42762382e8e0f4a8fc87b43eb0ddfba06028bcaf`
- HPC submissions or scheduler mutations: none
- Authorization changes: none

## Bootstrap and Safety

The mandatory bootstrap commands were run before task work. The canonical
coordination files were read in the required order, `ACTIVE_SESSION.json` was
verified inactive, and the session was claimed with a narrow write scope. All
pre-existing dirty paths were preserved. The artifact registry was searched
before adding the research and session records.

## Work Performed

1. Located the official TU Bergakademie Freiberg publication entry and the
   directly linked 2012 GACM report PDF.
2. Downloaded a temporary source copy, extracted its text, rendered pages for
   visual verification, and reconstructed the published ABAQUSER interface.
3. Cross-checked the workflow against Roth and Kiefer (2022), Diddige, Roth and
   Kiefer (2025), the current IMFD software listing, and Roth's dissertation.
4. Searched public discovery channels for a software distribution: exact-name
   web queries, distinctive controller/metadata strings, GitHub, GitLab,
   Zenodo, current TU pages, and URL-name searches in the Internet Archive.
5. Updated the Diddige literature note and wrote a durable research record.

## Findings

- The literature/interface concept is substantially recovered.
- The 2012 paper identifies ABAQUSER as shell and Python scripts controlled by
  `abaquser.sh`, consuming a binary Abaqus `.fil` plus an information file and
  reconstructing physical fields in an `.odb` using dummy standard elements.
- The published information-file grammar includes `*DIM`, `*UEL`, `TYPE`,
  `NUMIP`, `NUMSDV`, `NUMSDVPIP`, `ABADUMMY`, and `*SDV`, with ordering and
  field metadata needed for the reconstruction.
- No publicly attributable original source package or executable distribution
  was located in the channels searched. This is a bounded search result, not a
  proof that no public copy exists.
- Authentic integration/execution remains blocked on obtaining the original
  software or sufficient implementation artifacts and a representative example.

## Files Changed

- `docs/experiment_records/F1080RESEARCH_ABAQUSER_PUBLIC_ARTIFACT_DISCOVERY_RECORD.md`
- `references/notes/diddige_roth_kiefer_2025.md`
- `project_coordination/TASK_LEDGER.csv`
- `project_coordination/ARTIFACT_REGISTRY.csv`
- `project_coordination/ACTIVE_SESSION.json`
- this session report

## Verification and Evidence

- Official source PDF SHA-256:
  `C3D1961F611FB320DF0BD1B86DC11D2990114262942E8140D12EA772BB7D739A`
- Research record SHA-256 before ledger registration:
  `1AF1C417AD08E2F035A9D4725CA505FC74E6681D689E142D5E0CCA3E9536E5F2`
- Updated literature note SHA-256:
  `2899F56CA7F100F6EF40990266DFEDBC3D7D42F4DF3B5FFC4F83A94E91DCD18C`
- No solver, Abaqus, PBS, or notification test was run because this was a
  literature and artifact-discovery task.

## Next Decision

Prepare a narrowly scoped request to Dr. Stefan Roth / IMFD for the original
ABAQUSER package, license and platform constraints, one example information
file, the corresponding UEL output convention, and a minimal `.fil` to `.odb`
demonstration. No external message was sent in this session.
