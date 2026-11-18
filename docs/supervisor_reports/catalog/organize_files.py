"""Organise only loose supervisor-report files; keep dated packages intact."""
from pathlib import Path
import csv,hashlib,json,os,re,subprocess
from urllib.parse import unquote

BASE=Path(__file__).resolve().parents[1]
ROOT=BASE.parents[1]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()

def destination(p):
    n=p.name;low=n.lower();ext=p.suffix.lower()
    if '.bak' in low:return 'archive/backups/'+n
    if n=='MANIFEST.sha256':return 'archive/manifests/MANIFEST_before_organisation.sha256'
    if ext=='.zip':return 'archive/packages/'+n
    if ext in ('.aux','.log'):return 'archive/latex_build/'+n
    if ext in ('.png','.pdf') and low.startswith(('fig','gate6_')):
        return 'figures/'+('gate_6/' if 'gate6' in low else 'mode1/')+n
    if ext in ('.json','.csv'):return 'data/'+('gate_6/' if 'gate6' in low else 'mode1/')+n
    if 'abaquser' in low:return 'correspondence/abaquser/'+n
    if any(x in low for x in ('author_inquiry','author_query','reproducibility_inquiry')):return 'correspondence/author_inquiries/'+n
    if low.startswith(('supervisor_progress','supervisor_submission','supervisor_review','final_project_status','final_supervisor_revision')):
        d=re.search(r'20\d\d-\d\d-\d\d',n)
        return 'progress_updates/'+(d.group(0)+'/' if d else '')+n
    if low.startswith(('gate0','gate1')):return 'reports/gates_0_1/'+n
    if low.startswith(('gate5','stage_gate5')):return 'reports/gate_5/'+n
    if 'gate6' in low:return 'reports/gate_6/'+n
    if low.startswith(('mode1_','condensed_mode1','supervisor_executive','supervisor_handoff')):return 'reports/mode1/'+n
    return 'planning_and_decisions/'+n

def main():
    loose=sorted(p for p in BASE.iterdir() if p.is_file())
    assert loose and not (BASE/'FILE_INDEX.csv').exists(),'Already organised; no blind replay'
    before={p.resolve():{'sha256':sha(p),'bytes':p.stat().st_size} for p in BASE.rglob('*') if p.is_file()}
    moves={p.resolve():(BASE/destination(p)).resolve() for p in loose}
    for old,new in moves.items():
        assert old.is_relative_to(BASE) and new.is_relative_to(BASE)
        assert not new.exists(),'Destination collision: '+str(new)
    existing_dirs=sorted(p.name for p in BASE.iterdir() if p.is_dir() and p.name!='catalog')
    # Validate every resolved path before performing any move; never overwrite.
    for old,new in moves.items():
        new.parent.mkdir(parents=True,exist_ok=True)
        old.rename(new)
        assert sha(new)==before[old]['sha256']
    updated=[]
    for old,meta in before.items():
        new=moves.get(old,old)
        if new.suffix.lower() not in ('.md','.tex') or 'archive' in new.relative_to(BASE).parts:continue
        raw=new.read_bytes()
        try:text=raw.decode('utf-8-sig' if raw.startswith(b'\xef\xbb\xbf') else 'utf-8')
        except UnicodeDecodeError:continue
        original=text
        def relocate(target):
            clean=target.strip();angled=clean.startswith('<') and clean.endswith('>');clean=clean[1:-1] if angled else clean
            if re.match(r'^[A-Za-z][A-Za-z0-9+.-]*:',clean) or clean.startswith(('#','/')):return target
            path,sep,frag=clean.partition('#');candidate=(old.parent/unquote(path)).resolve()
            if candidate not in before and not candidate.exists():return target
            resolved=moves.get(candidate,candidate)
            rel=os.path.relpath(resolved,new.parent).replace('\\','/')+(sep+frag if sep else '')
            return '<'+rel+'>' if angled else rel
        text=re.sub(r'(\]\()([^\n]*?)(\))',lambda m:m[1]+relocate(m[2])+m[3],text)
        if new.suffix.lower()=='.tex':
            text=re.sub(r'(\\(?:includegraphics|input|include)(?:\[[^\]]*\])?\{)([^}]+)(\})',lambda m:m[1]+relocate(m[2])+m[3],text)
        for src,dst in moves.items():
            a=src.relative_to(ROOT).as_posix();b=dst.relative_to(ROOT).as_posix()
            text=text.replace(a,b).replace(a.replace('/','\\'),b.replace('/','\\'))
        if text!=original:
            encoding='utf-8-sig' if raw.startswith(b'\xef\xbb\xbf') else 'utf-8'
            new.write_bytes(text.encode(encoding));updated.append(new.relative_to(BASE).as_posix())
    rows=[]
    for old,new in sorted(moves.items()):
        rows.append({'old_path':old.relative_to(BASE).as_posix(),'new_path':new.relative_to(BASE).as_posix(),'original_sha256':before[old]['sha256'],'current_sha256':sha(new),'content_change':'link paths only' if sha(new)!=before[old]['sha256'] else 'none'})
    index=BASE/'FILE_INDEX.csv'
    with index.open('w',encoding='utf-8',newline='') as f:w=csv.DictWriter(f,fieldnames=rows[0].keys());w.writeheader();w.writerows(rows)
    outside=['scripts/evaluation/REFERENCE_EXTRACTION_RULES.json','scripts/visualization/generate_corrected_supervisor_figures.py','scripts/postprocessing/generate_gate6_resolution_and_divergence_figures.py','scripts/postprocessing/plot_strict_diagnostic_twin_1404933.py']
    audit={'moved_files':len(rows),'updated_link_files':updated,'existing_dated_packages_preserved':existing_dirs,'deleted_files':0,'scope':'docs/supervisor_reports only; user explicitly allowed parallel folder work while AGY owns F1859','external_legacy_references_left_untouched':outside,'historical_manifest':'archive/manifests/MANIFEST_before_organisation.sha256','immutable_files_verified':sum(1 for old in before if sha(moves.get(old,old))==before[old]['sha256'])}
    (BASE/'catalog/organisation_audit.json').write_text(json.dumps(audit,indent=2)+'\n')
    (BASE/'README.md').write_text('''# Supervisor reports

Loose files are organised by purpose. Existing dated meeting packages remain in their original folders.

|Folder|Contents|
|---|---|
|[reports](reports/)|Gate 0/1, Gate 5, Gate 6 and Mode-I scientific reports|
|[progress_updates](progress_updates/)|Progress reports and submission notes, grouped by date|
|[figures](figures/)|Plots and figure PDFs for Gate 6 and Mode-I|
|[data](data/)|JSON/CSV numerical audits and extracted tables|
|[correspondence](correspondence/)|ABAQUSER requests and author-inquiry drafts|
|[planning_and_decisions](planning_and_decisions/)|Plans, checklists, protocols and decision notes|
|[archive](archive/)|Historical backups, ZIP packages, LaTeX build files and original checksum manifest|
|[catalog](catalog/)|Organisation audit and maintenance helper|

[FILE_INDEX.csv](FILE_INDEX.csv) maps every moved file from its previous path to its new path and records hashes before and after organisation. Only link paths in Markdown/TeX were adjusted; numerical data, images, PDFs and backups are unchanged. No files were deleted.

`MANIFEST.sha256` contains current checksums; the previous historical manifest is preserved in `archive/manifests/` and its old paths can be resolved using the index.

This operation is confined to this folder. Historical references and figure generators elsewhere in the repository were not edited while AGY is working; the four known external generator/config paths are listed in `catalog/organisation_audit.json`. Use the index to resolve their legacy paths before rerunning them.
''',encoding='utf-8')
    # No original file may be missing. Binary/numerical evidence and backups stay byte-identical.
    for old,meta in before.items():
        new=moves.get(old,old);assert new.is_file()
        if new.suffix.lower() not in ('.md','.tex') or 'archive' in new.relative_to(BASE).parts:assert sha(new)==meta['sha256']
    manifest=BASE/'MANIFEST.sha256';manifest.write_text(''.join(sha(p)+'  '+p.relative_to(BASE).as_posix()+'\n' for p in sorted(BASE.rglob('*')) if p.is_file() and p!=manifest and '__pycache__' not in p.parts),encoding='utf-8')
    tracked=set(subprocess.check_output(['git','ls-files'],cwd=ROOT,text=True).splitlines())
    own=[p.relative_to(ROOT).as_posix() for p in moves if p.relative_to(ROOT).as_posix() in tracked]
    own += [p.relative_to(ROOT).as_posix() for p in moves.values()]
    own += ['docs/supervisor_reports/'+p for p in updated]
    own += ['docs/supervisor_reports/README.md','docs/supervisor_reports/FILE_INDEX.csv','docs/supervisor_reports/MANIFEST.sha256','docs/supervisor_reports/catalog/organisation_audit.json','docs/supervisor_reports/catalog/organize_files.py']
    (BASE/'catalog/commit_paths.json').write_text(json.dumps(sorted(set(own)),indent=2)+'\n')
    # Include commit metadata itself in the current checksum manifest.
    manifest.write_text(''.join(sha(p)+'  '+p.relative_to(BASE).as_posix()+'\n' for p in sorted(BASE.rglob('*')) if p.is_file() and p!=manifest and '__pycache__' not in p.parts),encoding='utf-8')
    print(json.dumps(audit,indent=2))
if __name__=='__main__':main()
