# Supervisor reports

Loose files are organised by purpose. Existing dated meeting packages remain in their original folders.

|Folder|Contents|
|---|---|
|[reports](reports/)|Gate 0/1, Gate 5, Gate 6 and Mode-I scientific reports|
|[progress_updates](progress_updates/)|Progress reports and submission notes, grouped by date|
|[figures](figures/)|Plots and figure PDFs for Gate 6 and Mode-I|
|[data](data/)|JSON/CSV numerical audits and extracted tables|
|[correspondence](correspondence/)|ABAQUSER requests and author-inquiry drafts|
|[planning_and_decisions](planning_and_decisions/)|Plans, checklists, protocols and decision notes|
|[archive](archive/)|Historical backups, ZIP packages, LaTeX build files and original checksum manifest|
|[catalog](catalog/)|Organisation audit and maintenance helper|

[FILE_INDEX.csv](FILE_INDEX.csv) maps every moved file from its previous path to its new path and records hashes before and after organisation. Only link paths in Markdown/TeX were adjusted; numerical data, images, PDFs and backups are unchanged. No files were deleted.

`MANIFEST.sha256` contains current checksums; the previous historical manifest is preserved in `archive/manifests/` and its old paths can be resolved using the index.

This operation is confined to this folder. Historical references and figure generators elsewhere in the repository were not edited while AGY is working; the four known external generator/config paths are listed in `catalog/organisation_audit.json`. Use the index to resolve their legacy paths before rerunning them.
