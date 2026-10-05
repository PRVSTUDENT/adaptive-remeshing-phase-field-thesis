# -*- coding: mbcs -*-
#
# Abaqus/CAE Release 2023 replay file
# Internal Version: 2022_09_28-20.11.55 183150
# Run by pr21vyci on Sat Oct  3 18:05:49 2026
#

# from driverUtils import executeOnCaeGraphicsStartup
# executeOnCaeGraphicsStartup()
#: Executing "onCaeGraphicsStartup()" in the site directory ...
from abaqus import *
from abaqusConstants import *
session.Viewport(name='Viewport: 1', origin=(1.36719, 1.36719), width=201.25, 
    height=135.625)
session.viewports['Viewport: 1'].makeCurrent()
from driverUtils import executeOnCaeStartup
executeOnCaeStartup()
execfile(
    '/home/pr21vyci/projects/adaptive-remeshing/models/pandey_kumar_mode1/95_mode1_stage10_inf_companion_remesh/execute_stage10_inf_companion_native_remesh.py', 
    __main__.__dict__)
#: ======================================================================
#: STAGE 10: NATIVE 1% ADAPTIVE REMESHING OF INF-COMPANION ODB
#: ======================================================================
#: Opening ODB: /home/pr21vyci/projects/adaptive-remeshing/models/pandey_kumar_mode1/90_mode1_preanalysis_continuum_matched_2906/PK_M1_JOB1_CONTINUUM_MATCHED_2906.odb
#: Model: /home/pr21vyci/projects/adaptive-remeshing/models/pandey_kumar_mode1/90_mode1_preanalysis_continuum_matched_2906/PK_M1_JOB1_CONTINUUM_MATCHED_2906.odb
#: Number of Assemblies:         1
#: Number of Assembly instances: 0
#: Number of Part instances:     1
#: Number of Meshes:             1
#: Number of Element Sets:       4
#: Number of Node Sets:          5
#: Number of Steps:              2
#: Step-1 total frames: 501, final frameValue (time/disp): 1.000000
#: ODB Field Check (Package 93 Infinitesimal Companion):
#:   Total elements with MISESERI: 2906
#:   Peak MISESERI: 9.500091e-01
#:   Min MISESERI:  2.540622e-04
#:   Mean MISESERI: 9.877701e-03
#: The model "PK_M1_STAGE10_INF_CAD" has been created.
#: Geometry-backed Part Coarse Mesh generated: 2963 elements, 3039 nodes
#: Created RemeshingRule on ALL_ELEM: errorTarget=1.0%, refFactor=10, h in [0.001, 0.020] mm
#: Calling m.adaptiveRemesh(odb=o)...
#: adaptiveRemesh call completed successfully!
#: Adapted Mesh Generated: 56344 elements, 55943 nodes
#: ======================================================================
#: STAGE 10 SUMMARY:
#:   Adapted Element Count: 56344 (Nodes: 55943)
#:   Corridor Elements: 8131 (14.43%)
#:   Far Field Elements: 48213 (85.57%)
#:   Saved: ./STAGE10_INF_COMPANION_REMESH_SUMMARY.json
#:   Saved: ./stage10_adapted_elements.csv
#:   Saved: ./PK_M1_STAGE10_INF_ADAPTED_RAW_1PCT.inp
#: ======================================================================
print 'RT script done'
#: RT script done
