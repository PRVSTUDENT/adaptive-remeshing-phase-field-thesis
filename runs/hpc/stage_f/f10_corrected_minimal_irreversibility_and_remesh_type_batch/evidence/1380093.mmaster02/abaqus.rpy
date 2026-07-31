# -*- coding: mbcs -*-
#
# Abaqus/CAE Release 2023 replay file
# Internal Version: 2022_09_28-20.11.55 183150
# Run by pr21vyci on Fri Jul 31 08:07:56 2026
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
execfile('runtime/qualify_stage_f10_remeshing_variable_type.py', 
    __main__.__dict__)
#* NameError: name '__file__' is not defined
#* File "runtime/qualify_stage_f10_remeshing_variable_type.py", line 6, in 
#* <module>
#*     CORE = os.path.join(os.path.dirname(os.path.abspath(__file__)),
