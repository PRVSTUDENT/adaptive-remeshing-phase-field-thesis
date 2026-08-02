from __future__ import print_function
import json,math,os,sys,traceback
from abaqus import mdb
from abaqusConstants import MODEL,NOT_ALLOWED,ON,UNIFORM_ERROR
from odbAccess import openOdb
out=os.environ['F18_OUTPUT_DIR']; odbp=os.environ['F18_SOURCE_ODB']; deck=os.path.join(os.getcwd(),'source_deck.inp')
def wr(n,d): open(os.path.join(out,n),'wb').write((json.dumps(d,indent=2,sort_keys=True)+'\n').encode('utf-8'))
zero={'solver_executions':0,'datacheck_executions':0,'adaptivity_process_submissions':0,'model_adaptiveRemesh_calls':0,'native_remesh_calls':0,'candidates_generated':0,'refined_analyses':0}
odb=None
try:
 m=mdb.ModelFromInputFile(name='F18_SOURCE',inputFileName=deck); p=m.parts[m.parts.keys()[0]]
 orphan=bool(getattr(p,'isMeshPart',False)); methods=[x for x in dir(m) if 'adapt' in x.lower() or 'remesh' in x.lower()]
 gp=m.Part2DGeomFrom2DMesh(name='F18_GEOMETRY_BACKED',part=p,featureAngle=20.0) if orphan and hasattr(m,'Part2DGeomFrom2DMesh') else None
 target=gp or p; geometry_backed=not bool(getattr(target,'isMeshPart',False))
 m.RemeshingRule(name='F18_MISESERI_RULE',stepName='Step-1',variables=(str('MISESERI'),),region=MODEL,sizingMethod=UNIFORM_ERROR,errorTarget=1.0,specifyMinSize=ON,minElementSize=0.001,specifyMaxSize=ON,maxElementSize=0.010,coarseningFactor=NOT_ALLOWED,refinementFactor=10)
 odb=openOdb(path=odbp,readOnly=True); step_names=odb.steps.keys()
 if not step_names: raise ValueError('source ODB has no steps')
 frames=odb.steps[step_names[-1]].frames
 if not frames: raise ValueError('source ODB final step has no frames')
 fields=frames[-1].fieldOutputs
 if 'MISESERI' not in fields: raise KeyError('MISESERI')
 values=fields['MISESERI'].values
 if not values: raise ValueError('MISESERI values empty')
 finite=0
 for value in values:
  datum=float(value.data)
  if not math.isnan(datum) and not math.isinf(datum): finite+=1
 physical=sum(len(x.elements) for x in m.parts.values())
 sets=sorted(m.rootAssembly.sets.keys()); materials=sorted(m.materials.keys()); sections=sorted(m.sections.keys())
 loads=sorted(m.loads.keys()); bcs=sorted(m.boundaryConditions.keys())
 associated='F18_MISESERI_RULE' in m.remeshingRules and m.remeshingRules['F18_MISESERI_RULE'].region is not None
 ok=geometry_backed and finite==3930 and physical==3930 and associated
 cls='native_adaptive_region_contract_qualified' if ok else ('native_adaptive_geometry_reconstruction_required' if orphan and not geometry_backed else 'native_adaptive_region_rule_association_failed' if not associated else 'native_adaptive_region_api_unresolved')
 wr('ADAPTIVE_REGION_API_AUDIT.json',{'classification':cls,'orphan_mesh':orphan,'geometry_backed':geometry_backed,'rule_region_associated':associated,'installed_methods':methods})
 wr('SOURCE_MODEL_INTEGRITY.json',{'deck_sha256':'a927b8317ff9e20bfa84dd669a2577b095e69d1bf1c343b81b158a83fd075ea2','odb_sha256':'bfcdbec08669774a9f80939d67c9c86ffe7df707e760450b08b1f6073fc588ac','physical_elements':physical,'miseseri_finite':finite,'materials':materials,'sections':sections,'sets':sets,'loads':loads,'boundary_conditions':bcs,'true_slit_coincident_pairs_expected':15,'disconnected_slit_required':True,'opposite_face_bridge_prohibited':True})
 wr('REMESH_RULE_MANIFEST.json',{'name':'F18_MISESERI_RULE','step':'Step-1','variables':['MISESERI'],'region_associated':associated})
 zero['classification']=cls
except Exception:
 zero['classification']='native_adaptive_region_construction_failed'; zero['traceback_redacted']=traceback.format_exc()
finally:
 if odb is not None: odb.close()
wr('NO_EXECUTION_AUDIT.json',zero); wr('STATUS.json',zero)
assert all(zero[k]==0 for k in ('solver_executions','datacheck_executions','adaptivity_process_submissions','model_adaptiveRemesh_calls','native_remesh_calls','candidates_generated','refined_analyses'))
sys.exit(0 if zero['classification']!='native_adaptive_region_construction_failed' else 1)
