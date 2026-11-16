# -*- coding: mbcs -*-
#
# Abaqus/CAE Release 2024 replay file
# Internal Version: 2023_09_21-14.55.25 RELr426 190762
# Run by pruth on Mon Nov 16 05:28:07 2026
#

# from driverUtils import executeOnCaeGraphicsStartup
# executeOnCaeGraphicsStartup()
#: Executing "onCaeGraphicsStartup()" in the site directory ...
from abaqus import *
from abaqusConstants import *
session.Viewport(name='Viewport: 1', origin=(1.36133, 1.36458), width=200.387, 
    height=135.367)
session.viewports['Viewport: 1'].makeCurrent()
from driverUtils import executeOnCaeStartup
executeOnCaeStartup()
execfile('scripts/remeshing/run_f1806_case2_distal_remesh.py', 
    __main__.__dict__)
#: === Task F1806: Case 2 Outermost Distal Native-MISESERI Target Sensitivity at 1.8% ===
#: Donor ODB: D:\Master thesis\Adaptive remeshing\models\pandey_kumar_mode1\254_f1804_case2_distal_recovery\PK_HOLE_STATE_POSTBREACH_RECOVERY.odb (7417896 bytes, SHA-256 35E9DC19B1E0A4F5EE5FB3547C9C71004D8882DC50F729C8A8F4CA8A4D50A959)
#: Loaded config: error_target=1.80%, min_h=0.0015 mm, max_h=0.0200 mm, variable=MISESERI, step=RECOVERY_STEP
#: 
#: --- Executing Native Abaqus adaptiveRemesh() (error_target = 1.8%) ---
#: The model "Model_F1806_Case2_Distal_Sensitivity" has been created.
#: Model: D:/Master thesis/Adaptive remeshing/models/pandey_kumar_mode1/254_f1804_case2_distal_recovery/PK_HOLE_STATE_POSTBREACH_RECOVERY.odb
#: Number of Assemblies:         1
#: Number of Assembly instances: 0
#: Number of Part instances:     1
#: Number of Meshes:             1
#: Number of Element Sets:       2910
#: Number of Node Sets:          5
#: Number of Steps:              1
#: Model: D:/Master thesis/Adaptive remeshing/models/pandey_kumar_mode1/254_f1804_case2_distal_recovery/PK_HOLE_STATE_POSTBREACH_RECOVERY.odb
#: Number of Assemblies:         1
#: Number of Assembly instances: 0
#: Number of Part instances:     1
#: Number of Meshes:             1
#: Number of Element Sets:       2910
#: Number of Node Sets:          5
#: Number of Steps:              1
#: Native remesh completed: raw INP = D:\Master thesis\Adaptive remeshing\runs\f1806_case2_distal_1p8pct\PK_F1806_CASE_2_ADAPT_PHYS.inp
#: Target physical INP saved: D:\Master thesis\Adaptive remeshing\models\pandey_kumar_mode1\256_f1806_case2_distal_1p8pct\PK_F1806_CASE_2_ADAPT_PHYS.inp (1649217 bytes, SHA-256 35CD501EC545F1885B129152E36E574DE0112404B458AFA86F75EFDE9186DF74)
#: Mesh Body SHA-256: 35178C924EB5652DD57991AAD34C4CCB436D5C6F6F132E3704B7D9AFF2F1955A
#: 
#: --- Auditing Finite Element Mesh Quality ---
#: Audit Results:
#:   Total Elements:       22924
#:   Quadrilaterals:       22346 (97.48%)
#:   Triangles:            578
#:   Min Signed det(J):    2.869789e-07
#:   Nonpositive det(J):   0
#:   Max Aspect Ratio:     2.500
#:   Median Aspect Ratio:  1.210
#:   AR Violations (>4.0): 0
#:   Min Corner Angle:     31.37 deg
#:   Max Corner Angle:     138.48 deg
#: 
#: --- Profiling Spatial Sizing Distribution on F1806 ---
#: Profiling F1795 baseline mesh...
#: Profiling F1804 predecessor mesh...
#: Profiling F1805 predecessor mesh...
#: 
#: Broad Distal Corridor (x in [0.75, 1.00], y in [0.55, 0.75]):
#:   Elements:             6581
#:   Mean h:               0.002551 mm (2.55 um)
#:   Min h (sqrt(area)):   0.000768 mm (0.77 um)
#:   Min Edge Length:      0.000975 mm (0.98 um)
#:   Max Edge Length:      0.009240 mm (9.24 um)
#:   % <= l0 (Count):      99.98%
#:   % <= l0/2 (Count):    89.41%
#:   % <= l0/2 (Area):     63.42%
#: 
#: Distal Sub-Bins (Count %% <= l0/2 | Area %% <= l0/2 | Min h | Min Edge):
#:   x_0_75_to_0_80           : 2402 elems | Count <= l0/2: 100.00% | Area <= l0/2: 100.00% | Min h: 0.7676 um | Min Edge: 0.9752 um
#:   x_0_80_to_0_85           : 1956 elems | Count <= l0/2:  99.03% | Area <= l0/2:  97.16% | Min h: 0.7844 um | Min Edge: 1.0498 um
#:   x_0_85_to_0_90           : 1345 elems | Count <= l0/2:  96.58% | Area <= l0/2:  92.56% | Min h: 0.9363 um | Min Edge: 1.2668 um
#:   x_0_90_to_0_95           :  566 elems | Count <= l0/2:  41.70% | Area <= l0/2:  26.02% | Min h: 1.7166 um | Min Edge: 2.0100 um
#:   x_0_95_to_1_00           :  312 elems | Count <= l0/2:   3.21% | Area <= l0/2:   1.05% | Min h: 2.1403 um | Min Edge: 2.6453 um
#:   combined_x_0_90_to_1_00  :  878 elems | Count <= l0/2:  28.02% | Area <= l0/2:  13.55% | Min h: 1.7166 um | Min Edge: 2.0100 um
#: 
#: Primary Corridor (x in [0.50, 0.65], y in [0.45, 0.65]):
#:   Elements:             1055
#:   Mean h:               0.004363 mm (4.36 um)
#:   % <= l0/2 (Count):    35.36%
#: 
#: Far-Field Coarsening:
#:   Far-to-Distal Ratio:  4.20 x (Target >= 2.0x)
#: 
#: Global Element Sizing Bounds Semantics Audit:
#:   Global min h = sqrt(area): 0.000768 mm (0.768 um)
#:   Global min edge length:    0.000975 mm (0.975 um)
#:   Config min_element_size:   0.001500 mm (1.500 um)
#: 
#: Gate Evaluations:
#:   GATE_01_NATIVE_EXECUTION_EXIT_0:     PASS
#:   GATE_02_QUAD_FRACTION_GE_90_PCT:     PASS
#:   GATE_03_ZERO_NEGATIVE_JACOBIANS:     PASS
#:   GATE_04_ASPECT_RATIO_LE_4:           PASS
#:   GATE_05_DISTAL_CORRIDOR_RESOLUTION:  PASS
#:   GATE_06_FAR_FIELD_COARSENING:        PASS
#:   GATE_07_COMPUTATIONAL_EFFICIENCY:    PASS
#:   SCIENTIFIC_GATE_OUTER_DISTAL:        FAIL (28.02% <= l0/2, threshold 50.0%)
