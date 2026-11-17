# F1851 native MISESERI diagnostics

User-directed diagnostics from the pasted F1850 review. The earlier F1850 bridge response remains unverified because its transport envelope was missing; this task proceeds on the user's direct request, not a fabricated bridge approval. Master OPEN. Zero new PBS; cumulative 36. No fracture solve, target tuning or frozen-source change.

## Findings
1. Case2 extraction preserved node labels/coordinates and mapped element connectivity exactly; offset 5812. MISESERI, MISESAVG and damage have zero difference at both frames. Source stress has four IPs on quads and one on triangles. Extracted SDV1 is whole-element; source damage is identical across each element's IPs, so its scalar value is preserved, but IP output is not retained as IP output.
2. The original Case2 ODB lacks EVOL. A real direct-original remesh under the frozen engine and unchanged final-frame controls failed with: `Output database must contain MISESERI, MISESAVG, and EVOL for error estimate computations.` Extracted EVOL / geometric area is 0.999999937 to 1.000000057, consistent with the input section thickness 1.0 mm. Therefore the extraction supplies geometrically correct volume for the recorded undeformed mesh, but original-vs-extracted remesh equality cannot be demonstrated. Frame300 cannot be selected directly by this frozen engine: it always uses the step's last frame. No source ODB was truncated or modified.
3. F1720 original and companion-only single-frame extracted donors give EXACT count and normalized mesh-body SHA equality at both Step1 frame12 and Step2 frame178. Both pairs use fixed historical F1835 controls (3.4%, min0.001, max0.020, LAST_INCREMENT, coarsening NOT_ALLOWED). Step1: 13,738; Step2: 13,169. The Step2 count differs from the historical F1835 reported13,438; historical replay parity is not claimed. Config and source inputs are preserved for that remaining difference.
4. Both original source status files state `THE ANALYSIS HAS NOT BEEN COMPLETED`. F1720 last frame t=0.725707 has max IP damage0.525213, not full ligament severance. Case2 last frame t=0.655825 has max damage0.997577, which alone does not establish a completed crack path. Neither is an authenticated completed Job1 at its intended termination. This is a concrete donor-state discrepancy with a claimed final-state reproduction.
5. Native MISESERI is already nonzero outside the fixed audit crack windows in the ORIGINAL donors. It is not created by the extraction or a temporal envelope. Stress/MISESAVG are broad around load-bearing boundaries/holes while damage is narrow. These maps identify where native error lies; they do not prove a unique physical or implementation cause for every error hotspot. A stress-error estimator need not refine only damaged elements. No local error/stress ratios were used for remeshing.

## Field localization
Audit masks only: Case2 uses the F1840 union x[0.50,0.65],y[0.45,0.70] and x[0.65,1],y[0.55,0.75]. F1720 uses the frozen adapter three-l0 inter-hole segment distance mask; this mask occupies a small fraction of area and is not a verified crack truth. The squared-error area proxy below is sum(MISESERI² * geometric area), not a reconstruction of Abaqus's internal error norm. Outside-mask error/fine area must not automatically be called unnecessary.

|Original state|Outside-mask area %|Outside squared-error area proxy %|Area d>=0.1 %|Max IP damage|
|---|---:|---:|---:|---:|
|case2_original300.json|92.012|46.576|4.608|0.997190|
|case2_original337.json|92.012|31.777|6.128|0.997577|
|f1720_step1_12.json|97.798|78.175|0.292|0.162551|
|f1720_step2_178.json|97.798|79.984|1.948|0.525213|

## Count and area coverage are different

|Mesh / region|Count|h<=l0 count %|h<=l0 area %|h<=l0/2 count %|h<=l0/2 area %|
|---|---:|---:|---:|---:|---:|
|F1838 / global|28165|85.986|28.739|63.934|11.041|
|F1838 / distal_report|10280|99.981|99.786|94.621|72.957|
|F1838 / distal_F1812|10458|99.771|96.430|94.129|69.860|
|F1840 / global|28160|85.518|28.398|64.549|10.458|
|F1840 / distal_report|8759|100.000|100.000|91.483|69.862|
|F1840 / distal_F1812|9052|99.746|96.716|91.350|68.116|

All elements are classified by centroid; area is polygon shoelace area. Boundary-straddling polygons are not clipped to the audit windows. F1840's distal h<=l0/2 coverage is 91.48% by count versus69.86% by area. Globally it is64.55% by count versus10.46% by area. The original mesh counts reproduce locally (28,165 and28,160).

## Donor inventory

|Source ODB|Bytes|SHA256|Step/frame|
|---|---:|---|---|
|/scratch9/pr21vyci/runs/f1838_case2_native_pilot/PK_HOLE_COARSE_F1838_PILOT.odb|518169932|1f45367a599497e5dd153f45187f41d390cd35affb1188d367f524d0e1ba962e|Step-2 / 300|
|/scratch9/pr21vyci/runs/f1838_case2_native_pilot/PK_HOLE_COARSE_F1838_PILOT.odb|518169932|1f45367a599497e5dd153f45187f41d390cd35affb1188d367f524d0e1ba962e|Step-2 / 337|
|models/pandey_kumar_mode1/213_f1720_coarse_coupled/PK_F1720_COARSE_COUPLED.odb|217936940|e2fe195b93a6378849e134dd3fe17ec69ffd03cca8d446496e6d30820e7958ae|Step-1 / 12|
|models/pandey_kumar_mode1/213_f1720_coarse_coupled/PK_F1720_COARSE_COUPLED.odb|217936940|e2fe195b93a6378849e134dd3fe17ec69ffd03cca8d446496e6d30820e7958ae|Step-2 / 178|
|models/pandey_kumar_mode1/277_f1838_case2_native_pilot/PK_F1838_CASE2_FRAME300_DONOR.odb|7512588|84622470d9b5dd86837030e4f7977308844b7d0b4def3ac444aca609c4a4a78f|RECOVERY_STEP / -1|
|models/pandey_kumar_mode1/278_f1840_final_frame_comparison/PK_F1840_CASE2_FINAL_FRAME_DONOR.odb|7526008|a48c17d793077bd08d9b95177cffb9f7c4fa39ed1e6959a37f20cd515fba27a5|RECOVERY_STEP / -1|

Original Case2 ODB remains HPC-resident. Native field/topology snapshots make all quantities used here reviewable without publishing prohibited large solver binaries. F1720 SHA is E2FE195B..., confirming the F1835 correction rather than the earlier conflicting transcription. No source history was inferred.

## Units, figures and limitations
Source input E=210.0 uses kN/mm² (210 GPa). For field DISPLAY only, stress/error/base values are divided by the documented dummy factor 1e-11/210. Physical S/MISES is shown in kN/mm²; multiply by1000 for MPa. Do not read the historical unscaled1.0466 as1.0466MPa without that unit conversion. All remeshing uses untouched stored fields.
Four original coarse-mesh field-map panels (each damage, S/MISES, MISESERI, MISESAVG) are generated from the same diagnostic revision. F1720 has output for all2747 companion elements: 2663 CPE4 times4 IP plus84 CPE3 times1 IP =10736 records. The historical claim of63 missing overlays incorrectly assumed four IPs per triangle. All native whole-element error/base fields are retained.
The known source termination failure, missing Case2 EVOL and lack of an exact original-Frame300 selection are explicit limitations, not proof of numerical parity. No native-method qualification or Job2 authorization is made. Readable pinned image links and hashes are in results/validation/f1851_image_manifest.json after publication.

## Remaining numerical question
Extraction is not a demonstrated source of indicator distortion in these tests. Every one of the74 CPE3 companions in Case2 reports zero S/MISES and zero MISESAVG; none of the2832 quads does. At frame300 those triangles account for58.92% of the total squared-error area proxy and76.76% of its outside-window part. At frame337 the shares are24.87% and64.28%. This zero-stress triangle output is a concrete formulation/output anomaly and a stronger suspect for off-path error hotspots than frame selection. Whether triangle physical stress should be nonzero must be checked against the UEL stress transfer; correlation alone does not establish how much total remesh refinement would disappear after a correction. Preserve the frozen source and diagnose triangle transfer and source convergence before changing sizing parameters or claiming paper reproduction.

## Generated native-copy ODBs

- `models/pandey_kumar_mode1/281_f1851_native_diagnostics/f1720_Step-1_extracted.odb`: 317268 bytes, SHA256 `30e5b05422df1a830244b14e412cc9c1c76bf3653bd56bebaafb1ec198fdfc53`.
- `models/pandey_kumar_mode1/281_f1851_native_diagnostics/f1720_Step-2_extracted.odb`: 317268 bytes, SHA256 `9a5babb0d5f59ddf3749eca8fbb412a63d77cffb60dcaec4c08aebf044dd93fc`.

All74 Case2 triangle stress tensors are exactly zero in the original final frame (not merely zero von Mises invariants). Four focused tests PASS. Status-file termination excerpts and hashes are in the summary.

Final verification: five focused tests PASS; all eight published image links return HTTP200. Guarded review handoff was NOT SENT: publisher refused the unresolved F1850 response. F1851 science remains pending independent review.
