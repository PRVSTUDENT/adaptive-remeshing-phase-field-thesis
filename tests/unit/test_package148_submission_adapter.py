"""No network or real profiles/jobs: submission receipt regression fixtures."""
import hashlib
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from scripts.validation.execute_package148_state_transfer import MANIFEST, execute, verified_receipt


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
