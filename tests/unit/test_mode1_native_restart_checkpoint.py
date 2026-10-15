import importlib.util
from pathlib import Path
import types
import unittest

path=Path(__file__).resolve().parents[2]/'scripts/postprocessing/inspect_mode1_native_restart_checkpoint.py'
spec=importlib.util.spec_from_file_location('checkpoint',path)
module=importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class CheckpointTests(unittest.TestCase):
    def fixture(self):
        fields={}
        for name,data in [('U',(0.0,0.005)),('RF',(0.0,0.65))]:
            fields[name]=types.SimpleNamespace(values=[types.SimpleNamespace(nodeLabel=999999,data=data)])
        for name,data in [('SDV2',1.0),('SDV14',0.095),('SDV17',0.01),('SDV18',0.1)]:
            fields[name]=types.SimpleNamespace(values=[types.SimpleNamespace(data=data)])
        frame=types.SimpleNamespace(frameValue=1.0,incrementNumber=500,fieldOutputs=fields)
        return types.SimpleNamespace(steps={'Step-1':types.SimpleNamespace(frames=[frame])}),frame

    def test_real_values_reported_without_claiming_restoration(self):
        odb,frame=self.fixture()
        result=module.inspect(odb)
        self.assertAlmostEqual(result['rp_reaction_N'],650.0)
        self.assertEqual(result['recipient_restoration'],'NOT_YET_TESTED')

    def test_incomplete_or_missing_or_nonfinite_state_rejected(self):
        for kind in ('incomplete','missing_rp','missing_history','nonfinite','bad_damage'):
            odb,frame=self.fixture()
            if kind=='incomplete':frame.frameValue=0.99
            if kind=='missing_rp':frame.fieldOutputs['U'].values=[]
            if kind=='missing_history':del frame.fieldOutputs['SDV2']
            if kind=='nonfinite':frame.fieldOutputs['RF'].values[0].data=(0.0,float('nan'))
            if kind=='bad_damage':frame.fieldOutputs['SDV14'].values[0].data=1.5
            with self.assertRaises(ValueError):module.inspect(odb)


if __name__=='__main__':unittest.main()
