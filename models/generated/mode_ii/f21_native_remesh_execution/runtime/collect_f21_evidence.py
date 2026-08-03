from __future__ import print_function
import argparse,hashlib,json,os,shutil
def sha(p):
 d=hashlib.sha256(); h=open(p,'rb')
 while True:
  b=h.read(1048576)
  if not b: break
  d.update(b)
 h.close(); return d.hexdigest()
def main():
 p=argparse.ArgumentParser(); p.add_argument('--work-dir',required=True); p.add_argument('--final-dir',required=True); p.add_argument('--cae-rc',type=int,required=True); a=p.parse_args()
 inventory=[]
 for name in sorted(os.listdir(a.work_dir)):
  src=os.path.join(a.work_dir,name)
  if os.path.isfile(src): shutil.copy2(src,os.path.join(a.final_dir,name)); inventory.append({'path':name,'size':os.path.getsize(src),'sha256':sha(src)})
 open(os.path.join(a.final_dir,'WORK_EVIDENCE_INVENTORY.json'),'wb').write((json.dumps(inventory,indent=2,sort_keys=True)+'\n').encode('utf-8'))
 required=['ABAQUS_PYTHON_COMPATIBILITY.json','NATIVE_REMESH_API_SELECTION.json','NATIVE_REMESH_EXECUTION_AUDIT.json','NO_DOWNSTREAM_EXECUTION_AUDIT.json','STATUS.json']
 missing=[x for x in required if not os.path.isfile(os.path.join(a.final_dir,x))]
 open(os.path.join(a.final_dir,'MISSING_EVIDENCE_REPORT.json'),'wb').write((json.dumps(missing,indent=2)+'\n').encode('utf-8'))
 names=sorted(x for x in os.listdir(a.final_dir) if os.path.isfile(os.path.join(a.final_dir,x)) and x!='EVIDENCE_MANIFEST.sha256')
 open(os.path.join(a.final_dir,'EVIDENCE_MANIFEST.sha256'),'wb').write((''.join('%s  %s\n'%(sha(os.path.join(a.final_dir,x)),x) for x in names)).encode('ascii'))
 return 1 if missing else 0
if __name__=='__main__': raise SystemExit(main())
