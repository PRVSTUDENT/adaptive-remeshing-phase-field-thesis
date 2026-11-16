# -*- coding: mbcs -*-
#
# Abaqus/CAE Release 2024 replay file
# Internal Version: 2023_09_21-14.55.25 RELr426 190762
# Run by pruth on Mon Nov 16 10:20:45 2026
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
#: RUNNING CASE 1: MODE-I EDGE-CRACKED PLATE (METHOD A.2 MULTI-STATE RECOVERY) AT ERROR TARGET 4.50%
#: Output directory: D:\Master thesis\Adaptive remeshing\models\pandey_kumar_mode1\261_f1812_crack_path_refinement\case1
#: Job name:         PK_F1812_CASE_1
#: ================================================================================
#: Donor ODB verified: PK_CASE1_MULTISTATE_RECOVERY.odb (SHA: 0A25CDFE64344BE9DF7C651802F46EBF3D6F85C445689BBD28DBA64157758117)
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
#: Generated physical mesh: D:\Master thesis\Adaptive remeshing\models\pandey_kumar_mode1\261_f1812_crack_path_refinement\case1\PK_F1812_CASE_1_PHYS.inp
#:   [AUDIT] Elements: 25461 (Quads: 24770, Tris: 691, Quad %: 97.29%)
#:   [AUDIT] Min signed det(J): 1.90583e-07, Max AR: 2.632, Coarsening: 2.39x
#:   [CRITICAL] Full Ligament: 3664, %<=l0: 100.00%, %<=l0/2: 97.19%, Outer %<=l0/2: 100.00% (Gate: PASS)
#: Receipt written: models/pandey_kumar_mode1/261_f1812_crack_path_refinement/case1/PK_F1812_CASE_1_RECEIPT.json
