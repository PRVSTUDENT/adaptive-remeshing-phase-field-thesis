# -*- coding: mbcs -*-
#
# Abaqus/CAE Release 2024 replay file
# Internal Version: 2023_09_21-14.55.25 RELr426 190762
# Run by pruth on Mon Nov 16 06:42:44 2026
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
    'D:/Master thesis/Adaptive remeshing/scripts/remeshing/run_f1808_single_case.py', 
    __main__.__dict__)
#: DEBUG sys.argv: ['C:\\SIMULIA\\EstProducts\\2024\\win_b64\\code\\bin\\ABQcaeK.exe', '-cae', '-noGUI', 'D:\\Master thesis\\Adaptive remeshing\\scripts\\remeshing\\run_f1808_single_case.py', '-tmpdir', 'C:\\Users\\pruth\\AppData\\Local\\Temp', '-lmlog', 'ON', 'case_3']
#: ================================================================================
#: TASK F1808 SINGLE-CASE ISOLATED EXECUTION: Case 3: Notched Plate with Hole and Pins (State 2 Degraded Recovery)
#: ================================================================================
#:   Case ID:     case_3
#:   Config:      D:\Master thesis\Adaptive remeshing\configs\remeshing\f1808_case3_native_miseseri.json
#:   Donor:       D:\Master thesis\Adaptive remeshing\models\pandey_kumar_mode1\253_f1803_case3_accurate_recovery\SEC43_STATE2_HIGH_FIDELITY_RECOVERY.odb
#:   Output Dir:  D:\Master thesis\Adaptive remeshing\models\pandey_kumar_mode1\258_f1808_four_case_reproducibility\case3
#:   Donor SHA-256: 965136FD7AE637EFF44DEEDF4D152817037CF3C05656D9D1B6006377038362BB (9935692 bytes)
#: The model "Model_MethodA_case_3" has been created.
#: Model: D:/Master thesis/Adaptive remeshing/models/pandey_kumar_mode1/253_f1803_case3_accurate_recovery/SEC43_STATE2_HIGH_FIDELITY_RECOVERY.odb
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
#:   Generated physical mesh: D:\Master thesis\Adaptive remeshing\models\pandey_kumar_mode1\258_f1808_four_case_reproducibility\case3\PK_F1808_CASE_3_PHYS.inp
#:   Physical Mesh SHA-256: 83ED15E806818769B71915E1087ED084EDF2E5BB88CD6BCE4089190128C28D37
#:   Body SHA-256:          46024F3241F0C6C8B7BC1D051D52D1E00F53EFDABF3FFFB9160FD7E937912B9C
#:   Size:                  1925795 bytes
#:   [AUDIT] Total elements:      26746 (Quads: 26048, Tris: 698, Quad Fraction: 97.39%)
#:   [AUDIT] Min signed det(J):   0.00076502 (Nonpositive: 0)
#:   [AUDIT] Aspect Ratio:        max 3.862 (median 1.246, violations > 4.0: 0)
#:   [AUDIT] Corner Angles:       [25.40 deg, 146.81 deg]
#:   [AUDIT] Element Size (area): min 0.046961 mm, mean 0.404079 mm, max 1.797829 mm
#:   [AUDIT] Coarsening Ratio:    2.48x (Far: 0.423671 mm vs Core: 0.170898 mm)
#:   [CRITICAL] Primary corridor elements:   859 (le l0: 0.5%, le l0/2: 0.0%)
#:   [CRITICAL] Secondary corridor elements: 4410 (le l0: 58.3%, le l0/2: 2.4%, min h: 0.0738 mm)
#:   Saved case receipt: D:\Master thesis\Adaptive remeshing\models\pandey_kumar_mode1\258_f1808_four_case_reproducibility\case3\PK_F1808_CASE_3_RECEIPT.json
