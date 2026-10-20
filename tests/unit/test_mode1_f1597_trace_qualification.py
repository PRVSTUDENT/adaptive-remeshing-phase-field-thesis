"""No remote commands or solver calls: exact adapter and manufactured parity tests."""
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'scripts/validation'))
import qualify_mode1_f1597_trace as qualification
spec=importlib.util.spec_from_file_location('trace_engine',ROOT/'scripts/hpc/mode1_execution_gate.py')
engine=importlib.util.module_from_spec(spec);spec.loader.exec_module(engine)


class AdapterTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name);self.folder=self.root/qualification.PACKAGE;self.folder.mkdir(parents=True)
        source=ROOT/qualification.PACKAGE
        self.batch=json.loads((source/'TRACE_BATCH.json').read_text())
        for name in self.batch['files']:(self.folder/name).write_bytes((source/name).read_bytes())
        self.path=self.folder/'TRACE_BATCH.json';self.write()

    def write(self): self.path.write_text(json.dumps(self.batch))

    def test_exact_trace_manifest_accepted(self):
        self.assertEqual(engine.validate_manifest(self.path,self.root)[0]['max_submissions'],1)

    def test_arbitrary_logging_block_payload_rejected(self):
        path=self.folder/'f42_history_trace_uel.for'
        path.write_bytes(path.read_bytes().replace(b'SEQ=SEQ+1',b'SEQ=SEQ+2'))
        self.batch['files'][path.name]=hashlib.sha256(path.read_bytes()).hexdigest();self.write()
        with self.assertRaisesRegex(ValueError,'deterministic logging'):
            engine.validate_manifest(self.path,self.root)

    def test_changed_receiver_rejected(self):
        path=self.folder/'offset_state_table.csv';path.write_bytes(path.read_bytes()+b'\n')
        self.batch['files'][path.name]=hashlib.sha256(path.read_bytes()).hexdigest();self.write()
        with self.assertRaisesRegex(ValueError,'unchanged receiver'):
            engine.validate_manifest(self.path,self.root)

    def test_resources_not_expanded(self):
        self.batch['jobs'][0]['cpus']=8;self.write()
        with self.assertRaisesRegex(ValueError,'Resource bounds'):
            engine.validate_manifest(self.path,self.root)


class ParityTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup);self.root=Path(self.temp.name)
        self.base=self.root/(qualification.PARENT+'evidence_1415199');self.base.mkdir(parents=True)
        self.evidence=self.root/qualification.PACKAGE/'evidence';self.evidence.mkdir(parents=True)
        self.force='999999 0.0 0.001\n999999 0.0001 0.002\n'
        self.energy='Step,Increment,TotalTime,StepTime,E1,E2,E3\n1,1,1,1,0.001,0.002,0.003\n2,1,2,1,0.002,0.003,0.005\n'
        (self.base/'M1_EXP_COUPLED_TRANSFER_650.dat').write_text(self.force)
        (self.base/'uel_energy_balance.csv').write_text(self.energy)
        (self.evidence/'solver.dat').write_text(self.force);(self.evidence/'uel_energy_balance.csv').write_text(self.energy)
        plan=dict(baseline_sources={p.relative_to(self.root).as_posix():qualification.digest(p.read_bytes()) for p in self.base.iterdir()},force_rtol=1e-8,force_atol_kN=1e-12,energy_rtol=1e-8,energy_atol_kNmm=1e-14)
        (self.root/qualification.PACKAGE/'PARITY_PLAN.json').write_text(json.dumps(plan))

    def test_identical_outputs_pass_all_samples(self):
        p=qualification.compare_parity(self.root,self.evidence)
        self.assertEqual((p['force_samples'],p['accepted_increments']),(2,2))

    def test_changed_force_rejected(self):
        (self.evidence/'solver.dat').write_text(self.force.replace('0.002','0.003'))
        with self.assertRaisesRegex(ValueError,'parity failed'):qualification.compare_parity(self.root,self.evidence)

    def test_nonfinite_energy_rejected(self):
        (self.evidence/'uel_energy_balance.csv').write_text(self.energy.replace('0.005','NaN'))
        with self.assertRaisesRegex(ValueError,'Nonfinite'):qualification.compare_parity(self.root,self.evidence)

    def test_missing_increment_rejected(self):
        (self.evidence/'uel_energy_balance.csv').write_text('\n'.join(self.energy.splitlines()[:-1])+'\n')
        with self.assertRaisesRegex(ValueError,'Changed accepted increments'):qualification.compare_parity(self.root,self.evidence)


if __name__=='__main__':unittest.main()
