import ast, json, os, pathlib, re, shutil, subprocess, tempfile, unittest

ROOT=pathlib.Path(__file__).resolve().parents[2]
PACKAGE=ROOT/'models/generated/mode_ii/f20_native_adaptive_region_r7'

class F20PreparationTests(unittest.TestCase):
    def test_python2_scan(self):
        prohibited=[r'\bf["\']',r'pathlib',r'subprocess\.run',r'\{[^\n]*\bfor\b[^\n]*\}',r'\b(sum|min|max|tuple)\s*\([^\n]*\bfor\b']
        for name in ('qualify_f20_adaptive_region.py','f20_abaqus_python_compatibility.py'):
            path=PACKAGE/'runtime'/name
            text=path.read_text(encoding='utf-8')
            for pattern in prohibited:
                self.assertIsNone(re.search(pattern,text),'%s: %s'%(path,pattern))
            ast.parse(text)
    def test_explicit_element_count_and_topology(self):
        text=(PACKAGE/'runtime/qualify_f20_adaptive_region.py').read_text()
        self.assertIn('for part_name in m.parts.keys()',text)
        self.assertIn("'coincident_pairs':audits",text)
        self.assertIn("'bridge_search_pass':len(bridges)==0",text)
    def test_zero_execution_and_resources(self):
        audit=json.loads((PACKAGE/'F20_NO_EXECUTION_AUDIT.json').read_text())
        for key in ('solver_executions','datacheck_executions','adaptivity_process_submissions','model_adaptiveRemesh_calls','native_remesh_calls','candidates_generated','refined_analyses'):
            self.assertEqual(audit[key],0)
        pbs=(PACKAGE/'M2RMREG7.pbs').read_text()
        self.assertIn('#PBS -q entry_imfdfkmq',pbs); self.assertIn('ncpus=1:mem=8gb',pbs); self.assertIn('walltime=00:30:00',pbs)
        self.assertNotIn('qsub ',pbs); self.assertNotIn('adaptiveRemesh(',pbs)
    def test_source_deck_hash(self):
        import hashlib
        self.assertEqual(hashlib.sha256((PACKAGE/'runtime/source_deck.inp').read_bytes()).hexdigest(),'a927b8317ff9e20bfa84dd669a2577b095e69d1bf1c343b81b158a83fd075ea2')

    def test_guarded_orchestrator_mock(self):
        script=ROOT/'scripts/hpc/stage_f/submit_stage_f20_adaptive_r7.sh'
        closed=subprocess.run(['bash',str(script)],text=True,capture_output=True)
        self.assertEqual(closed.returncode,3); self.assertIn('activation_gate_closed',closed.stdout)
        with tempfile.TemporaryDirectory() as temporary:
            base=pathlib.Path(temporary); package=base/'package'; evidence=base/'evidence'; bindir=base/'bin'
            shutil.copytree(PACKAGE,package); bindir.mkdir()
            qsub=bindir/'qsub'; qsub.write_text('#!/bin/sh\nprintf "900001.mmaster02\\n"\n'); qsub.chmod(0o755)
            env=os.environ.copy(); env.update({'PATH':str(bindir)+os.pathsep+env['PATH'],'F20_ACTIVATE_SUBMISSION':'1','F20_EXPLICIT_AUTHORIZATION':'1','F20_ADAPTIVE_PACKAGE_DIR':str(package),'F20_EVIDENCE_ROOT':str(evidence)})
            run=subprocess.run(['bash',str(script)],env=env,text=True,capture_output=True)
            self.assertEqual(run.returncode,0,run.stdout+run.stderr); self.assertIn('submitted_adaptive_r7',run.stdout)
            self.assertIn('"qsub_attempts":1',run.stdout)

if __name__=='__main__': unittest.main()
