# -*- coding: mbcs -*-
#
# Abaqus/CAE Release 2024 replay file
# Internal Version: 2023_09_21-14.55.25 RELr426 190762
# Run by pruth on Mon Nov 16 06:42:12 2026
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
#: DEBUG sys.argv: ['C:\\SIMULIA\\EstProducts\\2024\\win_b64\\code\\bin\\ABQcaeK.exe', '-cae', '-noGUI', 'D:\\Master thesis\\Adaptive remeshing\\scripts\\remeshing\\run_f1808_single_case.py', '-tmpdir', 'C:\\Users\\pruth\\AppData\\Local\\Temp', '-lmlog', 'ON', 'case_2']
#: ================================================================================
#: TASK F1808 SINGLE-CASE ISOLATED EXECUTION: Case 2: Plate with an Off-Axis Hole (F1806 Baseline)
#: ================================================================================
#:   Case ID:     case_2
#:   Config:      D:\Master thesis\Adaptive remeshing\configs\remeshing\f1808_case2_native_miseseri.json
#:   Donor:       D:\Master thesis\Adaptive remeshing\models\pandey_kumar_mode1\254_f1804_case2_distal_recovery\PK_HOLE_STATE_POSTBREACH_RECOVERY.odb
#:   Output Dir:  D:\Master thesis\Adaptive remeshing\models\pandey_kumar_mode1\258_f1808_four_case_reproducibility\case2
#:   Donor SHA-256: 35E9DC19B1E0A4F5EE5FB3547C9C71004D8882DC50F729C8A8F4CA8A4D50A959 (7417896 bytes)
#: The model "Model_MethodA_case_2" has been created.
#: Model: D:/Master thesis/Adaptive remeshing/models/pandey_kumar_mode1/254_f1804_case2_distal_recovery/PK_HOLE_STATE_POSTBREACH_RECOVERY.odb
#: Number of Assemblies:         1
#: Number of Assembly instances: 0
#: Number of Part instances:     1
#: Number of Meshes:             1
#: Number of Element Sets:       2910
#: Number of Node Sets:          5
#: Number of Steps:              1
#: Model: D:/Master thesis/Adaptive remeshing/models/pandey_kumar_mode1/254_f1804_case2_distal_recovery/PK_HOLE_STATE_POSTBREACH_RECOVERY.odb
#: Number of Assemblies:         1
#: Number of Assembly instances: 0
#: Number of Part instances:     1
#: Number of Meshes:             1
#: Number of Element Sets:       2910
#: Number of Node Sets:          5
#: Number of Steps:              1
#:   Generated physical mesh: D:\Master thesis\Adaptive remeshing\models\pandey_kumar_mode1\258_f1808_four_case_reproducibility\case2\PK_F1808_CASE_2_PHYS.inp
#:   Physical Mesh SHA-256: 8178C4AE61AE4F57DF66D898BB1AE25F8710293F569F9BBD29903AA05A93B29F
#:   Body SHA-256:          35178C924EB5652DD57991AAD34C4CCB436D5C6F6F132E3704B7D9AFF2F1955A
#:   Size:                  1649195 bytes
#:   [AUDIT] Total elements:      22924 (Quads: 22346, Tris: 578, Quad Fraction: 97.48%)
#:   [AUDIT] Min signed det(J):   2.86979e-07 (Nonpositive: 0)
#:   [AUDIT] Aspect Ratio:        max 2.500 (median 1.210, violations > 4.0: 0)
#:   [AUDIT] Corner Angles:       [31.37 deg, 138.48 deg]
#:   [AUDIT] Element Size (area): min 0.000768 mm, mean 0.005069 mm, max 0.025498 mm
#:   [AUDIT] Coarsening Ratio:    2.10x (Far: 0.005222 mm vs Core: 0.002485 mm)
#:   [CRITICAL] Broad distal elements: 6581 (le l0: 100.0%, le l0/2: 89.4%)
#:   [CRITICAL] Combined outer ligament x in [0.90, 1.00]: 878 elements (le l0/2: 28.02%)
#:   Saved case receipt: D:\Master thesis\Adaptive remeshing\models\pandey_kumar_mode1\258_f1808_four_case_reproducibility\case2\PK_F1808_CASE_2_RECEIPT.json
