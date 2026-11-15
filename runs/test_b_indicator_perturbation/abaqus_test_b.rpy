# -*- coding: mbcs -*-
#
# Abaqus/CAE Release 2024 replay file
# Internal Version: 2023_09_21-14.55.25 RELr426 190762
# Run by pruth on Sun Nov 15 19:04:07 2026
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
execfile('scripts/remeshing/run_f1783_generality_tests.py', __main__.__dict__)
#: ================================================================================
#: TASK F1783 REPRODUCIBLE GENERALITY RUNNER (ABAQUS CAE noGUI)
#: ================================================================================
#: 
#: ================================================================================
#: TEST A: GEOMETRY PERTURBATION (CASE 3 NOTCHED PLATE)
#: ================================================================================
#: Loaded Perturbed Config: D:\Master thesis\Adaptive remeshing\configs\remeshing\f1783_test_a_perturbed_case3.json
#: Plate: 70.0 x 130.0 mm, Notch: a=15.0, w=0.40
#: Holes: [(42.0, 60.0, 12.0), (25.0, 25.0, 6.0), (25.0, 105.0, 6.0)]
#: The model "Model_TestA_Perturbed" has been created.
#: Area of face = 8409.4159868246
#: Analytical Face Area: 8409.415987 mm^2
#: Abaqus CAE Face Area:  8409.415987 mm^2
#: Delta Area:           0.000000 mm^2
#: Physical Mesh Elements: 9360 (95.37% Quads, min det(J)=3.024e-06, max AR=3.238)
#: 
#: ================================================================================
#: TEST B: INDICATOR PERTURBATION (RESPONSIVE ADAPTIVE REFINEMENT)
#: ================================================================================
#: Model: D:/Master thesis/Adaptive remeshing/runs/test_b_indicator_perturbation/DONOR_HORIZ.odb
#: Number of Assemblies:         1
#: Number of Assembly instances: 0
#: Number of Part instances:     1
#: Number of Meshes:             1
#: Number of Element Sets:       7
#: Number of Node Sets:          4
#: Number of Steps:              1
#: Model: D:/Master thesis/Adaptive remeshing/runs/test_b_indicator_perturbation/DONOR_DIAG.odb
#: Number of Assemblies:         1
#: Number of Assembly instances: 0
#: Number of Part instances:     1
#: Number of Meshes:             1
#: Number of Element Sets:       7
#: Number of Node Sets:          4
#: Number of Steps:              1
#: Created Donor 1 (Horizontal Indicator) and Donor 2 (Diagonal Indicator).
#: Executing Adaptive Remesh for Donor 1 (Horizontal)...
#: The model "Model_Horiz" has been created.
#: Model: D:/Master thesis/Adaptive remeshing/runs/test_b_indicator_perturbation/DONOR_HORIZ.odb
#: Number of Assemblies:         1
#: Number of Assembly instances: 0
#: Number of Part instances:     1
#: Number of Meshes:             1
#: Number of Element Sets:       7
#: Number of Node Sets:          4
#: Number of Steps:              1
#: Model: D:/Master thesis/Adaptive remeshing/runs/test_b_indicator_perturbation/DONOR_HORIZ.odb
#: Number of Assemblies:         1
#: Number of Assembly instances: 0
#: Number of Part instances:     1
#: Number of Meshes:             1
#: Number of Element Sets:       7
#: Number of Node Sets:          4
#: Number of Steps:              1
#: Executing Adaptive Remesh for Donor 2 (Diagonal)...
#: The model "Model_Diag" has been created.
#: Model: D:/Master thesis/Adaptive remeshing/runs/test_b_indicator_perturbation/DONOR_DIAG.odb
#: Number of Assemblies:         1
#: Number of Assembly instances: 0
#: Number of Part instances:     1
#: Number of Meshes:             1
#: Number of Element Sets:       7
#: Number of Node Sets:          4
#: Number of Steps:              1
#: Model: D:/Master thesis/Adaptive remeshing/runs/test_b_indicator_perturbation/DONOR_DIAG.odb
#: Number of Assemblies:         1
#: Number of Assembly instances: 0
#: Number of Part instances:     1
#: Number of Meshes:             1
#: Number of Element Sets:       7
#: Number of Node Sets:          4
#: Number of Steps:              1
#: 
#: Mesh 1 (Horizontal Donor): Total=4087, Horiz Win=67 (mean h=15.25 um), Diag Win=90 (mean h=15.90 um), Ratio=1.043
#: Mesh 2 (Diagonal Donor):   Total=5736, Horiz Win=59 (mean h=15.89 um), Diag Win=474 (mean h=6.18 um), Ratio=0.389
#: Ratio Inversion Factor: 2.68x
#: 
#: ================================================================================
#: GENERALITY TESTS COMPLETED. Summary published to:
#:   D:\Master thesis\Adaptive remeshing\results\validation\f1783_generality_evidence.json
#: Test A Status: PASS
#: Test B Status: PASS
#: Overall Status: PASS
#: ================================================================================
print('RT script done')
#: RT script done
