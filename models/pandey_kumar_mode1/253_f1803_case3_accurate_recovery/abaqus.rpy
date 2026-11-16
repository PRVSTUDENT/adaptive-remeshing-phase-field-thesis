# -*- coding: mbcs -*-
#
# Abaqus/CAE Release 2024 replay file
# Internal Version: 2023_09_21-14.55.25 RELr426 190762
# Run by pruth on Mon Nov 16 03:36:57 2026
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
execfile('scripts/remeshing/run_f1803_case3_accurate_recovery_remesh.py', 
    __main__.__dict__)
#: === Task F1803: Case 3 State-2 Degraded Modulus Fidelity and Native Remesh ===
#: Verifying causal configuration schema and test parameters...
#: PASS: Configuration verified (causal_mode=True, max_frame_index=1, max_frame_time=1.0, error_target=3.0%)
#: Case 3 High-Fidelity Donor: D:\Master thesis\Adaptive remeshing\models\pandey_kumar_mode1\253_f1803_case3_accurate_recovery\SEC43_STATE2_HIGH_FIDELITY_RECOVERY.odb (9935692 bytes, SHA-256: 965136FD7AE637EFF44DEEDF4D152817037CF3C05656D9D1B6006377038362BB)
#: Model: D:/Master thesis/Adaptive remeshing/runs/f1803_case3_accurate_recovery/SEC43_STATE2_HIGH_FIDELITY_RECOVERY_DONOR.odb
#: Number of Assemblies:         1
#: Number of Assembly instances: 0
#: Number of Part instances:     1
#: Number of Meshes:             1
#: Number of Element Sets:       3927
#: Number of Node Sets:          4
#: Number of Steps:              1
#: Model: D:/Master thesis/Adaptive remeshing/models/pandey_kumar_mode1/253_f1803_case3_accurate_recovery/SEC43_STATE2_HIGH_FIDELITY_RECOVERY.odb
#: Number of Assemblies:         1
#: Number of Assembly instances: 0
#: Number of Part instances:     1
#: Number of Meshes:             1
#: Number of Element Sets:       3927
#: Number of Node Sets:          4
#: Number of Steps:              1
#: 
#: --- Executing Abaqus Native Remeshing for Case 3 (Method A.2 High-Fidelity Donor, error_target = 3.0%%) ---
#: The model "Model_F1803_Case3_Native" has been created.
#: Model: D:/Master thesis/Adaptive remeshing/runs/f1803_case3_accurate_recovery/SEC43_STATE2_HIGH_FIDELITY_RECOVERY_DONOR.odb
#: Number of Assemblies:         1
#: Number of Assembly instances: 0
#: Number of Part instances:     1
#: Number of Meshes:             1
#: Number of Element Sets:       3927
#: Number of Node Sets:          4
#: Number of Steps:              1
#: Model: D:/Master thesis/Adaptive remeshing/runs/f1803_case3_accurate_recovery/SEC43_STATE2_HIGH_FIDELITY_RECOVERY_DONOR.odb
#: Number of Assemblies:         1
#: Number of Assembly instances: 0
#: Number of Part instances:     1
#: Number of Meshes:             1
#: Number of Element Sets:       3927
#: Number of Node Sets:          4
#: Number of Steps:              1
#: Generated Physical Mesh INP: D:\Master thesis\Adaptive remeshing\models\pandey_kumar_mode1\253_f1803_case3_accurate_recovery\PK_F1803_CASE_3_ADAPT_PHYS.inp (1925805 bytes, SHA-256: A8CFA533697BAF4DF1E787CA46EE496490F39B8DB03F922EF108B729DDC08E4B)
#: Generated Physical Mesh Body SHA-256: 46024F3241F0C6C8B7BC1D051D52D1E00F53EFDABF3FFFB9160FD7E937912B9C
#: Saved Case 3 accurate remesh receipt: D:\Master thesis\Adaptive remeshing\models\pandey_kumar_mode1\253_f1803_case3_accurate_recovery\PK_F1803_CASE3_ACCURATE_REMESH_RECEIPT.json
