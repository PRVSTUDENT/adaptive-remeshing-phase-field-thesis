# -*- coding: mbcs -*-
#
# Abaqus/CAE Release 2024 replay file
# Internal Version: 2023_09_21-14.55.25 RELr426 190762
# Run by pruth on Mon Nov 16 16:08:14 2026
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
    'D:/Master thesis/Adaptive remeshing/scripts/remeshing/run_f1822_control_verification.py', 
    __main__.__dict__)
#: 
#: ================================================================================
#: TASK F1822: UNIFORM_ERROR 3.0% CONTROL VERIFICATION FOR CASE 1
#:   Executing RemeshingRule with sizingMethod=UNIFORM_ERROR, errorTarget=3.0%
#:   Donor: D:\Master thesis\Adaptive remeshing\models\pandey_kumar_mode1\261_f1812_crack_path_refinement\case1\PK_CASE1_MULTISTATE_RECOVERY.odb
#:   Output dir: D:\Master thesis\Adaptive remeshing\models\pandey_kumar_mode1\266_f1822_uniform_error_control
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
#:   CONTROL RESULTS: Total Elements = 62611 (Quads: 60966 = 97.37%, Tris: 1645)
#:   Body SHA-256: D36603D89FF9D953395A176D8C327F097FE69E92469FA73F6CC3193426B6E768
#:   Min det(J): 1.20e-07, Max AR: 2.71
#:   Coarsening Ratio: 1.85x
#:   Full Ligament Gate: 100.00% (PASS)
print('RT script done')
#: RT script done
