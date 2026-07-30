# -*- coding: mbcs -*-
#
# Abaqus/CAE Release 2023 replay file
# Internal Version: 2022_09_28-20.11.55 183150
# Run by pr21vyci on Thu Jul 30 14:26:43 2026
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
execfile('runtime/scripts/remeshing/qualify_mode_ii_native_miseseri_api.py', 
    __main__.__dict__)
#: usage: ABQcaeK [-h] --config CONFIG --odb ODB --deck DECK --output-dir
#:                OUTPUT_DIR
#: ABQcaeK: error: unrecognized arguments: -cae -noGUI runtime/scripts/remeshing/qualify_mode_ii_native_miseseri_api.py -lmlog ON -tmpdir /local/pbs.1379967.mmaster02
#* Exit code: 2
#* File "runtime/scripts/remeshing/qualify_mode_ii_native_miseseri_api.py", 
#* line 164, in <module>
#*     sys.exit(main())
#* File "runtime/scripts/remeshing/qualify_mode_ii_native_miseseri_api.py", 
#* line 42, in main
#*     args = parser.parse_args(argv)
#* File 
#* "/cluster/application/abaqus/2023/linux_a64/tools/SMApy/python2.7/lib/python2.7/argparse.py", 
#* line 1704, in parse_args
#*     self.error(msg % ' '.join(argv))
#* File 
#* "/cluster/application/abaqus/2023/linux_a64/tools/SMApy/python2.7/lib/python2.7/argparse.py", 
#* line 2374, in error
#*     self.exit(2, _('%s: error: %s\n') % (self.prog, message))
#* File 
#* "/cluster/application/abaqus/2023/linux_a64/tools/SMApy/python2.7/lib/python2.7/argparse.py", 
#* line 2362, in exit
#*     _sys.exit(status)
