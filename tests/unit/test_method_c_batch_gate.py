"""Real gate Python logic against temporary state; never invokes PBS or WSL."""
import contextlib
import base64
import gzip
from datetime import datetime, timezone, timedelta
import hashlib
import io
import json
import os
from pathlib import Path
import re
import sys
import subprocess
import tempfile
import types
import unittest
from unittest.mock import patch


def digest(data):
    return hashlib.sha256(data).hexdigest()


class BatchGateTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.candidate = self.root / 'candidate.pbs'
        self.candidate.write_bytes(b'fixture')
        self.commands = ['qsub donor.pbs', 'qsub prod.pbs', 'qsub diag.pbs']
        self.hashes = [digest(c.encode()) for c in self.commands]
        self.manifest = dict(max_submissions=3, files={'candidate.pbs': digest(b'fixture')},
                             dependency_review_path='review.json', jobs=[
                                 dict(id=name, command=c, command_sha256=h, max_submissions=1,
                                      depends_on=[] if name == 'donor' else ['donor_checkpoint_review'])
                                 for name, c, h in zip(['donor', 'prod', 'diag'], self.commands, self.hashes)])
        self.manifest_path = self.root / 'batch.json'
        self.manifest_path.write_text(json.dumps(self.manifest))
        self.manifest_hash = digest(self.manifest_path.read_bytes())
        future = (datetime.now(timezone.utc)+timedelta(hours=24)).isoformat()
        self.state = dict(daily_chatgpt_delegation=dict(active=True, expires_at=future, max_concurrent_jobs=10), jobs={},
                          submission_authorization=dict(active=True, consumed=0, max_submissions=3, expires_at=future,
                              authorized_commands=self.commands, candidate_manifest_sha256=self.manifest_hash,
                              batch_manifest_path=str(self.manifest_path), batch_package_path=str(self.root), batch_repo_path=str(self.root),
                              notification_preflight=dict(passed=True, pbs_email_verified=True, telegram_verified=True,
                                  candidate_manifest_sha256=self.manifest_hash, file_hashes=self.manifest['files'])))
        source = (Path(__file__).resolve().parents[2] / '.agents/qsub-safety-gate.ps1').read_text(encoding='utf-8-sig')
        self.code = re.search(r'\$pyCheck = @"\n(.*?)\n"@', source, re.S).group(1)
        self.path = self.root / 'state.json'
        self.code = self.code.replace('/home/openclaw/.openclaw/workspace-antigravity-controller/controller-state.json', str(self.path).replace('\\', '/'))

    def gate(self, command):
        self.path.write_text(json.dumps(self.state))
        output = io.StringIO()
        fake = types.SimpleNamespace(LOCK_EX=1, LOCK_UN=2, flock=lambda *args: None)
        with patch.dict(sys.modules, {'fcntl': fake}), patch.object(sys, 'argv', ['test', command, self.context()]), contextlib.redirect_stdout(output):
            try:
                exec(compile(self.code, 'isolated-batch-gate', 'exec'), {})
            except SystemExit as error:
                status = error.code
        self.state = json.loads(self.path.read_text())
        return status, output.getvalue()

    def context(self):
        data=dict(manifest_bytes_b64=base64.b64encode(self.manifest_path.read_bytes()).decode(),
                  file_hashes={'candidate.pbs':digest(self.candidate.read_bytes())})
        if (self.root/'review.json').exists():
            data['dependency_review']=json.loads((self.root/'review.json').read_text())
        return base64.b64encode(gzip.compress(json.dumps(data).encode())).decode()

    def test_donor_once_and_dependencies_fail_without_consuming(self):
        self.assertEqual(self.gate(self.commands[1])[0], 1)
        self.assertEqual(self.state['submission_authorization']['consumed'], 0)
        self.assertEqual(self.gate(self.commands[0])[0], 0)
        self.assertEqual(self.gate(self.commands[0])[0], 1)
        self.assertEqual(self.gate(self.commands[1])[0], 1)
        self.assertEqual(self.state['submission_authorization']['consumed'], 1)

    def test_unknown_changed_manifest_changed_file_expiry_and_exhaustion(self):
        self.assertEqual(self.gate('qsub unrelated.pbs')[0], 1)
        self.candidate.write_bytes(b'changed')
        self.assertEqual(self.gate(self.commands[0])[0], 1)
        self.candidate.write_bytes(b'fixture')
        self.manifest_path.write_text('{}')
        self.assertEqual(self.gate(self.commands[0])[0], 1)
        self.manifest_path.write_text(json.dumps(self.manifest))
        self.state['submission_authorization']['expires_at']='2020-01-01T00:00:00+00:00'
        self.assertEqual(self.gate(self.commands[0])[0], 1)
        self.state['submission_authorization']['expires_at']=(datetime.now(timezone.utc)+timedelta(hours=1)).isoformat()
        self.state['submission_authorization']['consumed']=3
        self.assertEqual(self.gate(self.commands[0])[0], 1)

    def test_review_unlocks_two_distinct_recipients_only_once(self):
        self.assertEqual(self.gate(self.commands[0])[0], 0)
        review=dict(batch_manifest_sha256=self.manifest_hash, donor_terminal_exit_status=0,
                    checkpoint_verified=True, scientific_review='PASS', handoff_displacement_mm=0.005,
                    donor_pbs_job_id='1414000.mmaster02', checkpoint_hashes={'checkpoint.res': 'a'*64},
                    reviewed_by='fixture', evidence_report='fixture')
        (self.root/'review.json').write_text(json.dumps(review))
        self.assertEqual(self.gate(self.commands[1])[0], 0)
        self.assertEqual(self.gate(self.commands[1])[0], 1)
        self.assertEqual(self.gate(self.commands[2])[0], 0)
        auth=self.state['submission_authorization']
        self.assertEqual(auth['consumed'], 3)
        self.assertFalse(auth['active'])
        self.assertEqual(len(auth['consumption_audit']), 3)

    @unittest.skipUnless(os.name == 'posix', 'Real fcntl concurrency checked on WSL')
    def test_real_lock_prevents_two_simultaneous_donor_consumptions(self):
        self.path.write_text(json.dumps(self.state))
        processes = [subprocess.Popen([sys.executable, '-c', self.code, self.commands[0], self.context()],
                                      stdout=subprocess.PIPE, stderr=subprocess.PIPE) for _ in range(2)]
        results = [p.communicate(timeout=15) for p in processes]
        self.assertEqual(sorted(p.returncode for p in processes), [0, 1])
        auth=json.loads(self.path.read_text())['submission_authorization']
        self.assertEqual(auth['consumed'], 1)
        self.assertEqual(auth['command_consumption'][self.hashes[0]], 1)

    @unittest.skipUnless(os.name == 'nt', 'Native PowerShell hook detection checked on Windows')
    def test_hook_recognizes_routed_commands_before_python_validation(self):
        source=(Path(__file__).resolve().parents[2]/'.agents/qsub-safety-gate.ps1').read_text()
        expression=re.search(r'^    \$isSubmissionCmd = (.*)$', source, re.M).group(1)
        script="$cases=@('qsub donor.pbs','qsub -q entry_imfdfkmq donor.pbs','powershell -File guard.ps1 -RemoteCommand \"qsub -q entry_imfdfkmq donor.pbs\"'); foreach($cmd in $cases){ if(-not "+expression+"){throw 'Submission detection bypass'}}"
        script+="; $cmd='powershell -File .agents/qsub-safety-gate.ps1'; if("+expression+"){throw 'Hook filename mistaken for executable'}"
        path=self.root/'detection.ps1'
        path.write_text(script)
        result=subprocess.run(['powershell.exe','-NoProfile','-File',str(path)],stdin=subprocess.DEVNULL,capture_output=True,text=True)
        self.assertEqual(result.returncode,0,result.stderr)


if __name__ == '__main__':
    unittest.main()
