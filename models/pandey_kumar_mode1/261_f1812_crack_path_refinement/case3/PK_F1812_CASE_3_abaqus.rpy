# -*- coding: mbcs -*-
#
# Abaqus/CAE Release 2024 replay file
# Internal Version: 2023_09_21-14.55.25 RELr426 190762
# Run by pruth on Mon Nov 16 10:21:55 2026
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
    'D:/Master thesis/Adaptive remeshing/scripts/remeshing/run_f1812_single_target.py', 
    __main__.__dict__)
#: ================================================================================
#: RUNNING CASE 3: NOTCHED PLATE WITH HOLE AND PINS (METHOD A.2 MULTI-STATE RECOVERY) AT ERROR TARGET 3.00%
#: Output directory: D:\Master thesis\Adaptive remeshing\models\pandey_kumar_mode1\261_f1812_crack_path_refinement\case3
#: Job name:         PK_F1812_CASE_3
#: ================================================================================
#: Donor ODB verified: SEC43_MULTISTATE_RECOVERY.odb (SHA: C67C0DEE132B31B53FDF7C2DF4C1D232AD92D42E9AFB29F5CD8313C269CF9780)
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
#: Generated physical mesh: D:\Master thesis\Adaptive remeshing\models\pandey_kumar_mode1\261_f1812_crack_path_refinement\case3\PK_F1812_CASE_3_PHYS.inp
#:   [AUDIT] Elements: 77779 (Quads: 75708, Tris: 2071, Quad %: 97.34%)
#:   [AUDIT] Min signed det(J): 0.00106939, Max AR: 2.659, Coarsening: 1.65x
#:   [CRITICAL] Secondary Corridor: 12638, % <= l0: 93.84% (Gate: PASS)
#: Receipt written: models/pandey_kumar_mode1/261_f1812_crack_path_refinement/case3/PK_F1812_CASE_3_RECEIPT.json
