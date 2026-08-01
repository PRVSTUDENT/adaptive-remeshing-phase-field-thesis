# -*- coding: mbcs -*-
#
# Abaqus/CAE Release 2023 replay file
# Internal Version: 2022_09_28-20.11.55 183150
# Run by pr21vyci on Fri Jul 31 13:33:22 2026
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
execfile('runtime/execute_stage_f13_native_remesh.py', __main__.__dict__)
#: The model "F13_MISESERI_COARSE" has been created.
#: The part "PART-1" has been imported from the input file.
#: 
#: WARNING: The following keywords/parameters are not yet supported by the input file reader:
#: ---------------------------------------------------------------------------------
#: *PREPRINT
#: The model "F13_MISESERI_COARSE" has been imported from an input file. 
#: Please scroll up to check for error and warning messages.
#: Model: /scratch/pr21vyci/adaptive-remeshing/runs/stage_f4/F4R1_20260730_065138_86ec6c79/miseseri_corrected/M2MISER1.odb
#: Number of Assemblies:         1
#: Number of Assembly instances: 0
#: Number of Part instances:     1
#: Number of Meshes:             2
#: Number of Element Sets:       4
#: Number of Node Sets:          9
#: Number of Steps:              1
#* Exit code: 1
#* File "runtime/execute_stage_f13_native_remesh.py", line 6, in <module>
#*     exec(compile(open(core, "rb").read(), core, "exec"), namespace, 
#* namespace)
#* File 
#* "/home/pr21vyci/adaptive-remeshing-evidence/stage_f13/F13_20260731_105412_51b31f9/native_remesh/runtime/execute_stage_f13_native_remesh_core.py", 
#* line 55, in <module>
#*     sys.exit(0 if status.get("candidate_generated") else 1)
