# -*- coding: mbcs -*-
#
# Abaqus/CAE Release 2024 replay file
# Internal Version: 2023_09_21-14.55.25 RELr426 190762
# Run by pruth on Mon Nov 16 04:20:11 2026
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
execfile('scripts/remeshing/run_f1804_case2_distal_remesh.py', 
    __main__.__dict__)
#: === Task F1804: Case 2 Distal Degraded-Modulus Recovery Native Remesh ===
#: Donor ODB: D:\Master thesis\Adaptive remeshing\models\pandey_kumar_mode1\254_f1804_case2_distal_recovery\PK_HOLE_STATE_POSTBREACH_RECOVERY.odb (7417896 bytes, SHA-256 35E9DC19B1E0A4F5EE5FB3547C9C71004D8882DC50F729C8A8F4CA8A4D50A959)
#: Loaded config: error_target=2.30%, min_h=0.0015 mm, max_h=0.0200 mm, variable=MISESERI, step=RECOVERY_STEP
#: 
#: --- Executing Native Abaqus adaptiveRemesh() ---
#: The model "Model_F1804_Case2_Distal" has been created.
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
#: Native remesh completed: raw INP = D:\Master thesis\Adaptive remeshing\runs\f1804_case2_distal_recovery\PK_F1804_CASE_2_ADAPT_PHYS.inp
#: Target physical INP saved: D:\Master thesis\Adaptive remeshing\models\pandey_kumar_mode1\254_f1804_case2_distal_recovery\PK_F1804_CASE_2_ADAPT_PHYS.inp (942941 bytes, SHA-256 FDDA676278B096D66C1392528921BE8E3DC54CB3C1B822BD038AA17F855E43E8)
#: Mesh Body SHA-256: E562D18AA3558DD4B48F71FFC225934DADF9090D850D56F79984DAA4ADA0293B
#: 
#: --- Auditing Finite Element Mesh Quality ---
#: Audit Results:
#:   Total Elements:       13061
#:   Quadrilaterals:       12699 (97.23%)
#:   Triangles:            362
#:   Min Signed det(J):    3.595125e-07
#:   Nonpositive det(J):   0
#:   Max Aspect Ratio:     2.121
#:   Median Aspect Ratio:  1.209
#:   AR Violations (>4.0): 0
#:   Min Corner Angle:     34.28 deg
#:   Max Corner Angle:     135.07 deg
#: 
#: --- Profiling Spatial Sizing Distribution ---
#: Primary Corridor (Notch to Hole):
#:   Elements:             636
#:   Mean h:               0.005666 mm (5.67 um)
#:   Min h:                0.002349 mm (2.35 um)
#:   % <= l0:             89.94%
#:   % <= l0/2:           7.08%
#: 
#: Outer Distal Corridor (Hole to Right Boundary):
#:   Elements:             3609
#:   Mean h:               0.003363 mm (3.36 um)
#:   Min h:                0.000808 mm (0.81 um)
#:   % <= l0:             96.87%
#:   % <= l0/2:           72.10% (F1795 pre-analysis baseline: 66.34%)
#: 
#: Far Field Background:
#:   Elements:             628
#:   Mean h:               0.012213 mm (12.21 um)
#:   Far-to-Distal Ratio:  3.63 x (Target >= 2.0x)
