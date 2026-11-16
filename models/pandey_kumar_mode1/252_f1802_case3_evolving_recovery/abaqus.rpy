# -*- coding: mbcs -*-
#
# Abaqus/CAE Release 2024 replay file
# Internal Version: 2023_09_21-14.55.25 RELr426 190762
# Run by pruth on Mon Nov 16 03:02:24 2026
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
execfile('scripts/remeshing/run_f1802_case3_evolving_recovery.py', 
    __main__.__dict__)
#: === Task F1802: Case 3 Method A.2 Evolving Recovery Donor Qualification and Remesh ===
#: Verifying causal configuration schema and test parameters...
#: PASS: Configuration verified (causal_mode=True, max_frame_index=1, max_frame_time=1.0, error_target=3.0%)
#: Case 3 Evolving Donor: D:\Master thesis\Adaptive remeshing\models\pandey_kumar_mode1\198_pk_sec43_coupled_validation\SEC43_STATE2_HOLE_ARREST.odb (1676760 bytes, SHA-256: 8ED4E4189A1B1EBA4E8D39DA6FB8C6A9CBE22C9D1227E235C52F4679B4821AD1)
#: Model: D:/Master thesis/Adaptive remeshing/runs/f1802_case3_evolving_recovery/SEC43_STATE2_HOLE_ARREST_DONOR.odb
#: Number of Assemblies:         1
#: Number of Assembly instances: 0
#: Number of Part instances:     1
#: Number of Meshes:             1
#: Number of Element Sets:       23
#: Number of Node Sets:          4
#: Number of Steps:              1
#: Model: D:/Master thesis/Adaptive remeshing/models/pandey_kumar_mode1/198_pk_sec43_coupled_validation/SEC43_STATE2_HOLE_ARREST.odb
#: Number of Assemblies:         1
#: Number of Assembly instances: 0
#: Number of Part instances:     1
#: Number of Meshes:             1
#: Number of Element Sets:       23
#: Number of Node Sets:          4
#: Number of Steps:              1
#: Saved Case 3 donor qualification receipt: D:\Master thesis\Adaptive remeshing\models\pandey_kumar_mode1\252_f1802_case3_evolving_recovery\PK_F1802_CASE3_DONOR_QUALIFICATION_RECEIPT.json
#: 
#: --- Executing Abaqus Native Remeshing for Case 3 (Method A.2 Evolving Donor, error_target = 3.0%%) ---
#: The model "Model_F1802_Case3_Native" has been created.
#: Model: D:/Master thesis/Adaptive remeshing/runs/f1802_case3_evolving_recovery/SEC43_STATE2_HOLE_ARREST_DONOR.odb
#: Number of Assemblies:         1
#: Number of Assembly instances: 0
#: Number of Part instances:     1
#: Number of Meshes:             1
#: Number of Element Sets:       23
#: Number of Node Sets:          4
#: Number of Steps:              1
#: Model: D:/Master thesis/Adaptive remeshing/runs/f1802_case3_evolving_recovery/SEC43_STATE2_HOLE_ARREST_DONOR.odb
#: Number of Assemblies:         1
#: Number of Assembly instances: 0
#: Number of Part instances:     1
#: Number of Meshes:             1
#: Number of Element Sets:       23
#: Number of Node Sets:          4
#: Number of Steps:              1
#: Generated Physical Mesh INP: D:\Master thesis\Adaptive remeshing\models\pandey_kumar_mode1\252_f1802_case3_evolving_recovery\PK_F1802_CASE_3_ADAPT_PHYS.inp (2006768 bytes, SHA-256: 251ECD959A5127BC4A2003E496314FE808408B2AC5CE38E124DF10C4AF0E3C46)
#: Generated Physical Mesh Body SHA-256: 34B036E40307C9A4A38F674309B9DA64EF20C4CD23A6212CAFCFC61F55F44D28
#: Saved Case 3 evolving remesh receipt: D:\Master thesis\Adaptive remeshing\models\pandey_kumar_mode1\252_f1802_case3_evolving_recovery\PK_F1802_CASE3_EVOLVING_REMESH_RECEIPT.json
