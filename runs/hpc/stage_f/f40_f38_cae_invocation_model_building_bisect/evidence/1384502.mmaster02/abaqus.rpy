# -*- coding: mbcs -*-
#
# Abaqus/CAE Release 2023 replay file
# Internal Version: 2022_09_28-20.11.55 183150
# Run by pr21vyci on Thu Aug  6 13:17:24 2026
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
    '/home/pr21vyci/projects/adaptive-remeshing/runs/hpc/stage_f/f40_f38_cae_invocation_model_building_bisect/M2RMBISECT1_1384502.mmaster02/runtime/run_f38_cae_diagnostic.py', 
    __main__.__dict__)
#: The model "F38_IMPORT_PROBE" has been created.
#: The part "PART-1" has been imported from the input file.
#: 
#: WARNING: The following keywords/parameters are not yet supported by the input file reader:
#: ---------------------------------------------------------------------------------
#: *PREPRINT
#: The model "F38_IMPORT_PROBE" has been imported from an input file. 
#: Please scroll up to check for error and warning messages.
#: The model "F38_GEOMETRY_PROBE" has been created.
#: The part "PART-1" has been imported from the input file.
#: 
#: WARNING: The following keywords/parameters are not yet supported by the input file reader:
#: ---------------------------------------------------------------------------------
#: *PREPRINT
#: The model "F38_GEOMETRY_PROBE" has been imported from an input file. 
#: Please scroll up to check for error and warning messages.
#: Warning: Planar shell feature failed
#: The model "F38_MESH_PROBE" has been created.
#: The part "PART-1" has been imported from the input file.
#: 
#: WARNING: The following keywords/parameters are not yet supported by the input file reader:
#: ---------------------------------------------------------------------------------
#: *PREPRINT
#: The model "F38_MESH_PROBE" has been imported from an input file. 
#: Please scroll up to check for error and warning messages.
#: Warning: Planar shell feature failed
#: The model "F38_INSTANCE_PROBE" has been created.
#: The part "PART-1" has been imported from the input file.
#: 
#: WARNING: The following keywords/parameters are not yet supported by the input file reader:
#: ---------------------------------------------------------------------------------
#: *PREPRINT
#: The model "F38_INSTANCE_PROBE" has been imported from an input file. 
#: Please scroll up to check for error and warning messages.
#: Warning: Planar shell feature failed
#: The model "F38_CRACK_PROBE" has been created.
#: The part "PART-1" has been imported from the input file.
#: 
#: WARNING: The following keywords/parameters are not yet supported by the input file reader:
#: ---------------------------------------------------------------------------------
#: *PREPRINT
#: The model "F38_CRACK_PROBE" has been imported from an input file. 
#: Please scroll up to check for error and warning messages.
#: Warning: Planar shell feature failed
#: The model "F38_OUTPUT_PROBE" has been created.
#: The part "PART-1" has been imported from the input file.
#: 
#: WARNING: The following keywords/parameters are not yet supported by the input file reader:
#: ---------------------------------------------------------------------------------
#: *PREPRINT
#: The model "F38_OUTPUT_PROBE" has been imported from an input file. 
#: Please scroll up to check for error and warning messages.
#: The model "F38_WRITE_INPUT_PROBE" has been created.
#: The part "PART-1" has been imported from the input file.
#: 
#: WARNING: The following keywords/parameters are not yet supported by the input file reader:
#: ---------------------------------------------------------------------------------
#: *PREPRINT
#: The model "F38_WRITE_INPUT_PROBE" has been imported from an input file. 
#: Please scroll up to check for error and warning messages.
#: Warning: History output is not requested in the following steps:
#: Step-1
#: F38 CAE Diagnostic Matrix execution complete. Overall passed: False
print 'RT script done'
#: RT script done
