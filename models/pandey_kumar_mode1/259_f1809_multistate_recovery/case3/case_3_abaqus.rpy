# -*- coding: mbcs -*-
#
# Abaqus/CAE Release 2024 replay file
# Internal Version: 2023_09_21-14.55.25 RELr426 190762
# Run by pruth on Mon Nov 16 08:07:59 2026
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
    'D:/Master thesis/Adaptive remeshing/scripts/remeshing/run_f1809_single_case.py', 
    __main__.__dict__)
#: DEBUG sys.argv: ['C:\\SIMULIA\\EstProducts\\2024\\win_b64\\code\\bin\\ABQcaeK.exe', '-cae', '-noGUI', 'D:\\Master thesis\\Adaptive remeshing\\scripts\\remeshing\\run_f1809_single_case.py', '-tmpdir', 'C:\\Users\\pruth\\AppData\\Local\\Temp', '-lmlog', 'ON', 'case_3']
#: ================================================================================
#: TASK F1809 SINGLE-CASE ISOLATED EXECUTION: Case 3: Notched Plate with Hole and Pins (Method A.2 Multi-State Recovery)
#: ================================================================================
#:   Case ID:     case_3
#:   Config:      D:\Master thesis\Adaptive remeshing\configs\remeshing\f1809_case3_native_miseseri.json
#:   Donor:       D:\Master thesis\Adaptive remeshing\models\pandey_kumar_mode1\259_f1809_multistate_recovery\case3\SEC43_MULTISTATE_RECOVERY.odb
#:   Output Dir:  D:\Master thesis\Adaptive remeshing\models\pandey_kumar_mode1\259_f1809_multistate_recovery\case3
#:   Donor SHA-256: C67C0DEE132B31B53FDF7C2DF4C1D232AD92D42E9AFB29F5CD8313C269CF9780 (10043772 bytes)
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
#:   Generated physical mesh: D:\Master thesis\Adaptive remeshing\models\pandey_kumar_mode1\259_f1809_multistate_recovery\case3\PK_F1809_CASE_3_PHYS.inp
#:   Physical Mesh SHA-256: 4B1E5F42BA7899D33473DB6960AA0C1FBEF86742233629B00BA3BC5AE5AAA6DD
#:   Body SHA-256:          08FA694A09033EC1F6BDE1C9150F539B3379BE7DF75CAAAD5DED3D42937FA2B4
#:   Size:                  5572384 bytes
#:   [AUDIT] Total elements:      77779 (Quads: 75708, Tris: 2071, Quad Fraction: 97.34%)
#:   [AUDIT] Min signed det(J):   0.00106939 (Nonpositive: 0)
#:   [AUDIT] Aspect Ratio:        max 2.659 (median 1.235, violations > 4.0: 0)
#:   [AUDIT] Corner Angles:       [24.33 deg, 141.94 deg]
#:   [AUDIT] Element Size (area): min 0.043456 mm, mean 0.256296 mm, max 1.570485 mm
#:   [AUDIT] Coarsening Ratio:    1.65x (Far: 0.260279 mm vs Core: 0.157388 mm)
#:   [CRITICAL] Primary corridor elements:   10654 (le l0: 72.6%, le l0/2: 23.9%)
#:   [CRITICAL] Secondary corridor elements: 12638 (le l0: 93.8%, le l0/2: 31.2%, min h: 0.0514 mm)
#:   Saved case receipt: D:\Master thesis\Adaptive remeshing\models\pandey_kumar_mode1\259_f1809_multistate_recovery\case3\PK_F1809_CASE_3_RECEIPT.json
