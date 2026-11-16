# -*- coding: mbcs -*-
#
# Abaqus/CAE Release 2024 replay file
# Internal Version: 2023_09_21-14.55.25 RELr426 190762
# Run by pruth on Mon Nov 16 06:43:27 2026
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
#: DEBUG sys.argv: ['C:\\SIMULIA\\EstProducts\\2024\\win_b64\\code\\bin\\ABQcaeK.exe', '-cae', '-noGUI', 'D:\\Master thesis\\Adaptive remeshing\\scripts\\remeshing\\run_f1808_single_case.py', '-tmpdir', 'C:\\Users\\pruth\\AppData\\Local\\Temp', '-lmlog', 'ON', 'case_5']
#: ================================================================================
#: TASK F1808 SINGLE-CASE ISOLATED EXECUTION: Case 5: Plate with Seven Holes (Table 6 Parity)
#: ================================================================================
#:   Case ID:     case_5
#:   Config:      D:\Master thesis\Adaptive remeshing\configs\remeshing\f1808_case5_native_miseseri.json
#:   Donor:       D:\Master thesis\Adaptive remeshing\models\pandey_kumar_mode1\218_f1726_seven_hole_study\PK_F1726_SEVEN_HOLE_COARSE.odb
#:   Output Dir:  D:\Master thesis\Adaptive remeshing\models\pandey_kumar_mode1\258_f1808_four_case_reproducibility\case5
#:   Donor SHA-256: CB673713FDE31593AE452A21BC05BFFC140BCCCE71F1D43D601EE17B43802B0E (194344892 bytes)
#: The model "Model_MethodA_case_5" has been created.
#: Model: D:/Master thesis/Adaptive remeshing/models/pandey_kumar_mode1/218_f1726_seven_hole_study/PK_F1726_SEVEN_HOLE_COARSE.odb
#: Number of Assemblies:         1
#: Number of Assembly instances: 0
#: Number of Part instances:     1
#: Number of Meshes:             1
#: Number of Element Sets:       11
#: Number of Node Sets:          6
#: Number of Steps:              2
#: Model: D:/Master thesis/Adaptive remeshing/models/pandey_kumar_mode1/218_f1726_seven_hole_study/PK_F1726_SEVEN_HOLE_COARSE.odb
#: Number of Assemblies:         1
#: Number of Assembly instances: 0
#: Number of Part instances:     1
#: Number of Meshes:             1
#: Number of Element Sets:       11
#: Number of Node Sets:          6
#: Number of Steps:              2
#:   Generated physical mesh: D:\Master thesis\Adaptive remeshing\models\pandey_kumar_mode1\258_f1808_four_case_reproducibility\case5\PK_F1808_CASE_5_PHYS.inp
#:   Physical Mesh SHA-256: 1827723DDF7B952FF9CE218C8EDD9E09F244532180A18D7FF5478E432EC73432
#:   Body SHA-256:          78009AAEE4FE732C0FA56F2DE5487C1717E82E245B4CAF32C3B9CE19AB2B4065
#:   Size:                  1127961 bytes
#:   [AUDIT] Total elements:      15466 (Quads: 15141, Tris: 325, Quad Fraction: 97.90%)
#:   [AUDIT] Min signed det(J):   3.92157e-07 (Nonpositive: 0)
#:   [AUDIT] Aspect Ratio:        max 2.374 (median 1.205, violations > 4.0: 0)
#:   [AUDIT] Corner Angles:       [29.82 deg, 139.67 deg]
#:   [AUDIT] Element Size (area): min 0.000979 mm, mean 0.006097 mm, max 0.024971 mm
#:   [AUDIT] Coarsening Ratio:    2.12x (Far: 0.007120 mm vs Core: 0.003363 mm)
#:   [CRITICAL] Upper inter-hole corridor elements: 5295 (le l0: 99.0%)
#:   [CRITICAL] Lower inter-hole corridor elements: 2735 (le l0: 94.3%)
#:   Saved case receipt: D:\Master thesis\Adaptive remeshing\models\pandey_kumar_mode1\258_f1808_four_case_reproducibility\case5\PK_F1808_CASE_5_RECEIPT.json
