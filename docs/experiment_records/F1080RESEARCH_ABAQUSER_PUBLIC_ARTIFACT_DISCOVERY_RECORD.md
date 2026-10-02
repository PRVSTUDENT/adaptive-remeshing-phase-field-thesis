# F1080 - ABAQUSER Public Artifact and Interface Discovery

Date: 2026-09-23  
Agent: Codex  
Execution scope: public literature and software-artifact search only  
HPC / Abaqus submission activity: none

## Result

The former statement that the ABAQUSER interface was wholly unknown is too
strong. The public literature documents the main data route, the controller
name, the auxiliary information-file vocabulary, and the dummy-element mapping
contract. The authentic IMFD implementation itself was not found as a publicly
downloadable package.

Recommended classification:

- `LITERATURE_INTERFACE_CONCEPT_SUBSTANTIALLY_RECOVERED`
- `ORIGINAL_ABAQUSER_IMPLEMENTATION_NOT_OBTAINED`
- `AUTHENTIC_INTEGRATION_EXECUTION_REMAINS_BLOCKED`

The existing verified companion visualization bridge remains scientifically
distinct from authentic ABAQUSER execution.

## Primary-source trail

1. The TU Bergakademie Freiberg publication page lists S. Roth, G. Hütter,
   U. Mühlich, B. Nassauer, L. Zybell, and M. Kuna, *Visualisation of User
   Defined Finite Elements with Abaqus/Viewer*, GACM Report, Summer 2012,
   pp. 7-14, and links the original PDF:
   <https://tu-freiberg.de/en/imfd/tm-fk/team/pd-dr-geralf-hutter>
2. Direct university-hosted PDF:
   <https://drupal1.hrz.tu-freiberg.de/sites/default/files/media/technische-mechanik---festkoerpermechanik-16567/Mitarbeiter/Huetter_Geralf/4_07-14_gacm-report-roth_8-12.pdf>
3. Roth and Kiefer (2022), DOI `10.1002/nme.6864`, gives a later concrete
   application description:
   <https://onlinelibrary.wiley.com/doi/full/10.1002/nme.6864>
4. Diddige, Roth, and Kiefer (2025), DOI `10.1016/j.cma.2025.118143`, identifies
   ABAQUSER as the developed in-house visualization tool and cites the 2012
   report:
   <https://doi.org/10.1016/j.cma.2025.118143>
5. The current IMFD equipment page lists ABAQUSER among its own software
   developments, rather than as a public download:
   <https://tu-freiberg.de/en/imfd/tm-fk/equipment>
6. Stephan Roth's dissertation records that the author developed ABAQUSER and
   points back to the 2012 report for details:
   <https://nbn-resolving.de/urn:nbn:de:bsz:105-qucosa-209735>

## Recovered interface contract

The 2012 report establishes the following implementation-level facts.

- ABAQUSER is described as a collection of shell and Python scripts, not merely
  an opaque executable.
- The controlling entry point is named `abaquser.sh`. Its command form resembles
  the Abaqus command and adds an option for an auxiliary information file. The
  wrapper checks required conventions, submits the FE job, and starts
  visualization post-processing after successful completion.
- The preferred result source is the binary Abaqus `.fil` file. The paper rejects
  `.dat` as slower, larger, and precision-limited for this purpose.
- Abaqus Python is used to create or update an `.odb`. The workflow reconstructs
  the assembly/instance structure from node and element labels before writing
  model and result fields.
- Every node and element must belong to at least one named set used to recover
  assembly and instance ownership; otherwise the entity cannot be assigned to an
  instance and visualization fails.
- The separate information file is input-deck-like. The published vocabulary
  includes `*DIM`, `*UEL`, `TYPE`, `NUMIP`, `NUMSDV`, `NUMSDVPIP`, `ABADUMMY`,
  and `*SDV`.
- For each UEL type, the information file supplies the user/dummy node ordering,
  integration-point correspondence, model dimension, total SDV count, SDVs per
  integration point, and the chosen Abaqus-library dummy element.
- Each exposed field is assigned a name, description, tensorial rank, and SDV
  component indices. This is the mechanism used to reconstruct scalars, vectors,
  and tensors and to make tensor invariants available in Viewer.
- The unstructured SDV array read from `.fil` is decomposed first by integration
  point and then by physical field, reordered for the dummy element, grouped by
  Abaqus instance, and written through the ODB update interfaces.
- The original implementation used the Abaqus Python interface; the paper notes
  that a C++ interface could improve performance. For Abaqus 6.10 and later, the
  2012 implementation could parallelize `.fil` extraction and ODB update with
  Python 2.6 multiprocessing.

The later Roth-Kiefer paper confirms this route in production use:

`UEL analysis -> binary .fil -> ABAQUSER field interpretation -> dummy standard elements -> .odb -> Abaqus/Viewer`

For that paper's example, quadratic UELs U1/U2 were represented by CPE8 dummy
elements. Cubic UELs U3/U4/U5 were represented by CPE4 because Abaqus had no
matching cubic built-in element. The authors explicitly note that this mismatch
can introduce a small contour-plot approximation, while direct integration-point
field access in the ODB retains the calculated values.

## Public-package search

Searches were performed on 2026-09-23 using the exact product name and the
implementation-specific strings `abaquser.sh`, `ABADUMMY`, and `NUMSDVPIP`.
Targets included:

- TU Freiberg current IMFD pages and publication pages;
- GitHub repository search API;
- GitLab public project search API;
- Zenodo record search API;
- web search for source archives, supplementary files, and exact interface keys;
- Qucosa / German National Library dissertation records;
- Internet Archive CDX URL-name search for `*abaquser*` under `tu-freiberg.de`.

Observed public results:

- GitHub repository-name/description search: zero repositories.
- GitLab public project search: zero projects.
- Zenodo record search: zero records.
- Internet Archive URL-name search under `tu-freiberg.de`: zero matching URLs.
- The TU publication page exposes the 2012 PDF, but no source, executable, or
  package link.
- The current IMFD equipment page labels ABAQUSER as an in-house development.
- Later papers continue to cite the same 2012 report and use the tool, but no
  supplementary software artifact was located.

This negative search is not proof that no public copy exists anywhere. It is
sufficient to conclude that no authentic, attributable package was located in
the searched primary channels.

## Integration consequences for this repository

The literature now supports designing and validating the required interface:

- request binary `.fil` output for the required nodal and integration-point data;
- preserve complete node/element set ownership information;
- define one visualization mapping per UEL type;
- define an explicit SDV-to-physical-field table including rank and component
  ordering;
- use topology-compatible standard elements wherever possible;
- verify contour interpolation separately from integration-point value parity.

It does not authorize claiming authentic ABAQUSER integration. A clean-room
converter could be implemented from the published contract, but it would remain
an independent compatible implementation unless the original IMFD software is
obtained and executed.

## Narrow request to IMFD / Dr. Roth

The external request can now be specific rather than open-ended:

1. the `abaquser.sh` wrapper and all Python modules or compiled extensions;
2. license or written permission for thesis use and archival status;
3. supported Abaqus releases and Python/runtime requirements;
4. one minimal UEL input, matching `.fil`, information file, and expected ODB;
5. the complete command-line syntax and required Abaqus output requests;
6. set/instance naming constraints and the supported `*DIM`, `*UEL`, and `*SDV`
   grammar;
7. any current replacement for the Python 2.6-era implementation.

## Scientific boundary

No Abaqus or PBS job was prepared, authorized, submitted, retried, or modified.
Gate 7 execution remains on hold. This record changes only the knowledge state:
the interface is substantially documented, while the authentic software artifact
remains unobtained.
