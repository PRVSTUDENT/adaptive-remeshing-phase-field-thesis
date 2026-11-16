# -*- coding: mbcs -*-
#
# Abaqus/CAE Release 2024 replay file
# Internal Version: 2023_09_21-14.55.25 RELr426 190762
# Run by pruth on Mon Nov 16 02:13:02 2026
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
execfile('scripts/remeshing/run_f1800_case3_precritical_remesh.py', 
    __main__.__dict__)
#: === Task F1800: Case 3 Precritical Native-MISESERI Scale and Causal Remesh Test ===
#: Verifying causal configuration schema...
#: PASS: Causal configuration verified (causal_mode=True, max_frame_index=1, max_frame_time=1.0)
#: Precritical Case 3 Donor: D:\Master thesis\Adaptive remeshing\models\pandey_kumar_mode1\250_f1800_case3_precritical_remesh\PK_SEC43_PRECRITICAL_RECOVERY.odb (1498500 bytes, SHA-256: 02663A609E96670F41774C153AB31D75C6F170CFFA41E5B99DD3DD036610929B)
#: Model: D:/Master thesis/Adaptive remeshing/runs/f1800_case3_precritical_remesh/PK_SEC43_PRECRITICAL_RECOVERY_DONOR.odb
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
#: Saved Case 3 precritical donor qualification receipt: D:\Master thesis\Adaptive remeshing\models\pandey_kumar_mode1\250_f1800_case3_precritical_remesh\PK_F1800_CASE3_DONOR_QUALIFICATION_RECEIPT.json
#: 
#: --- Executing Abaqus Native Remeshing for Case 3 Precritical Donor ---
#: The model "Model_F1800_Case3_Native" has been created.
#: Model: D:/Master thesis/Adaptive remeshing/runs/f1800_case3_precritical_remesh/PK_SEC43_PRECRITICAL_RECOVERY_DONOR.odb
#: Number of Assemblies:         1
#: Number of Assembly instances: 0
#: Number of Part instances:     1
#: Number of Meshes:             1
#: Number of Element Sets:       4
#: Number of Node Sets:          5
#: Number of Steps:              1
#: Model: D:/Master thesis/Adaptive remeshing/runs/f1800_case3_precritical_remesh/PK_SEC43_PRECRITICAL_RECOVERY_DONOR.odb
#: Number of Assemblies:         1
#: Number of Assembly instances: 0
#: Number of Part instances:     1
#: Number of Meshes:             1
#: Number of Element Sets:       4
#: Number of Node Sets:          5
#: Number of Steps:              1
#: Generated Physical Mesh INP: D:\Master thesis\Adaptive remeshing\models\pandey_kumar_mode1\250_f1800_case3_precritical_remesh\PK_F1800_CASE_3_ADAPT_PHYS.inp (1942364 bytes, SHA-256: 921B6E657E2654E92A59C066A8ADD2724B8970E54E29E807EBEEC29BACAB0664)
#: Generated Physical Mesh Body SHA-256: 0DAFAD93742A4988AF068070F7BFE72FE71CD3C353506C346584A208E71EF6AC
#: Saved Case 3 precritical remesh receipt: D:\Master thesis\Adaptive remeshing\models\pandey_kumar_mode1\250_f1800_case3_precritical_remesh\PK_F1800_CASE3_PRECRITICAL_REMESH_RECEIPT.json
