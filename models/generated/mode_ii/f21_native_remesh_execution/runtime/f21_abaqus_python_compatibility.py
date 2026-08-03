from __future__ import print_function
import json,os,sys,traceback
path=os.path.join(os.environ['F21_OUTPUT_DIR'],'ABAQUS_PYTHON_COMPATIBILITY.json')
try:
 payload={'compatible':sys.version_info[0]==2,'python_version':sys.version,'return_code':0 if sys.version_info[0]==2 else 1}
except Exception: payload={'compatible':False,'return_code':2,'traceback':traceback.format_exc()}
open(path,'wb').write((json.dumps(payload,indent=2,sort_keys=True)+'\n').encode('utf-8'))
sys.exit(payload['return_code'])
