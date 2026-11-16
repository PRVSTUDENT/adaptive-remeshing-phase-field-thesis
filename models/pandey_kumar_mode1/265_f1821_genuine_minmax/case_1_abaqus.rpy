# -*- coding: mbcs -*-
#
# Abaqus/CAE Release 2024 replay file
# Internal Version: 2023_09_21-14.55.25 RELr426 190762
# Run by pruth on Mon Nov 16 15:45:42 2026
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
#: TASK F1821 GENUINE MINIMUM_MAXIMUM SIZING: CASE_1 (Case 1: Mode-I Edge-Cracked Plate)
#:   Executing RemeshingRule with sizingMethod=MINIMUM_MAXIMUM
#:   max_solution_error_target = 1.0%, min_solution_error_target = 5.0%, mesh_bias = 7
#:   Output dir: D:\Master thesis\Adaptive remeshing\models\pandey_kumar_mode1\265_f1821_genuine_minmax
#: ================================================================================
#: The model "Model_MethodA_case_1" has been created.
#: Model: D:/Master thesis/Adaptive remeshing/models/pandey_kumar_mode1/261_f1812_crack_path_refinement/case1/PK_CASE1_MULTISTATE_RECOVERY.odb
#: Number of Assemblies:         1
#: Number of Assembly instances: 0
#: Number of Part instances:     1
#: Number of Meshes:             1
#: Number of Element Sets:       2910
#: Number of Node Sets:          4
#: Number of Steps:              1
#: Model: D:/Master thesis/Adaptive remeshing/models/pandey_kumar_mode1/261_f1812_crack_path_refinement/case1/PK_CASE1_MULTISTATE_RECOVERY.odb
#: Number of Assemblies:         1
#: Number of Assembly instances: 0
#: Number of Part instances:     1
#: Number of Meshes:             1
#: Number of Element Sets:       2910
#: Number of Node Sets:          4
#: Number of Steps:              1
#:   Total Elements: 63210 (Quads: 61519 = 97.32%, Tris: 1691)
#:   Min det(J): 1.03e-07, Max AR: 2.67
#:   Gate 06 Coarsening: 1.87x (Gate: FAIL)
#:   Scientific Gate (SCIENTIFIC_GATE_FULL_LIGAMENT): 100.00% (Gate: PASS)
#:   Width metrics (h <= l0/2): Total fine = 52069
#:     Within 2*l0: 5486 (10.54%)
#:     Within 3*l0: 8266 (15.88%)
#:     Within 5*l0: 14053 (26.99%)
print('RT script done')
#: RT script done
