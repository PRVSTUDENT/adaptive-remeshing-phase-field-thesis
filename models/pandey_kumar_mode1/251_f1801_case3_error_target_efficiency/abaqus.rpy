# -*- coding: mbcs -*-
#
# Abaqus/CAE Release 2024 replay file
# Internal Version: 2023_09_21-14.55.25 RELr426 190762
# Run by pruth on Mon Nov 16 02:34:43 2026
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
execfile('scripts/remeshing/run_f1801_case3_error_target_efficiency.py', 
    __main__.__dict__)
#: === Task F1801: Case 3 Native-MISESERI Error-Target Efficiency Test ===
#: Verifying causal configuration schema and test parameters...
#: PASS: Configuration verified (causal_mode=True, max_frame_index=1, max_frame_time=1.0, error_target=5.0%)
#: Case 3 Recovery Donor: D:\Master thesis\Adaptive remeshing\models\pandey_kumar_mode1\250_f1800_case3_precritical_remesh\PK_SEC43_PRECRITICAL_RECOVERY.odb (1498500 bytes, SHA-256: 02663A609E96670F41774C153AB31D75C6F170CFFA41E5B99DD3DD036610929B)
#: Model: D:/Master thesis/Adaptive remeshing/runs/f1801_case3_error_target_efficiency/PK_SEC43_PRECRITICAL_RECOVERY_DONOR.odb
#: Number of Assemblies:         1
#: Number of Assembly instances: 0
#: Number of Part instances:     1
#: Number of Meshes:             1
#: Number of Element Sets:       4
#: Number of Node Sets:          5
#: Number of Steps:              1
#: Model: D:/Master thesis/Adaptive remeshing/models/pandey_kumar_mode1/250_f1800_case3_precritical_remesh/PK_SEC43_PRECRITICAL_RECOVERY.odb
#: Number of Assemblies:         1
#: Number of Assembly instances: 0
#: Number of Part instances:     1
#: Number of Meshes:             1
#: Number of Element Sets:       4
#: Number of Node Sets:          5
#: Number of Steps:              1
#: Saved Case 3 donor qualification receipt: D:\Master thesis\Adaptive remeshing\models\pandey_kumar_mode1\251_f1801_case3_error_target_efficiency\PK_F1801_CASE3_DONOR_QUALIFICATION_RECEIPT.json
#: 
#: --- Executing Abaqus Native Remeshing for Case 3 (error_target = 5.0%%) ---
#: The model "Model_F1801_Case3_Native" has been created.
#: Model: D:/Master thesis/Adaptive remeshing/runs/f1801_case3_error_target_efficiency/PK_SEC43_PRECRITICAL_RECOVERY_DONOR.odb
#: Number of Assemblies:         1
#: Number of Assembly instances: 0
#: Number of Part instances:     1
#: Number of Meshes:             1
#: Number of Element Sets:       4
#: Number of Node Sets:          5
#: Number of Steps:              1
#: Model: D:/Master thesis/Adaptive remeshing/runs/f1801_case3_error_target_efficiency/PK_SEC43_PRECRITICAL_RECOVERY_DONOR.odb
#: Number of Assemblies:         1
#: Number of Assembly instances: 0
#: Number of Part instances:     1
#: Number of Meshes:             1
#: Number of Element Sets:       4
#: Number of Node Sets:          5
#: Number of Steps:              1
#: Generated Physical Mesh INP: D:\Master thesis\Adaptive remeshing\models\pandey_kumar_mode1\251_f1801_case3_error_target_efficiency\PK_F1801_CASE_3_ADAPT_PHYS.inp (622577 bytes, SHA-256: D3D4B876D76613611DB9B7DCF8BF48B5CE489DBB7D6A032BC92F5D329E6B96A4)
#: Generated Physical Mesh Body SHA-256: AF53DCD3E2877FDA3ABB4271CB275D73E16D802D9CC32593EC25C6D234581BB1
#: Saved Case 3 error target receipt: D:\Master thesis\Adaptive remeshing\models\pandey_kumar_mode1\251_f1801_case3_error_target_efficiency\PK_F1801_CASE3_ERROR_TARGET_RECEIPT.json
