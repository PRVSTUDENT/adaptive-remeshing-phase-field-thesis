# -*- coding: mbcs -*-
#
# Abaqus/CAE Release 2024 replay file
# Internal Version: 2023_09_21-14.55.25 RELr426 190762
# Run by pruth on Mon Nov 16 08:07:06 2026
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
#: DEBUG sys.argv: ['C:\\SIMULIA\\EstProducts\\2024\\win_b64\\code\\bin\\ABQcaeK.exe', '-cae', '-noGUI', 'D:\\Master thesis\\Adaptive remeshing\\scripts\\remeshing\\run_f1809_single_case.py', '-tmpdir', 'C:\\Users\\pruth\\AppData\\Local\\Temp', '-lmlog', 'ON', 'case_1']
#: ================================================================================
#: TASK F1809 SINGLE-CASE ISOLATED EXECUTION: Case 1: Mode-I Edge-Cracked Plate
#: ================================================================================
#:   Case ID:     case_1
#:   Config:      D:\Master thesis\Adaptive remeshing\configs\remeshing\f1809_case1_native_miseseri.json
#:   Donor:       D:\Master thesis\Adaptive remeshing\models\pandey_kumar_mode1\257_f1807_four_case_regression\case1\PK_F1807_CASE1_COARSE_DONOR.odb
#:   Output Dir:  D:\Master thesis\Adaptive remeshing\models\pandey_kumar_mode1\259_f1809_multistate_recovery\case1
#:   Donor SHA-256: DF246BEA9AD9AD5DD650073156322C6C2213B1B3A26C2C66ECE11D1691E9DCF0 (4172008 bytes)
#: The model "Model_MethodA_case_1" has been created.
#: Model: D:/Master thesis/Adaptive remeshing/models/pandey_kumar_mode1/257_f1807_four_case_regression/case1/PK_F1807_CASE1_COARSE_DONOR.odb
#: Number of Assemblies:         1
#: Number of Assembly instances: 0
#: Number of Part instances:     1
#: Number of Meshes:             1
#: Number of Element Sets:       4
#: Number of Node Sets:          5
#: Number of Steps:              1
#: Model: D:/Master thesis/Adaptive remeshing/models/pandey_kumar_mode1/257_f1807_four_case_regression/case1/PK_F1807_CASE1_COARSE_DONOR.odb
#: Number of Assemblies:         1
#: Number of Assembly instances: 0
#: Number of Part instances:     1
#: Number of Meshes:             1
#: Number of Element Sets:       4
#: Number of Node Sets:          5
#: Number of Steps:              1
#:   Generated physical mesh: D:\Master thesis\Adaptive remeshing\models\pandey_kumar_mode1\259_f1809_multistate_recovery\case1\PK_F1809_CASE_1_PHYS.inp
#:   Physical Mesh SHA-256: B18339EA2B4D69932851CAE66483779D258711CB9961D752598D2155A72C57A3
#:   Body SHA-256:          EAA671FBECC8E1AE759BF3EE5A54AC8BE90F354B087483CD8B513A85DF85F277
#:   Size:                  1011306 bytes
#:   [AUDIT] Total elements:      14087 (Quads: 13667, Tris: 420, Quad Fraction: 97.02%)
#:   [AUDIT] Min signed det(J):   2.47887e-07 (Nonpositive: 0)
#:   [AUDIT] Aspect Ratio:        max 2.640 (median 1.221, violations > 4.0: 0)
#:   [AUDIT] Corner Angles:       [31.19 deg, 137.82 deg]
#:   [AUDIT] Element Size (area): min 0.000706 mm, mean 0.007016 mm, max 0.022249 mm
#:   [AUDIT] Coarsening Ratio:    2.54x (Far: 0.007435 mm vs Core: 0.002925 mm)
#:   [CRITICAL] Ligament elements: 918 (100% le l0: 89.3%, le l0/2: 79.8%)
#:   [CRITICAL] Proximal tip elements: 628 (le l0/2: 100.0%)
#:   Saved case receipt: D:\Master thesis\Adaptive remeshing\models\pandey_kumar_mode1\259_f1809_multistate_recovery\case1\PK_F1809_CASE_1_RECEIPT.json
