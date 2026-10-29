"""Authentic artifact tests plus explicitly synthetic adversarial algorithm fixtures."""
import copy
import csv
import gzip
import json
import math
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT/'scripts/validation'))
import evaluate_package146_package147_results as e
import evaluate_package146_package147_evaluation_spec as spec

FIXTURES = ROOT/'tests/fixtures/package146147'


class AuthenticTextArtifacts(unittest.TestCase):
    def test_fixture_provenance(self):
        metadata = json.loads((FIXTURES/'provenance.json').read_text())
        for record in metadata.values():
            for name, sha in record['files'].items():
                self.assertEqual(e.compute_file_sha256(FIXTURES/name), sha)

    def test_donor_dat_extraction_and_mapping(self):
        nodes=set(range(1,5291))  # Pinned authentic deck labels, independent of parser.
        with gzip.open(FIXTURES/'146_step1_dat.txt.gz', 'rt') as f:
            dat=e.parse_dat_endpoint(f.read(), nodes, 76)
        self.assertEqual(len(dat), 5291)
        self.assertEqual(dat[999999][1], 0.0018003125)
        self.assertEqual(dat[999999][4], 0.18730795)
        self.assertIsNone(dat[999999][0])  # Inactive DOF must not become a fabricated zero.
        self.assertEqual(max(dat[n][2] for n in nodes), 0.49527405)

    def test_reference_dat_extraction_and_mapping(self):
        nodes=set(range(1,7266))
        with gzip.open(FIXTURES/'147_step1_dat.txt.gz','rt') as f:
            dat=e.parse_dat_endpoint(f.read(),nodes,79)
        self.assertEqual(len(dat),7266)
        self.assertEqual(dat[999999][4],0.18730824)
        self.assertEqual(max(dat[n][2] for n in nodes),0.50354272)

    def test_energy_independent_recomputation(self):
        # Independently read raw accepted CSV, not evaluator helper output.
        totals=[]
        for pkg,inc in [(146,76),(147,79)]:
            with (FIXTURES/(str(pkg)+'_energy.csv')).open() as f:
                row=next(r for r in csv.DictReader(f) if int(r['Step'])==1 and int(r['Increment'])==inc)
            recomputed=float(row['E_elastic_kNmm'])+float(row['E_fracture_kNmm'])
            extracted=e.parse_energy((FIXTURES/(str(pkg)+'_energy.csv')).read_text())[1,inc]['E_total_kNmm']
            # Independently rounded eight-significant-digit CSV columns.
            self.assertTrue(math.isclose(recomputed,extracted,rel_tol=1e-7,abs_tol=1e-14))
            totals.append(extracted)
        self.assertAlmostEqual(100*(totals[1]-totals[0])/totals[0],0.13319884944626892,places=10)

    def test_exact_pbs_identity(self):
        for pkg in (146,147):
            e.pbs_identity((FIXTURES/(str(pkg)+'_pbs.txt')).read_text(),e.PACKAGES[pkg])

    def test_wrong_pbs_identity(self):
        with self.assertRaises(e.EvidenceError):
            e.pbs_identity((FIXTURES/'146_pbs.txt').read_text(),e.PACKAGES[147])

    def test_pending_distinguished_from_failure(self):
        text=(FIXTURES/'146_pbs.txt').read_text()
        with self.assertRaises(e.Unavailable):
            e.pbs_identity(text.replace('job_state = F','job_state = R'),e.PACKAGES[146])
        with self.assertRaises(e.PhysicalFailure):
            e.pbs_identity(text.replace('Exit_status = 0','Exit_status = 1'),e.PACKAGES[146])

    def test_wrong_dat_frame(self):
        with gzip.open(FIXTURES/'146_step1_dat.txt.gz','rt') as f:
            text=f.read()
        with self.assertRaises(e.EvidenceError):
            e.parse_dat_endpoint(text,{1,2},79)

    def test_truncated_authentic_dat(self):
        nodes=set(range(1,5291))
        with gzip.open(FIXTURES/'146_step1_dat.txt.gz','rt') as f:
            text=f.read()
        with self.assertRaises(e.EvidenceError):
            e.parse_dat_endpoint(text[:len(text)//2],nodes,76)

    def test_empty_and_inconsistent_energy(self):
        with self.assertRaises(e.EvidenceError): e.parse_energy('')
        text=(FIXTURES/'146_energy.csv').read_text()
        with self.assertRaises(e.EvidenceError): e.parse_energy(text.replace('0.21270454E-03','0.90000000E-03'))

    def test_nonfinite_csv_field(self):
        text=(FIXTURES/'146_energy.csv').read_text()
        for bad in ['NaN','Inf','-Inf']:
            with self.subTest(bad=bad):
                with self.assertRaises(e.EvidenceError): e.parse_energy(text.replace('0.10000000E-02',bad,1))


class AdversarialSnapshot(unittest.TestCase):
    """Small synthetic values isolate validation; never represented as solver data."""
    def setUp(self):
        self.nodes={1,2,3,4};self.visual={10:(1,2,3,4)}
        keys=['PART:10:'+str(i) for i in range(1,5)]
        self.snapshot=dict(schema=1,step='Step-1',step_number=1,history_keys=keys,
            frames=[dict(frame_index=0,increment=0,step_time=0,rp={'u2':0,'rf2':0},history_values=[0]*4),
                    dict(frame_index=1,increment=1,step_time=0.36006251,rp={'u2':e.TARGET_DISPLACEMENT,'rf2':1},history_values=[0.1]*4)],
            nodes=[['PART:'+str(n),0,0] for n in self.nodes],
            energies=[[field,key,value] for field,value in [('SDV17',3),('SDV18',2)] for key in keys],
            history_semantics='Synthetic trial history validation fixture',odb_sha256='0'*64)
        self.dat={n:[0,0,0.2,0,0,0] for n in self.nodes};self.dat[999999]=[None,e.TARGET_DISPLACEMENT,None,None,1,None]
        self.energy={(1,1):{'StepTime':0.36006251,'E_elastic_kNmm':2,'E_fracture_kNmm':3,'E_total_kNmm':5}}
        self.sta='1 1 1 0 1 1 0.360 0.360 0.360'

    def run_reader(self):
        return e.validate_snapshot(self.snapshot,self.nodes,self.visual,self.dat,self.energy,self.sta)

    def test_independent_element_energy_sum_no_fourfold_count(self):
        r=self.run_reader();self.assertEqual(r['sdv_energy_totals'],{'SDV17':3,'SDV18':2});self.assertEqual(r['total_kNmm'],5)

    def test_nan_endpoint(self):
        self.snapshot['frames'][-1]['rp']['u2']=math.nan
        with self.assertRaises(e.EvidenceError): self.run_reader()

    def test_nan_damage(self):
        self.dat[1][2]=math.nan
        with self.assertRaises(e.EvidenceError): self.run_reader()

    def test_infinite_force(self):
        self.snapshot['frames'][-1]['rp']['rf2']=math.inf
        with self.assertRaises(e.EvidenceError): self.run_reader()

    def test_infinite_energy(self):
        self.snapshot['energies'][0][2]=math.inf
        with self.assertRaises(e.EvidenceError): self.run_reader()

    def test_empty_damage(self):
        with self.assertRaises(e.EvidenceError): e.verify_damage_admissibility([],[])

    def test_mismatched_damage_lengths(self):
        with self.assertRaises(e.EvidenceError): e.verify_damage_admissibility([0.2],[])

    def test_unphysical_damage(self):
        self.dat[1][2]=1.01
        with self.assertRaises(e.PhysicalFailure): self.run_reader()

    def test_wrong_node_mapping(self):
        self.snapshot['nodes'][0][0]='PART:500'
        with self.assertRaises(e.EvidenceError): self.run_reader()

    def test_empty_nodal_output(self):
        self.snapshot['nodes']=[]
        with self.assertRaises(e.EvidenceError): self.run_reader()

    def test_wrong_vector_dimension(self):
        self.snapshot['nodes'][0]=['PART:1',0]
        with self.assertRaises(e.EvidenceError): self.run_reader()

    def test_missing_history(self):
        self.snapshot['history_keys']=[]
        with self.assertRaises(e.EvidenceError): self.run_reader()

    def test_nan_history(self):
        self.snapshot['frames'][1]['history_values'][0]=math.nan
        with self.assertRaises(e.EvidenceError): self.run_reader()

    def test_truncated_history(self):
        self.snapshot['frames'][1]['history_values'].pop()
        with self.assertRaises(e.EvidenceError): self.run_reader()

    def test_decreasing_history(self):
        self.snapshot['frames'][0]['history_values']=[1]*4
        with self.assertRaises(e.PhysicalFailure): self.run_reader()

    def test_wrong_step(self):
        self.snapshot['step']='Step-2'
        with self.assertRaises(e.EvidenceError): self.run_reader()

    def test_wrong_frame(self):
        self.snapshot['frames'][-1]['frame_index']=2
        with self.assertRaises(e.EvidenceError): self.run_reader()

    def test_incomplete_convergence(self):
        self.sta='1 1 1U 0 1 1 0.360 0.360 0.360'
        with self.assertRaises(e.EvidenceError): self.run_reader()

    def test_missing_energy_frame(self):
        self.energy={}
        with self.assertRaises(e.EvidenceError): self.run_reader()

    def test_wrong_time(self):
        self.snapshot['frames'][-1]['step_time']=0.2
        with self.assertRaises(e.EvidenceError): self.run_reader()

    def test_preserve_unverified_irreversibility(self):
        r=self.run_reader();self.assertTrue(r['nodal_irreversibility'].startswith('UNVERIFIED'));self.assertTrue(r['committed_history_preservation'].startswith('UNVERIFIED'))


class FailClosedAndReview(unittest.TestCase):
    def test_missing_artifacts_never_compares(self):
        with tempfile.TemporaryDirectory() as t:
            r=e.evaluate(ROOT,t)
        self.assertIsNone(r['comparisons']);self.assertFalse(r['scientific_acceptance'])

    def test_zero_denominator(self):
        with self.assertRaises(e.EvidenceError): e.evaluate_energy_continuity(0,1)

    def test_rejected_nonfinite_helpers(self):
        for x in [math.nan,math.inf,-math.inf]:
            with self.subTest(x=x):
                with self.assertRaises(e.EvidenceError): e.evaluate_convergence_and_displacement(x,0)
                with self.assertRaises(e.EvidenceError): e.verify_damage_admissibility([x],[0])
                with self.assertRaises(e.EvidenceError): e.evaluate_energy_continuity(1,x)

    def test_signed_donor_denominator(self):
        self.assertEqual(e.comparison(100,102,0.02)[:2],(True,0.02))

    def test_no_self_registration_or_unbound_review_claim(self):
        r=spec.compile_review_intake();self.assertFalse(r['verification_passed']);self.assertFalse(r['executable_in_current_scope']);self.assertEqual(r['registration_status'],'NOT_REGISTERED')

    def test_output_cannot_overwrite_source(self):
        with tempfile.TemporaryDirectory() as t:
            target=Path(t)/'existing';target.write_text('preserved')
            with patch.object(sys,'argv',['reader','--artifact-root',t,'--output',str(target)]):
                with self.assertRaises(FileExistsError): e.main()
            self.assertEqual(target.read_text(),'preserved')

    def test_transport_does_not_overwrite_partial_retrieval(self):
        with tempfile.TemporaryDirectory() as t:
            (Path(t)/'146').mkdir()
            with patch.object(e.subprocess,'run') as run:
                with self.assertRaises(FileExistsError):
                    e.retrieve_authenticated_artifacts(ROOT,t,'/scratch9/pr21vyci/runs/existing_export')
                run.assert_not_called()

    def test_missing_file_manifest_never_claims_authentication(self):
        with tempfile.TemporaryDirectory() as t:
            d=Path(t)/'146';d.mkdir();cfg=e.PACKAGES[146]
            (d/'manifest.json').write_text(json.dumps({'schema':1,'job_id':cfg['job'],'remote_directory':cfg['remote']}))
            r=e.evaluate(ROOT,t)
        self.assertEqual(r['packages']['146']['status'],'UNAVAILABLE');self.assertIsNone(r['comparisons'])

    def test_tampered_artifact_fails_hash_binding(self):
        with tempfile.TemporaryDirectory() as t:
            d=Path(t)/'146';d.mkdir();cfg=e.PACKAGES[146]
            (d/'qstat.txt').write_text('altered')
            (d/'manifest.json').write_text(json.dumps({'schema':1,'job_id':cfg['job'],'remote_directory':cfg['remote'],'files':{'qstat.txt':'0'*64}}))
            r=e.evaluate(ROOT,t)
        self.assertEqual(r['packages']['146']['status'],'INVALID_EVIDENCE');self.assertIn('hash mismatch',r['packages']['146']['reason']);self.assertIsNone(r['comparisons'])

    def test_malformed_manifest_has_no_comparison(self):
        with tempfile.TemporaryDirectory() as t:
            d=Path(t)/'146';d.mkdir();(d/'manifest.json').write_text('{truncated')
            r=e.evaluate(ROOT,t)
        self.assertEqual(r['packages']['146']['status'],'INVALID_EVIDENCE');self.assertIsNone(r['comparisons'])


@unittest.skipUnless(os.environ.get('PACKAGE146147_ARTIFACT_ROOT'),'Full authentic exports are external; set PACKAGE146147_ARTIFACT_ROOT')
class FullAuthenticatedExports(unittest.TestCase):
    @classmethod
    def setUpClass(cls): cls.report=e.evaluate(ROOT,os.environ['PACKAGE146147_ARTIFACT_ROOT'])

    def test_genuine_extraction_and_independent_difference(self):
        r=self.report;self.assertIsNotNone(r['comparisons'],r)
        a,b=[r['packages'][str(p)] for p in (146,147)]
        self.assertEqual(a['node_count'],5290);self.assertEqual(b['node_count'],7265)
        self.assertEqual(a['gp_count'],20448);self.assertEqual(b['gp_count'],28224)
        self.assertEqual(a['increment'],76);self.assertEqual(b['increment'],79)
        self.assertAlmostEqual(a['RF2_kN'],0.1873079389333725,places=12)
        self.assertAlmostEqual(b['RF2_kN'],0.18730823695659637,places=12)
        self.assertAlmostEqual(r['comparisons']['Delta_E_percent'],100*(0.00021298786-0.00021270454)/0.00021270454,places=10)
        self.assertAlmostEqual(r['comparisons']['Delta_RF_percent'],100*(0.18730823695659637-0.1873079389333725)/0.1873079389333725,places=10)
        self.assertEqual(r['comparisons']['refinement_only']['coarsened_elements'],0)

    def test_no_transfer_or_unverified_irreversibility_acceptance(self):
        self.assertFalse(self.report['stage_c1_1_transfer_acceptance']);self.assertFalse(self.report['scientific_acceptance'])
        for p in self.report['packages'].values():self.assertTrue(p['nodal_irreversibility'].startswith('UNVERIFIED'))

    def test_truncated_export_is_structured_failure(self):
        with patch.object(e.gzip,'open',side_effect=EOFError('truncated export')):
            r=e.evaluate(ROOT,os.environ['PACKAGE146147_ARTIFACT_ROOT'])
        self.assertIsNone(r['comparisons'])
        for package in r['packages'].values():self.assertEqual(package['status'],'INVALID_EVIDENCE')


if __name__=='__main__': unittest.main()
