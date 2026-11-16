# -*- coding: mbcs -*-
#
# Abaqus/CAE Release 2024 replay file
# Internal Version: 2023_09_21-14.55.25 RELr426 190762
# Run by pruth on Mon Nov 16 23:47:57 2026
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
execfile('scripts/remeshing/run_f1826_single_target.py', __main__.__dict__)
#: --- [F1826 Single] Case: case_1 | Target: 4.50% ---
#:   Donor ODB SHA-256: 0A25CDFE64344BE9DF7C651802F46EBF3D6F85C445689BBD28DBA64157758117
#: The model "Model_F1826_CASE_1" has been created.
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
#:   Generated INP: models/pandey_kumar_mode1/270_f1826_adapter_harmonization/case1/PK_F1826_CASE_1_ADAPT_PHYS.inp
#:   INP Whole SHA: 54D9031E4E521E54B41FC6894F13472BE06B1728E8041FAC0FA0357A4B48D898
#:   INP Body  SHA: 50CB4E3C826D66C7BDAB7FEBEADF5254CDEE33B709B214E9714CD776B3CE379E
