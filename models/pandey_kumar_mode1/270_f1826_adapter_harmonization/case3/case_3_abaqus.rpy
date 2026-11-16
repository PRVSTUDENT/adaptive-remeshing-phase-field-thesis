# -*- coding: mbcs -*-
#
# Abaqus/CAE Release 2024 replay file
# Internal Version: 2023_09_21-14.55.25 RELr426 190762
# Run by pruth on Mon Nov 16 23:50:21 2026
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
#: --- [F1826 Single] Case: case_3 | Target: 3.00% ---
#:   Donor ODB SHA-256: C67C0DEE132B31B53FDF7C2DF4C1D232AD92D42E9AFB29F5CD8313C269CF9780
#: The model "Model_F1826_CASE_3" has been created.
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
#:   Generated INP: models/pandey_kumar_mode1/270_f1826_adapter_harmonization/case3/PK_F1826_CASE_3_ADAPT_PHYS.inp
#:   INP Whole SHA: 819452A3F0C13F2EFB710078C55B4BA733EEA72A6E783C1C8A7D0702CB4F5B0F
#:   INP Body  SHA: 08FA694A09033EC1F6BDE1C9150F539B3379BE7DF75CAAAD5DED3D42937FA2B4
