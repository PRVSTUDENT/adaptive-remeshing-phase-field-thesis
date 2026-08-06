# -*- coding: mbcs -*-
#
# Abaqus/CAE Release 2023 replay file
# Internal Version: 2022_09_28-20.11.55 183150
# Run by pr21vyci on Thu Aug  6 11:08:42 2026
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
    '/scratch9/pr21vyci/f21_exec_83cbfe0/runs/hpc/stage_f/f40_f38_cae_invocation_model_building_bisect/M2RMBISECT1_1384450.mmaster02/runtime/f40_cae_bisection_runner.py', 
    __main__.__dict__)
#: === F40 Abaqus CAE Bisection Matrix Runner ===
#: PHASE_AUDIT_RECORDED: P00_KERNEL_STARTUP (rc=0)
#: PHASE_AUDIT_RECORDED: P01_IMPORTS (rc=0)
#: PHASE_AUDIT_RECORDED: P02_MODULE_LOADING (rc=0)
#: PHASE_AUDIT_RECORDED: P03_SOURCE_DECK_DISCOVERY (rc=0)
#: The model "F40_MODEL" has been created.
#: The part "PART-1" has been imported from the input file.
#: 
#: WARNING: The following keywords/parameters are not yet supported by the input file reader:
#: ---------------------------------------------------------------------------------
#: *PREPRINT
#: The model "F40_MODEL" has been imported from an input file. 
#: Please scroll up to check for error and warning messages.
#: PHASE_AUDIT_RECORDED: P04_MODEL_FROM_INPUT_FILE (rc=0)
#: PHASE_AUDIT_RECORDED: P05_IMPORTED_MODEL_INVENTORY (rc=0)
#: Warning: Planar shell feature failed
#: PHASE_AUDIT_RECORDED: P06_GEOMETRY_CONVERSION (rc=0)
#: The model "F40_PROBE_OWNERSHIP" has been created.
#: PHASE_AUDIT_RECORDED: P07_INDEPENDENT_MODEL_OWNERSHIP (rc=0)
#: PHASE_AUDIT_RECORDED: P08_ASSEMBLY_OPERATIONS (rc=0)
#: PHASE_AUDIT_RECORDED: P09_TOPOLOGY_MEASUREMENT (rc=0)
#: PHASE_AUDIT_RECORDED: P10_SETS_SURFACES_INVENTORY (rc=0)
#: PHASE_AUDIT_RECORDED: P11_STEP_OUTPUT_PROBING (rc=0)
#: ALL_BISECTION_PHASES_COMPLETED_SUCCESSFULLY
#* Exit code: 0
#* File 
#* "/scratch9/pr21vyci/f21_exec_83cbfe0/runs/hpc/stage_f/f40_f38_cae_invocation_model_building_bisect/M2RMBISECT1_1384450.mmaster02/runtime/f40_cae_bisection_runner.py", 
#* line 272, in <module>
#*     sys.exit(run_bisection_matrix())
