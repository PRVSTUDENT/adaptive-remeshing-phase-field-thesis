"""No network or real profiles/jobs: submission receipt regression fixtures."""
import hashlib
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from scripts.validation.execute_package148_state_transfer import MANIFEST, OPERATION, execute, verified_receipt, operation_contract


class SubmissionAdapterTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        p = self.root/MANIFEST
        p.parent.mkdir(parents=True)
        p.write_text(json.dumps({'jobs':[{'command_sha256':'a'*64}]}))
        self.key = hashlib.sha256(p.read_bytes()).hexdigest()
        (self.root/'project_coordination').mkdir()

    def receipt(self, job='123.mmaster02', command='a'*64, ledger=True):
        (self.root/'project_coordination/MODE1_BATCH_SUBMISSIONS.json').write_text(json.dumps({self.key:{'M1_C4_P148_R1':{'pbs_job_id':job,'command_sha256':command}}}))
        (self.root/'project_coordination/HPC_JOB_LEDGER.csv').write_text('Job_ID,Job_Name\n'+(job+',M1_C4_P148_R1\n' if ledger else ''))

    def test_authentic_receipt(self):
        self.receipt()
        self.assertEqual(verified_receipt(self.root), '123.mmaster02')

    def test_reject_fabricated_id(self):
        self.receipt('PENDING')
        with self.assertRaises(ValueError): verified_receipt(self.root)

    def test_reject_wrong_command(self):
        self.receipt(command='b'*64)
        with self.assertRaises(ValueError): verified_receipt(self.root)

    def test_require_ledger(self):
        self.receipt(ledger=False)
        with self.assertRaises(ValueError): verified_receipt(self.root)

    def test_gate_failure_never_creates_success(self):
        calls=[]
        def fail(args, **kw):
            calls.append(args)
            if len(calls)==2: raise subprocess.CalledProcessError(1,args)
        output=self.root/'results/validation/result.json'
        with self.assertRaises(subprocess.CalledProcessError): execute(self.root, output, runner=fail)
        self.assertFalse(output.exists())
        self.assertIn('Invoke-Mode1Execution.ps1', str(calls[-1]))
        self.assertFalse(any('qsub' in str(c) for c in calls))

    def test_reject_output_replay(self):
        output=self.root/'results/validation/result.json'
        output.parent.mkdir(parents=True);output.write_text('preserve')
        with self.assertRaises(ValueError): execute(self.root, output)
        self.assertEqual(output.read_text(),'preserve')

    def test_r2_receipt_cannot_reuse_r1(self):
        relative, job, qualification=operation_contract(OPERATION+'_r2')
        self.assertIn('_r2/',relative);self.assertEqual(job,'M1_C4_P148_R2')
        self.receipt()
        target=self.root/relative;target.parent.mkdir(parents=True);target.write_bytes((self.root/MANIFEST).read_bytes())
        with self.assertRaises(ValueError):verified_receipt(self.root,OPERATION+'_r2')

    def test_r3_contract(self):
        relative, job, qualification = operation_contract(OPERATION+'_r3')
        self.assertIn('_r3/', relative)
        self.assertEqual(job, 'M1_C4_P148_R3')
        self.assertEqual(qualification, 'scripts/validation/evaluate_mode1_package148_state_transfer_r3.qualification.json')

    def test_unknown_revision_rejected(self):
        with self.assertRaises(ValueError):operation_contract(OPERATION+'_r5')

    def test_r4_distinct_contract_and_no_predecessor_receipt(self):
        relative, job, qualification = operation_contract(OPERATION+'_r4')
        self.assertIn('_r4/', relative)
        self.assertEqual(job, 'M1_C4_P148_R4')
        self.assertEqual(qualification, 'scripts/validation/evaluate_mode1_package148_state_transfer_r4.qualification.json')
        self.receipt()
        target = self.root/relative
        target.parent.mkdir(parents=True)
        target.write_bytes((self.root/MANIFEST).read_bytes())
        with self.assertRaises(ValueError): verified_receipt(self.root, OPERATION+'_r4')

    def test_r4_exact_receipt_and_changed_manifest_rejected(self):
        relative, job, _ = operation_contract(OPERATION+'_r4')
        target = self.root/relative
        target.parent.mkdir(parents=True)
        target.write_text(json.dumps({'jobs':[{'command_sha256':'c'*64}]}))
        key = hashlib.sha256(target.read_bytes()).hexdigest()
        (self.root/'project_coordination/MODE1_BATCH_SUBMISSIONS.json').write_text(json.dumps({key:{job:{'pbs_job_id':'789.mmaster02','command_sha256':'c'*64}}}))
        (self.root/'project_coordination/HPC_JOB_LEDGER.csv').write_text('Job_ID,Job_Name\n789.mmaster02,'+job+'\n')
        self.assertEqual(verified_receipt(self.root, OPERATION+'_r4'), '789.mmaster02')
        target.write_text(target.read_text()+' ')
        with self.assertRaises(ValueError): verified_receipt(self.root, OPERATION+'_r4')

    def test_authentic_r2_receipt_and_changed_manifest(self):
        relative, job, _=operation_contract(OPERATION+'_r2')
        target=self.root/relative;target.parent.mkdir(parents=True)
        target.write_text(json.dumps({'jobs':[{'command_sha256':'b'*64}]}))
        key=hashlib.sha256(target.read_bytes()).hexdigest()
        (self.root/'project_coordination/MODE1_BATCH_SUBMISSIONS.json').write_text(json.dumps({key:{job:{'pbs_job_id':'456.mmaster02','command_sha256':'b'*64}}}))
        (self.root/'project_coordination/HPC_JOB_LEDGER.csv').write_text('Job_ID,Job_Name\n456.mmaster02,'+job+'\n')
        self.assertEqual(verified_receipt(self.root,OPERATION+'_r2'),'456.mmaster02')
        target.write_text(target.read_text()+' ')
        with self.assertRaises(ValueError):verified_receipt(self.root,OPERATION+'_r2')
