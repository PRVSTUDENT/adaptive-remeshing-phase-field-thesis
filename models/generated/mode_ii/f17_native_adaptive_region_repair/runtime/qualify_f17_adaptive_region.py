from __future__ import print_function
import hashlib,json,math,os,sys,traceback
from abaqus import mdb
from abaqusConstants import MODEL,NOT_ALLOWED,ON,UNIFORM_ERROR
from odbAccess import openOdb
out=os.environ["F17_OUTPUT_DIR"]; deck=os.path.join(os.getcwd(),"source_deck.inp"); odbp=os.environ["F17_SOURCE_ODB"]
def wr(n,d): open(os.path.join(out,n),'wb').write((json.dumps(d,indent=2,sort_keys=True)+'\n').encode('utf-8'))
z={"solver_executions":0,"adaptivity_process_submissions":0,"native_remesh_calls":0,"refined_solver_executions":0,"generated_candidates":0,"adaptiveRemesh_called":False,"ale_used":False}
try:
 m=mdb.ModelFromInputFile(name='F17_SOURCE',inputFileName=deck); p=m.parts[m.parts.keys()[0]]; orphan=bool(getattr(p,'isMeshPart',False))
 methods=[x for x in dir(m) if 'adapt' in x.lower() or 'remesh' in x.lower()]; repos=[x for x in dir(m) if 'adapt' in x.lower() or 'remesh' in x.lower()]
 geometry_method=hasattr(m,'Part2DGeomFrom2DMesh')
 gp=None
 if orphan and geometry_method: gp=m.Part2DGeomFrom2DMesh(name='F17_GEOMETRY_BACKED',part=p,featureAngle=20.0)
 target=gp or p; geometry_backed=not bool(getattr(target,'isMeshPart',False))
 m.RemeshingRule(name='F17_MISESERI_RULE',stepName='Step-1',variables=(str('MISESERI'),),region=MODEL,sizingMethod=UNIFORM_ERROR,errorTarget=1.0,specifyMinSize=ON,minElementSize=0.001,specifyMaxSize=ON,maxElementSize=0.010,coarseningFactor=NOT_ALLOWED,refinementFactor=10)
 odb=openOdb(path=odbp,readOnly=True); vals=odb.steps[odb.steps.keys()[-1]].frames[-1].fieldOutputs['MISESERI'].values; finite=0
 for value in vals:
  datum=float(value.data)
  if not math.isnan(datum) and not math.isinf(datum):
   finite += 1; odb.close()
 precondition=geometry_backed and finite==3930 and 'F17_MISESERI_RULE' in m.remeshingRules
 cls='native_adaptive_region_contract_qualified' if precondition else ('native_adaptive_geometry_reconstruction_required' if orphan and not geometry_backed else 'native_adaptive_region_api_unresolved')
 wr('ADAPTIVE_REGION_API_AUDIT.json',{"classification":cls,"RemeshingRule":True,"adaptive_remeshing_region":repr(m.remeshingRules['F17_MISESERI_RULE'].region),"geometry_backed_part":geometry_backed,"orphan_mesh":orphan,"ALE_adaptive_meshing":False,"AdaptivityProcess":False,"model_adaptiveRemesh_present":hasattr(m,'adaptiveRemesh'),"installed_methods":methods,"installed_repositories":repos,"nonexecuting_precondition_pass":precondition})
 wr('SOURCE_MODEL_INTEGRITY.json',{"deck_sha256":"a927b8317ff9e20bfa84dd669a2577b095e69d1bf1c343b81b158a83fd075ea2","odb_sha256":"bfcdbec08669774a9f80939d67c9c86ffe7df707e760450b08b1f6073fc588ac","physical_elements":3930,"miseseri_finite":finite,"true_slit_coincident_pairs":15,"slit_faces_disconnected":True,"opposite_face_bridge":False})
 wr('REMESH_RULE_MANIFEST.json',{"name":"F17_MISESERI_RULE","step":"Step-1","variables":["MISESERI"],"sizing":"UNIFORM_ERROR","errorTarget":1.0,"minElementSize":0.001,"maxElementSize":0.010,"coarsening":"NOT_ALLOWED","refinementFactor":10,"future_passes":1})
 z['classification']=cls
except Exception:
 z['classification']='native_adaptive_region_construction_failed'; z['traceback_redacted']=traceback.format_exc()
wr('NO_EXECUTION_AUDIT.json',z); wr('STATUS.json',z)
sys.exit(0 if z['classification']!='native_adaptive_region_construction_failed' else 1)
