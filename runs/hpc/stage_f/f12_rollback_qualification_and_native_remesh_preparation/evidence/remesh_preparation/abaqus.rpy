# -*- coding: mbcs -*-
#
# Abaqus/CAE Release 2023 replay file
# Internal Version: 2022_09_28-20.11.55 183150
# Run by pr21vyci on Fri Jul 31 12:11:54 2026
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
execfile('runtime/prepare_stage_f12_native_remesh.py', __main__.__dict__)
#: The model "F12_MISESERI_COARSE" has been created.
#: The part "PART-1" has been imported from the input file.
#: 
#: WARNING: The following keywords/parameters are not yet supported by the input file reader:
#: ---------------------------------------------------------------------------------
#: *PREPRINT
#: The model "F12_MISESERI_COARSE" has been imported from an input file. 
#: Please scroll up to check for error and warning messages.
#: Warning: History output is not requested in the following steps:
#: Step-1
#: The model database has been saved to "/scratch/pr21vyci/adaptive-remeshing/runs/stage_f12/F12_20260731_100123_03e544a/remesh_preparation/output/F12_MISESERI_DISPOSABLE.cae".
#* Exit code: 0
#* File "runtime/prepare_stage_f12_native_remesh.py", line 9, in <module>
#*     execfile(core, namespace, namespace)
#* File 
#* "/scratch/pr21vyci/adaptive-remeshing/runs/stage_f12/F12_20260731_100123_03e544a/remesh_preparation/runtime/prepare_stage_f12_native_remesh_core.py", 
#* line 50, in <module>
#*     sys.exit(0 if status.get("rule_object_created") else 1)
