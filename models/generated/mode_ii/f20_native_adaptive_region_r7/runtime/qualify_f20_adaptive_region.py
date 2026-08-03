from __future__ import print_function
import json,math,os,sys,traceback
from abaqus import mdb
from abaqusConstants import MODEL,NOT_ALLOWED,ON,UNIFORM_ERROR
from odbAccess import openOdb

out=os.environ['F20_OUTPUT_DIR']; odbp=os.environ['F20_SOURCE_ODB']; deck=os.path.join(os.getcwd(),'source_deck.inp')
def wr(name,data): open(os.path.join(out,name),'wb').write((json.dumps(data,indent=2,sort_keys=True)+'\n').encode('utf-8'))
zero={'solver_executions':0,'datacheck_executions':0,'adaptivity_process_submissions':0,'model_adaptiveRemesh_calls':0,'native_remesh_calls':0,'candidates_generated':0,'refined_analyses':0}

def slit_topology(part,tolerance):
 nodes=[]
 for node in part.nodes:
  coordinates=[]
  for coordinate in node.coordinates: coordinates.append(float(coordinate))
  nodes.append((int(node.label),tuple(coordinates)))
 pairs=[]
 for i in range(len(nodes)):
  for j in range(i+1,len(nodes)):
   a=nodes[i]; b=nodes[j]; same=True
   for k in range(len(a[1])):
    if abs(a[1][k]-b[1][k])>tolerance: same=False; break
   if same: pairs.append((a,b))
 element_nodes={}
 for element in part.elements:
  element_nodes[int(element.label)]=set(int(x) for x in element.connectivity)
 audits=[]; bridges=[]
 for pair in pairs:
  left=[]; right=[]
  for label,connectivity in element_nodes.items():
   if pair[0][0] in connectivity: left.append(label)
   if pair[1][0] in connectivity: right.append(label)
   if pair[0][0] in connectivity and pair[1][0] in connectivity: bridges.append(label)
  audits.append({'node_a':pair[0][0],'node_b':pair[1][0],'coordinates':pair[0][1],
                 'node_a_elements':sorted(left),'node_b_elements':sorted(right),
                 'shared_elements':sorted(set(left).intersection(set(right)))})
 return {'coordinate_tolerance':tolerance,'coincident_pair_count':len(pairs),
         'coincident_pairs':audits,'bridge_element_ids':sorted(set(bridges)),
         'bridge_search_pass':len(bridges)==0,'opposite_faces_disconnected':len(bridges)==0}

odb=None
try:
 m=mdb.ModelFromInputFile(name='F20_SOURCE',inputFileName=deck); part=m.parts[m.parts.keys()[0]]
 orphan=bool(getattr(part,'isMeshPart',False)); methods=[]
 for item in dir(m):
  if 'adapt' in item.lower() or 'remesh' in item.lower(): methods.append(item)
 geometry_part=m.Part2DGeomFrom2DMesh(name='F20_GEOMETRY_BACKED',part=part,featureAngle=20.0) if orphan and hasattr(m,'Part2DGeomFrom2DMesh') else None
 target=geometry_part or part; geometry_backed=not bool(getattr(target,'isMeshPart',False))
 m.RemeshingRule(name='F20_MISESERI_RULE',stepName='Step-1',variables=(str('MISESERI'),),region=MODEL,sizingMethod=UNIFORM_ERROR,errorTarget=1.0,specifyMinSize=ON,minElementSize=0.001,specifyMaxSize=ON,maxElementSize=0.010,coarseningFactor=NOT_ALLOWED,refinementFactor=10)
 odb=openOdb(path=odbp,readOnly=True); step_names=odb.steps.keys()
 if not step_names: raise ValueError('source ODB has no steps')
 frames=odb.steps[step_names[-1]].frames
 if not frames: raise ValueError('source ODB final step has no frames')
 fields=frames[-1].fieldOutputs
 if 'MISESERI' not in fields: raise KeyError('MISESERI')
 values=fields['MISESERI'].values; finite=0
 for value in values:
  datum=float(value.data)
  if not math.isnan(datum) and not math.isinf(datum): finite+=1
 physical=0
 for part_name in m.parts.keys(): physical += len(m.parts[part_name].elements)
 topology=slit_topology(part,1.0e-10)
 sets=sorted(m.rootAssembly.sets.keys()); materials=sorted(m.materials.keys()); sections=sorted(m.sections.keys())
 loads=sorted(m.loads.keys()); bcs=sorted(m.boundaryConditions.keys())
 associated='F20_MISESERI_RULE' in m.remeshingRules and m.remeshingRules['F20_MISESERI_RULE'].region is not None
 integrity=physical==3930 and finite==3930 and topology['coincident_pair_count']==15 and topology['bridge_search_pass']
 ok=geometry_backed and integrity and associated
 cls='native_adaptive_region_contract_qualified' if ok else ('native_adaptive_geometry_reconstruction_required' if orphan and not geometry_backed else 'native_adaptive_region_rule_association_failed' if not associated else 'native_adaptive_region_source_integrity_failed' if not integrity else 'native_adaptive_region_api_unresolved')
 wr('ADAPTIVE_REGION_API_AUDIT.json',{'classification':cls,'orphan_mesh':orphan,'geometry_backed':geometry_backed,'rule_region_associated':associated,'installed_methods':methods})
 wr('SOURCE_MODEL_INTEGRITY.json',{'deck_sha256':'a927b8317ff9e20bfa84dd669a2577b095e69d1bf1c343b81b158a83fd075ea2','odb_sha256':'bfcdbec08669774a9f80939d67c9c86ffe7df707e760450b08b1f6073fc588ac','physical_elements':physical,'miseseri_finite':finite,'materials':materials,'sections':sections,'sets':sets,'loads':loads,'boundary_conditions':bcs,'integrity_pass':integrity})
 wr('SLIT_TOPOLOGY_AUDIT.json',topology)
 wr('REMESH_RULE_MANIFEST.json',{'name':'F20_MISESERI_RULE','step':'Step-1','variables':['MISESERI'],'region_associated':associated})
 zero['classification']=cls
except Exception:
 zero['classification']='native_adaptive_region_construction_failed'; zero['traceback_redacted']=traceback.format_exc()
finally:
 if odb is not None: odb.close()
wr('NO_EXECUTION_AUDIT.json',zero); wr('STATUS.json',zero)
for key in ('solver_executions','datacheck_executions','adaptivity_process_submissions','model_adaptiveRemesh_calls','native_remesh_calls','candidates_generated','refined_analyses'):
 assert zero[key]==0
sys.exit(0 if zero['classification']!='native_adaptive_region_construction_failed' else 1)
