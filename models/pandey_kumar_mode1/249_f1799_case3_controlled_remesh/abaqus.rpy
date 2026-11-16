# -*- coding: mbcs -*-
#
# Abaqus/CAE Release 2024 replay file
# Internal Version: 2023_09_21-14.55.25 RELr426 190762
# Run by pruth on Mon Nov 16 01:51:21 2026
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
execfile('scripts/remeshing/run_f1799_case3_controlled_remesh.py', 
    __main__.__dict__)
#: === Task F1799: Case 3 Causal Configuration & Physical-Donor Controlled Remeshing ===
#: Verifying causal configuration schema...
#: PASS: Causal configuration verified (causal_mode=True, max_frame_index=1, max_frame_time=1.0)
#: Authentic Case 3 Donor: D:\Master thesis\Adaptive remeshing\models\pandey_kumar_mode1\188_pk_sec43_hole_plate\PK_SEC43_COARSE_RECOVERY.odb (1498400 bytes, SHA-256: BDCC74908A7F85186E6CE4165851AB2061969BCEF84E370C41F5DEF63597E3F4)
#: Model: D:/Master thesis/Adaptive remeshing/runs/f1799_case3_controlled_remesh/PK_SEC43_COARSE_RECOVERY_DONOR.odb
#: Number of Assemblies:         1
#: Number of Assembly instances: 0
#: Number of Part instances:     1
#: Number of Meshes:             1
#: Number of Element Sets:       4
#: Number of Node Sets:          5
#: Number of Steps:              1
#: Model: D:/Master thesis/Adaptive remeshing/models/pandey_kumar_mode1/188_pk_sec43_hole_plate/PK_SEC43_COARSE_RECOVERY.odb
#: Number of Assemblies:         1
#: Number of Assembly instances: 0
#: Number of Part instances:     1
#: Number of Meshes:             1
#: Number of Element Sets:       4
#: Number of Node Sets:          5
#: Number of Steps:              1
#: Saved Case 3 donor qualification receipt: D:\Master thesis\Adaptive remeshing\models\pandey_kumar_mode1\249_f1799_case3_controlled_remesh\PK_F1799_CASE3_DONOR_QUALIFICATION_RECEIPT.json
#: 
#: --- Executing Abaqus Native Remeshing for Case 3 ---
#: The model "Model_F1799_Case3_Native" has been created.
#: Model: D:/Master thesis/Adaptive remeshing/runs/f1799_case3_controlled_remesh/PK_SEC43_COARSE_RECOVERY_DONOR.odb
#: Number of Assemblies:         1
#: Number of Assembly instances: 0
#: Number of Part instances:     1
#: Number of Meshes:             1
#: Number of Element Sets:       4
#: Number of Node Sets:          5
#: Number of Steps:              1
#: Model: D:/Master thesis/Adaptive remeshing/runs/f1799_case3_controlled_remesh/PK_SEC43_COARSE_RECOVERY_DONOR.odb
#: Number of Assemblies:         1
#: Number of Assembly instances: 0
#: Number of Part instances:     1
#: Number of Meshes:             1
#: Number of Element Sets:       4
#: Number of Node Sets:          5
#: Number of Steps:              1
#: Generated Physical Mesh INP: D:\Master thesis\Adaptive remeshing\models\pandey_kumar_mode1\249_f1799_case3_controlled_remesh\PK_F1799_CASE_3_ADAPT_PHYS.inp (1934333 bytes, SHA-256: C3B84ECAFEB93498EF7880006629FBDDEEA2B1D2744D8E393D57349CECC4B5C0)
#: Saved Case 3 controlled remesh receipt: D:\Master thesis\Adaptive remeshing\models\pandey_kumar_mode1\249_f1799_case3_controlled_remesh\PK_F1799_CASE3_CONTROLLED_REMESH_RECEIPT.json
