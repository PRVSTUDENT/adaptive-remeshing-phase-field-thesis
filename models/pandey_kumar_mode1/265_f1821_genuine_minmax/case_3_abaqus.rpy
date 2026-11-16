# -*- coding: mbcs -*-
#
# Abaqus/CAE Release 2024 replay file
# Internal Version: 2023_09_21-14.55.25 RELr426 190762
# Run by pruth on Mon Nov 16 15:47:02 2026
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
execfile(
    'D:/Master thesis/Adaptive remeshing/scripts/remeshing/run_f1821_genuine_minmax_single.py', 
    __main__.__dict__)
#: 
#: ================================================================================
#: TASK F1821 GENUINE MINIMUM_MAXIMUM SIZING: CASE_3 (Case 3: Notched Plate with Pins and Central Hole)
#:   Executing RemeshingRule with sizingMethod=MINIMUM_MAXIMUM
#:   max_solution_error_target = 1.0%, min_solution_error_target = 5.0%, mesh_bias = 7
#:   Output dir: D:\Master thesis\Adaptive remeshing\models\pandey_kumar_mode1\265_f1821_genuine_minmax
#: ================================================================================
#: The model "Model_MethodA_case_3" has been created.
#: Model: D:/Master thesis/Adaptive remeshing/models/pandey_kumar_mode1/259_f1809_multistate_recovery/case3/SEC43_MULTISTATE_RECOVERY.odb
#: Number of Assemblies:         1
#: Number of Assembly instances: 0
#: Number of Part instances:     1
#: Number of Meshes:             1
#: Number of Element Sets:       3927
#: Number of Node Sets:          4
#: Number of Steps:              1
#: Model: D:/Master thesis/Adaptive remeshing/models/pandey_kumar_mode1/259_f1809_multistate_recovery/case3/SEC43_MULTISTATE_RECOVERY.odb
#: Number of Assemblies:         1
#: Number of Assembly instances: 0
#: Number of Part instances:     1
#: Number of Meshes:             1
#: Number of Element Sets:       3927
#: Number of Node Sets:          4
#: Number of Steps:              1
#:   Total Elements: 87786 (Quads: 85480 = 97.37%, Tris: 2306)
#:   Min det(J): 6.64e-04, Max AR: 2.93
#:   Gate 06 Coarsening: 1.53x (Gate: FAIL)
#:   Scientific Gate (SCIENTIFIC_GATE_SECONDARY_CORRIDOR): 96.50% (Gate: PASS)
#:   Width metrics (h <= l0/2): Total fine = 26474
#:     Within 2*l0: 172 (0.65%)
#:     Within 3*l0: 281 (1.06%)
#:     Within 5*l0: 434 (1.64%)
print('RT script done')
#: RT script done
