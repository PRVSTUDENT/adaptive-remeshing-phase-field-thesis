"""Plot authentic element SDV1 without interpolation or invented crack paths."""
from pathlib import Path
import json,gzip,zlib,base64,hashlib
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.collections import PolyCollection
from matplotlib.colors import LinearSegmentedColormap,Normalize
ROOT=Path(__file__).resolve().parents[2]
source=ROOT/'results/validation/adaptive_job2_damage_states.json.gz'
data=json.loads(gzip.decompress(source.read_bytes()))
out=ROOT/'results/figures/adaptive_damage_contours';out.mkdir(parents=True,exist_ok=True)
cmap=LinearSegmentedColormap.from_list('phase',['#34479b','#237bb8','#35c9c8','#9be27a','#f4e73a','#f99528','#d7191c'])
norm=Normalize(0,1);manifest=[]
names={1:'Mode-I edge-cracked plate',2:'Off-axis-hole plate (Mode-I)',3:'Notched plate with hole and pins',5:'Seven-hole plate'}
for case in data:
    cid=case['case'];polys=[e['xy'] for e in case['elements']]
    xy=np.concatenate([np.array(x) for x in polys]);lo=xy.min(axis=0);hi=xy.max(axis=0)
    tall=cid==3
    fig,axs=plt.subplots(1,5,figsize=(14,6.5 if tall else 3.8))
    for k,ax in enumerate(axs):
        if k==0:
            coll=PolyCollection(polys,facecolors='#5ed0d0',edgecolors='#316b79',linewidths=.10,rasterized=True)
            ax.set_title('Existing adaptive mesh\n{:,.0f} physical elements'.format(len(polys)),fontsize=10)
        else:
            s=case['states'][k-1];coll=PolyCollection(polys,array=np.array(s['damage']),cmap=cmap,norm=norm,edgecolors='none',rasterized=True)
            ax.set_title('$u_y$ = %.5g mm\n%s, frame %d'%(s['u2_mm'],s['step'],s['frame_index']),fontsize=10)
        ax.add_collection(coll);ax.set_xlim(lo[0],hi[0]);ax.set_ylim(lo[1],hi[1]);ax.set_aspect('equal');ax.set_xticks([]);ax.set_yticks([])
        for sp in ax.spines.values():sp.set_visible(False)
    fig.suptitle('Case %d | %s'%(cid,names[cid]),fontsize=15,y=.98)
    fig.subplots_adjust(left=.025,right=.985,top=.84,bottom=.21,wspace=.06)
    cb=fig.colorbar(plt.cm.ScalarMappable(norm=norm,cmap=cmap),ax=list(axs),orientation='horizontal',fraction=.035,pad=.065,shrink=.5,aspect=50)
    cb.set_label(r'Damage $\phi$ = SDV1 (element integration-point mean)',fontsize=10)
    footer='Recorded states: pre-peak | peak load | post-peak | last available. '
    footer+=('Solver completed (Exit 0).' if cid==1 else 'Solver terminated (Exit 1); contours show available converged frames.')
    fig.text(.5,.025,footer,ha='center',fontsize=9)
    stem=out/('case_%d_damage_evolution'%cid)
    for ext in ('png','pdf'):
        p=stem.with_suffix('.'+ext);fig.savefig(p,dpi=250,facecolor='white');manifest.append({'case':cid,'path':p.relative_to(ROOT).as_posix(),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()})
    plt.close(fig)
    for j,s in enumerate(case['states']):
        fig,ax=plt.subplots(figsize=(5,7 if tall else 5));ax.add_collection(PolyCollection(polys,array=np.array(s['damage']),cmap=cmap,norm=norm,edgecolors='none',rasterized=True));ax.set(xlim=(lo[0],hi[0]),ylim=(lo[1],hi[1]),aspect='equal');ax.set_axis_off();ax.set_title('Case %d | $u_y$=%.6g mm\n%s, index %d, frameId %d'%(cid,s['u2_mm'],s['step'],s['frame_index'],s['frame_id']),fontsize=11);fig.colorbar(plt.cm.ScalarMappable(norm=norm,cmap=cmap),ax=ax,orientation='horizontal',fraction=.04,pad=.04,label=r'$\phi$ (SDV1)');fig.savefig(out/('case_%d_state_%d.png'%(cid,j+1)),dpi=220,bbox_inches='tight');plt.close(fig)
summary={'source':'Existing F1859 adaptive Job-2 ODBs; no solve or remesh','raw_export_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'states':[{k:v for k,v in c.items() if k!='elements' and k!='states'}|{'states':[{k:v for k,v in s.items() if k!='damage'} for s in c['states']]} for c in data],'images':manifest,'display_range':[0,1],'display_note':'Color saturation outside [0,1] only; raw SDV1 preserved. No spatial smoothing. Undeformed coordinates.'}
summary['source_revision']='951ca407a550321d7eb34f8e55879e098ba70a88'
summary['local_inputs']=[{'path':p.relative_to(ROOT).as_posix(),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for cid in (1,2,3,5) for p in [ROOT/('models/pandey_kumar_mode1/286_f1859_four_benchmark_reference_comparison/job2_adaptive_case%d/PK_F1859_J2_C%d.inp'%(cid,cid))]]
(ROOT/'results/validation/adaptive_job2_damage_contours_manifest.json').write_text(json.dumps(summary,indent=2))
print('Created four evolution PNG/PDF panels and 16 individual state PNGs')
