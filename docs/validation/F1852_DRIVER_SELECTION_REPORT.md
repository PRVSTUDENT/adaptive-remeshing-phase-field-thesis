# F1852 measured driver selection

User directly requested the next operation in the pasted F1851 review. This is not a repair or fabrication of the unresolved F1850 transport provenance. Master OPEN; 0 new PBS, cumulative36. No new fracture solve, donor substitution, target tuning or frozen framework/UEL edit.

## Numerical result

|Case|max damage|Core element fraction %|Selected driver|F1850 count|Fresh count|Body identical?|Gate06|
|---|---:|---:|---|---:|---:|---|---:|
|1|1.002208|3.131|CONSTRUCTED_DAMAGE_ENVELOPE|20193|20193|True|1.919 FAIL|
|2|0.997577|1.961|CONSTRUCTED_DAMAGE_ENVELOPE|17280|17280|True|2.205 PASS|
|3|0.999989|3.059|CONSTRUCTED_DAMAGE_ENVELOPE|45009|45009|True|2.004 PASS|
|5|0.476020|0.000|NATIVE_ABAQUS_STRESS_RECOVERY_ERROR|4375|15411|False|1.939 FAIL|

Cases1/2/3 are body-identical to F1850, preserving all their successes and failures, including Case3 diffuse refinement at45,009 elements. Case5 rises from4,375 to15,411, with selective inter-hole refinement. Gate06 improves from1.338 to1.939 but remains FAIL (<2.0). This is not four-case framework finalization or native method qualification. Native mesh count is not tuned to the historical15,330 target.

## Selection and implementation
New separately versioned source composes immutable F1849 damage and F1846 native engines. No case IDs or coordinates occur in selection. Max donor SDV1 >=0.5 selects the unchanged damage envelope; below0.5 selects raw native fields only after the native gate passes. Core fraction is measured and recorded, not a second fitted cutoff. All native fallback input is from one last available frame, with no temporal maximum of stress errors, local error/stress division or synthetic relabeling.
Damage strength was measured from every available SDV1 frame in the exact existing source donor; frozen envelope meshes remain the F1850 inputs for strong signals. This is an offline full-history comparison, not proof of causal online prediction. Later held-out accuracy evaluation is not available here. Case1 measured overshoot1.0022 is retained; no clipping or threshold tuning was introduced. Native field inspection does not prove mechanical correctness or solve completion.

## Case5 native gate
Original source: `models/pandey_kumar_mode1/218_f1726_seven_hole_study/PK_F1726_SEVEN_HOLE_COARSE.odb`, 194344892 bytes, SHA256 `cb673713fde31593ae452a21bc05bffc140bccce71f1d43d601ee17b43802b0e`.
Step2 index171, frameId341, t=0.778866. Native MISESERI/MISESAVG/EVOL/S present. All2465 quads and101 triangles have stress and positive MISESAVG; zero triangle tensors/base counts are0. Triangle share of squared-error area proxy: total0.935%, inside1.444%, outside0.812%. The F1851 Case2 zero-stress triangle anomaly is absent in this donor. Audit regions use the frozen SevenHolePlateAdapter and never enter sizing.

## Resolution and quality

|Case|Global h<=l0 count %|Global h<=l0 area %|Global h<=l0/2 count %|Global h<=l0/2 area %|Quads %|min detJ|max AR|CAE + audit seconds|
|---|---:|---:|---:|---:|---:|---:|---:|---:|
|1|58.045|35.478|8.483|1.922|97.296|1.026e-06|2.469|4.545|
|2|40.255|17.418|18.987|2.818|97.251|4.939e-07|2.646|4.094|
|3|39.928|9.349|4.181|0.402|97.292|0.001136|2.922|10.489|
|5|79.080|28.508|39.284|5.764|97.735|3.628e-07|2.409|4.415|

Area computed from polygon shoelace geometry; h=sqrt(area). Process/far-field coverage and prior-candidate values are in the summary. Critical-region classification is audit-only. Body equality preserves the full previous spatial resolution on Cases1/2/3; no count-only proxy is used to assert preservation.

## Historical baseline and provenance limits
F1774 reported counts:20,232 /23,965 /28,933 /15,330. Its original local baseline mesh artifacts are unavailable for fresh common-metric evaluation; historical report values are explicitly not mixed-revision fresh regression. F1850 comparison is measured directly from its frozen mesh inputs. Source/damage-history hashes, exact frames, active mesh hashes and current source revision are recorded in the audit JSONs.

## Preserved implementation evidence
An initial overly strict max-damage<=1 guard rejected Case1's authentic overshoot. The guard was corrected to require nonnegative finite damage, preserving the scientific0.5 selection rule. Initial Case5 result and Case1 failed-attempt folder remain under precheck directories; ALL four final meshes were regenerated after the correction and share the final source hash. A120s guarded SSH observation timed out during damage extraction; ps verified the same remote extraction still live, then exact output existence was checked and transferred. No extraction restart or duplicate job was made.

## Publication and review
Genuine standalone and2x2 composite PNG/PDF images were regenerated from all four final same-revision meshes. Pinned image hashes/URLs are in results/validation/f1852_image_manifest.json after publication. Frozen F1849/F1846/production/UEL hashes are retained. No native-method acceptance or Job2 authorization. The unresolved F1850 transport transaction remains untouched.

Timing scope: new per-case elapsed time includes native remeshing plus geometric quality audit, excludes initial donor hashing and damage-history extraction. It is not directly compared as a speedup against F1850 engine-only timing.

Case5 process-region AREA coverage h<=l0 improves16.994% to92.152%; h<=l0/2 improves0.000% to44.211%. These use the same inherited audit mask and are distinct from element-count coverage.

Four focused tests PASS: selection and native fail-closed gate; all-four source hashes and unchanged strong controls; Case5 native audit plus retained Gate06 failure; frozen inputs and image integrity.

Input manifests record exact config, damage measurement, logical donor snapshot and active ODB bytes/SHA for every case. Solver binaries remain local/HPC and are excluded from Git.
