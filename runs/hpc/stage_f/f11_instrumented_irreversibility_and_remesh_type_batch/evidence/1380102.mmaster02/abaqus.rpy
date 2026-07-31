# -*- coding: mbcs -*-
#
# Abaqus/CAE Release 2023 replay file
# Internal Version: 2022_09_28-20.11.55 183150
# Run by pr21vyci on Fri Jul 31 09:02:43 2026
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
execfile('runtime/qualify_stage_f11_remeshing_variable_type.py', 
    __main__.__dict__)
#: A new model database has been created.
#: The model "Model-1" has been created.
session.viewports['Viewport: 1'].setValues(displayedObject=None)
#: The model "F11_REMESH_TYPE" has been created.
#* Exit code: 0
#* File "runtime/qualify_stage_f11_remeshing_variable_type.py", line 10, in 
#* <module>
#*     execfile(core, globals())
#* File 
#* "/scratch/pr21vyci/adaptive-remeshing/runs/stage_f11/F11_20260731_065515_fec1165/remesh_type/runtime/qualify_stage_f11_remeshing_variable_type_core.py", 
#* line 130, in <module>
#*     sys.exit(RESULT)
