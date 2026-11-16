# -*- coding: mbcs -*-
#
# Abaqus/CAE Release 2024 replay file
# Internal Version: 2023_09_21-14.55.25 RELr426 190762
# Run by pruth on Mon Nov 16 04:48:00 2026
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
execfile('scripts/remeshing/run_f1805_case2_distal_remesh.py', 
    __main__.__dict__)
#: === Task F1805: Case 2 Outermost Distal Native-MISESERI Target Sensitivity ===
#: Donor ODB: D:\Master thesis\Adaptive remeshing\models\pandey_kumar_mode1\254_f1804_case2_distal_recovery\PK_HOLE_STATE_POSTBREACH_RECOVERY.odb (7417896 bytes, SHA-256 35E9DC19B1E0A4F5EE5FB3547C9C71004D8882DC50F729C8A8F4CA8A4D50A959)
#: Loaded config: error_target=1.90%, min_h=0.0015 mm, max_h=0.0200 mm, variable=MISESERI, step=RECOVERY_STEP
#: 
#: --- Executing Native Abaqus adaptiveRemesh() (error_target = 1.9%) ---
#: The model "Model_F1805_Case2_Distal_Sensitivity" has been created.
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
#: Native remesh completed: raw INP = D:\Master thesis\Adaptive remeshing\runs\f1805_case2_distal_sensitivity\PK_F1805_CASE_2_ADAPT_PHYS.inp
#: Target physical INP saved: D:\Master thesis\Adaptive remeshing\models\pandey_kumar_mode1\255_f1805_case2_distal_sensitivity\PK_F1805_CASE_2_ADAPT_PHYS.inp (1459541 bytes, SHA-256 4DA79E199FE7A9F8C6EBA54B2BCBD49A79573357B577F80259E3C3120D6CD8FD)
#: Mesh Body SHA-256: E0F6A5C6D8DF0C879E1E9990302C6FB06E0D156CA5B9BB0236EEC0F5880980D3
#: 
#: --- Auditing Finite Element Mesh Quality ---
#: Audit Results:
#:   Total Elements:       20281
#:   Quadrilaterals:       19744 (97.35%)
#:   Triangles:            537
#:   Min Signed det(J):    1.306679e-07
#:   Nonpositive det(J):   0
#:   Max Aspect Ratio:     2.687
#:   Median Aspect Ratio:  1.201
#:   AR Violations (>4.0): 0
#:   Min Corner Angle:     31.78 deg
#:   Max Corner Angle:     144.17 deg
#: 
#: --- Profiling Spatial Sizing Distribution on F1805 ---
#: Profiling F1795 baseline mesh...
#: Profiling F1804 predecessor mesh...
#: 
#: Broad Distal Corridor (x in [0.75, 1.00], y in [0.55, 0.75]):
#:   Elements:             5902
#:   Mean h:               0.002669 mm (2.67 um)
#:   Min h:                0.000500 mm (0.50 um)
#:   % <= l0 (Count):      99.81%
#:   % <= l0/2 (Count):    86.28%
#:   % <= l0/2 (Area):     56.35%
#: 
#: Distal Sub-Bins (Count %% <= l0/2 | Area %% <= l0/2):
#:   x_0_75_to_0_80           : 2281 elems | Count <= l0/2:  99.91% | Area <= l0/2:  99.70% | Min h: 0.5003 um
#:   x_0_80_to_0_85           : 1742 elems | Count <= l0/2:  97.36% | Area <= l0/2:  92.59% | Min h: 0.7956 um
#:   x_0_85_to_0_90           : 1138 elems | Count <= l0/2:  89.10% | Area <= l0/2:  78.01% | Min h: 1.1559 um
#:   x_0_90_to_0_95           :  477 elems | Count <= l0/2:  21.59% | Area <= l0/2:  11.21% | Min h: 1.7617 um
#:   x_0_95_to_1_00           :  264 elems | Count <= l0/2:   0.00% | Area <= l0/2:   0.00% | Min h: 3.7890 um
#:   combined_x_0_90_to_1_00  :  741 elems | Count <= l0/2:  13.90% | Area <= l0/2:   5.65% | Min h: 1.7617 um
#: 
#: Primary Corridor (x in [0.50, 0.65], y in [0.45, 0.65]):
#:   Elements:             953
#:   Mean h:               0.004593 mm (4.59 um)
#:   % <= l0/2 (Count):    34.31%
#: 
#: Far-Field Coarsening:
#:   Far-to-Distal Ratio:  4.20 x (Target >= 2.0x)
#: 
#: Gate Evaluations:
#:   GATE_01_NATIVE_EXECUTION_EXIT_0:     PASS
#:   GATE_02_QUAD_FRACTION_GE_90_PCT:     PASS
#:   GATE_03_ZERO_NEGATIVE_JACOBIANS:     PASS
#:   GATE_04_ASPECT_RATIO_LE_4:           PASS
#:   GATE_05_DISTAL_CORRIDOR_RESOLUTION:  PASS
#:   GATE_06_FAR_FIELD_COARSENING:        PASS
#:   GATE_07_COMPUTATIONAL_EFFICIENCY:    PASS
#:   SCIENTIFIC_GATE_OUTER_DISTAL:        FAIL (13.90% <= l0/2, threshold 50.0%)
