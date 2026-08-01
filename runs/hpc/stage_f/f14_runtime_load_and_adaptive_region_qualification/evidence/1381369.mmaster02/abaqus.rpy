# -*- coding: mbcs -*-
#
# Abaqus/CAE Release 2023 replay file
# Internal Version: 2022_09_28-20.11.55 183150
# Run by pr21vyci on Sat Aug  1 08:17:59 2026
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
execfile('runtime/qualify_stage_f14_adaptive_region_wrapper.py', 
    __main__.__dict__)
#: The model "F14_MISESERI_COARSE" has been created.
#: The part "PART-1" has been imported from the input file.
#: 
#: WARNING: The following keywords/parameters are not yet supported by the input file reader:
#: ---------------------------------------------------------------------------------
#: *PREPRINT
#: The model "F14_MISESERI_COARSE" has been imported from an input file. 
#: Please scroll up to check for error and warning messages.
#: Model: /scratch/pr21vyci/adaptive-remeshing/runs/stage_f4/F4R1_20260730_065138_86ec6c79/miseseri_corrected/M2MISER1.odb
#: Number of Assemblies:         1
#: Number of Assembly instances: 0
#: Number of Part instances:     1
#: Number of Meshes:             2
#: Number of Element Sets:       4
#: Number of Node Sets:          9
#: Number of Steps:              1
#* Exit code: 0
#* File "runtime/qualify_stage_f14_adaptive_region_wrapper.py", line 6, in 
#* <module>
#*     exec(compile(open(core, "rb").read(), core, "exec"), namespace, 
#* namespace)
#* File 
#* "/home/pr21vyci/adaptive-remeshing-evidence/stage_f14/F14_20260801_042129_ca800f5/adaptive_region/runtime/qualify_stage_f14_adaptive_region.py", 
#* line 83, in <module>
#*     ("native_adaptive_region_qualified", 
#* "native_adaptive_region_api_unresolved") else 1)
