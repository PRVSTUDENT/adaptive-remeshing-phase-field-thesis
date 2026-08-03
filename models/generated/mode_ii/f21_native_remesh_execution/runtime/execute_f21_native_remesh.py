from __future__ import print_function
import hashlib,json,math,os,sys,traceback
from abaqus import mdb
from abaqusConstants import MODEL,NOT_ALLOWED,OFF,ON,UNIFORM_ERROR
from odbAccess import openOdb

OUT=os.environ['F21_OUTPUT_DIR']; ODB_PATH=os.environ['F21_SOURCE_ODB']; DECK=os.path.join(os.getcwd(),'source_deck.inp')
CANDIDATE=os.path.join(OUT,'M2RMEXEC1_candidate.inp')
COUNTERS={'native_remesh_route_calls':0,'candidate_generations':0,'solver_executions':0,'datacheck_executions':0,'state_transfer_executions':0,'refined_analyses':0,'nested_qsub_calls':0}
def wr(name,data):
 with open(os.path.join(OUT,name),'wb') as h: h.write((json.dumps(data,indent=2,sort_keys=True)+'\n').encode('utf-8'))
def sha(path):
 d=hashlib.sha256(); h=open(path,'rb')
 while True:
  b=h.read(1048576)
  if not b: break
  d.update(b)
 h.close(); return d.hexdigest()
def part_summary(part):
 nodes=[]; elements=[]
 for n in part.nodes: nodes.append((int(n.label),tuple(float(x) for x in n.coordinates)))
 for e in part.elements: elements.append((int(e.label),str(e.type),tuple(int(x) for x in e.connectivity)))
 ch=hashlib.sha256(); kh=hashlib.sha256()
 for label,coords in sorted(nodes): ch.update(('%d:%s\n'%(label,','.join('%.17g'%x for x in coords))).encode('ascii'))
 for label,kind,conn in sorted(elements): kh.update(('%d:%s:%s\n'%(label,kind,','.join(str(x) for x in conn))).encode('ascii'))
 types={}
 for unused,kind,unused2 in elements: types[kind]=types.get(kind,0)+1
 bounds=[]
 if nodes:
  for axis in range(len(nodes[0][1])): bounds.append([min(x[1][axis] for x in nodes),max(x[1][axis] for x in nodes)])
 return {'node_count':len(nodes),'element_count':len(elements),'element_type_counts':types,'coordinate_hash':ch.hexdigest(),'connectivity_hash':kh.hexdigest(),'bounding_box':bounds}
def topology(part,tol):
 nodes=[]
 for n in part.nodes: nodes.append((int(n.label),tuple(float(x) for x in n.coordinates)))
 pairs=[]
 for i in range(len(nodes)):
  for j in range(i+1,len(nodes)):
   if all(abs(nodes[i][1][k]-nodes[j][1][k])<=tol for k in range(len(nodes[i][1]))): pairs.append((nodes[i][0],nodes[j][0],nodes[i][1]))
 bridges=[]
 for e in part.elements:
  c=set(int(x) for x in e.connectivity)
  for a,b,unused in pairs:
   if a in c and b in c: bridges.append(int(e.label))
 return {'coordinate_tolerance':tol,'coincident_pair_count':len(pairs),'bridge_element_ids':sorted(set(bridges)),'opposite_faces_disconnected':not bridges,'slit_endpoint_behavior':'preserved_when_no_bridge_and_faces_disconnected'}

odb=None; classification='native_remesh_evidence_incomplete'; failure=None
try:
 model=mdb.ModelFromInputFile(name='F21_SOURCE',inputFileName=DECK); source_part=model.parts[model.parts.keys()[0]]
 if bool(getattr(source_part,'isMeshPart',False)):
  target=model.Part2DGeomFrom2DMesh(name='F21_GEOMETRY_BACKED',part=source_part,featureAngle=20.0)
 else: target=source_part
 model.RemeshingRule(name='F20_MISESERI_RULE',stepName='Step-1',variables=(str('MISESERI'),),region=MODEL,sizingMethod=UNIFORM_ERROR,errorTarget=1.0,specifyMinSize=ON,minElementSize=0.001,specifyMaxSize=ON,maxElementSize=0.010,coarseningFactor=NOT_ALLOWED,refinementFactor=10)
 source=part_summary(target); source_topology=topology(source_part,1.0e-10)
 odb=openOdb(path=ODB_PATH,readOnly=True); step=odb.steps[odb.steps.keys()[-1]]; values=step.frames[-1].fieldOutputs['MISESERI'].values
 finite=[float(v.data) for v in values if not math.isnan(float(v.data)) and not math.isinf(float(v.data))]
 finite.sort(); n=len(finite)
 source_field={'finite_value_count':n,'minimum':finite[0],'maximum':finite[-1],'mean':sum(finite)/n,'quantiles':{'q50':finite[int(.5*(n-1))],'q90':finite[int(.9*(n-1))],'q95':finite[int(.95*(n-1))]}}
 wr('NATIVE_REMESH_API_SELECTION.json',{'owner':'mdb.models[\"F21_SOURCE\"]','selected_method':'Model.adaptiveRemesh(odb)','signature':'Model.adaptiveRemesh(odb)','rule':'F20_MISESERI_RULE','region':'MODEL','step':'Step-1','fallback_routes':[]})
 COUNTERS['native_remesh_route_calls']=1
 model.adaptiveRemesh(odb)
 candidate_part=model.parts[model.parts.keys()[0]]; candidate=part_summary(candidate_part)
 job=mdb.Job(name='M2RMEXEC1_candidate',model=model.name); job.writeInput(consistencyChecking=OFF); generated=os.path.join(os.getcwd(),'M2RMEXEC1_candidate.inp')
 if not os.path.isfile(generated): raise IOError('candidate export missing')
 os.rename(generated,CANDIDATE); COUNTERS['candidate_generations']=1
 changed=source['connectivity_hash']!=candidate['connectivity_hash'] or source['coordinate_hash']!=candidate['coordinate_hash']
 wr('SOURCE_MESH_SUMMARY.json',source); wr('CANDIDATE_MESH_SUMMARY.json',candidate)
 wr('MESH_CHANGE_AUDIT.json',{'mesh_changed':changed,'nodes_added':max(0,candidate['node_count']-source['node_count']),'nodes_removed':max(0,source['node_count']-candidate['node_count']),'elements_added':max(0,candidate['element_count']-source['element_count']),'elements_removed':max(0,source['element_count']-candidate['element_count']),'changed_connectivity':source['connectivity_hash']!=candidate['connectivity_hash'],'changed_coordinates':source['coordinate_hash']!=candidate['coordinate_hash']})
 candidate_topology=topology(candidate_part,1.0e-10); wr('CANDIDATE_SLIT_TOPOLOGY_AUDIT.json',candidate_topology)
 integrity={'parts':sorted(model.parts.keys()),'instances':sorted(model.rootAssembly.instances.keys()),'materials':sorted(model.materials.keys()),'sections':sorted(model.sections.keys()),'sets':sorted(model.rootAssembly.sets.keys()),'surfaces':sorted(model.rootAssembly.surfaces.keys()),'steps':sorted(model.steps.keys()),'loads':sorted(model.loads.keys()),'boundary_conditions':sorted(model.boundaryConditions.keys()),'structural_review_only':True,'datacheck_claimed':False}
 integrity['pass']=bool(integrity['parts'] and integrity['steps']); wr('CANDIDATE_MODEL_INTEGRITY.json',integrity)
 wr('MISESERI_REFINEMENT_AUDIT.json',{'source_field':source_field,'mesh_changed':changed,'coarsening_allowed':False,'minimum_size':0.001,'maximum_size':0.010,'refinement_factor':10,'mapping':'model.adaptiveRemesh applied qualified MISESERI rule; elementwise map retained only when exposed by Abaqus'})
 wr('CANDIDATE_MANIFEST.json',{'candidate_name':'M2RMEXEC1_candidate.inp','candidate_sha256':sha(CANDIDATE),'candidate_size':os.path.getsize(CANDIDATE),'line_count':sum(1 for x in open(CANDIDATE,'rb')),'source_odb_sha256':'bfcdbec08669774a9f80939d67c9c86ffe7df707e760450b08b1f6073fc588ac','source_deck_sha256':'a927b8317ff9e20bfa84dd669a2577b095e69d1bf1c343b81b158a83fd075ea2','api_route':'Model.adaptiveRemesh(odb)'})
 if not changed: classification='native_remesh_completed_without_mesh_change'
 elif not candidate_topology['opposite_faces_disconnected']: classification='native_remesh_slit_topology_failed'
 elif not integrity['pass']: classification='native_remesh_candidate_integrity_failed'
 else: classification='native_remesh_candidate_generated_pending_datacheck'
except Exception:
 failure=traceback.format_exc(); classification='native_remesh_api_execution_failed' if COUNTERS['native_remesh_route_calls'] else 'native_remesh_source_integrity_failed'
 wr('NATIVE_REMESH_TRACEBACK.txt',failure)
finally:
 if odb is not None: odb.close()
wr('NATIVE_REMESH_EXECUTION_AUDIT.json',dict(COUNTERS,classification=classification,traceback_present=bool(failure)))
wr('NO_DOWNSTREAM_EXECUTION_AUDIT.json',dict(COUNTERS,classification=classification))
wr('STATUS.json',dict(COUNTERS,classification=classification))
for key in ('solver_executions','datacheck_executions','state_transfer_executions','refined_analyses','nested_qsub_calls'): assert COUNTERS[key]==0
sys.exit(0 if classification in ('native_remesh_candidate_generated_pending_datacheck','native_remesh_completed_without_mesh_change') else 1)
