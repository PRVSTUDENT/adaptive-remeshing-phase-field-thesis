import importlib.util
import json
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CTL = ROOT / 'models/generated/mode_ii/f19_penalty_active_rollback_control'
FRC = ROOT / 'models/generated/mode_ii/f19_penalty_active_rollback_forced'
REG = ROOT / 'models/generated/mode_ii/f19_native_adaptive_region_repair'

def load_collector():
    path = REG / 'runtime/collect_f19_adaptive_evidence.py'
    spec = importlib.util.spec_from_file_location('collector', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

class StageF19Tests(unittest.TestCase):
    def test_shared_scientific_files_are_identical(self):
        for name in ['M2IRR_F18.for', 'M2IRR_F18.inp', 'extract_stage_f18_rollback.py',
                     'analyze_stage_f18_rollback.py', 'f19_flag_io_harness.for']:
            self.assertEqual((CTL / 'runtime' / name).read_bytes(), (FRC / 'runtime' / name).read_bytes(), name)

    def test_required_flag_contract_is_fail_closed(self):
        source = (CTL / 'runtime/M2IRR_F18.for').read_text(encoding='utf-8')
        self.assertIn('INQUIRE(FILE=TRIM(PATH),EXIST=EXISTS,IOSTAT=IOS)', source)
        self.assertNotIn("'_f18_force_enabled.flag'", source)
        self.assertIn("'_f19_force_mode.flag'", source)
        self.assertIn("'_f19_cutback_state.flag'", source)
        for token in ['OPEN(UNIT=97', 'READ(97,*,IOSTAT=IOS)', "WRITE(97,'(I1)',IOSTAT=IOS)", 'CLOSE(97,IOSTAT=CIOS)']:
            self.assertIn(token, source)

    def test_wrappers_create_exact_values(self):
        control = (CTL / 'M2IRRROLLCTL5.pbs').read_text(encoding='utf-8')
        forced = (FRC / 'M2IRRROLLFORCE5.pbs').read_text(encoding='utf-8')
        self.assertIn("printf '0\\n' > \"$mode_file\"", control)
        self.assertIn("printf '1\\n' > \"$mode_file\"", forced)
        self.assertIn("printf '0\\n' > \"$state_file\"", control)
        self.assertIn("printf '0\\n' > \"$state_file\"", forced)

    def test_adaptive_wrapper_preserves_return_code_order(self):
        wrapper = (REG / 'M2RMREG6.pbs').read_text(encoding='utf-8')
        self.assertLess(wrapper.index('test $compatibility_rc -eq 0'), wrapper.index('abaqus cae'))
        self.assertLess(wrapper.index('test $cae_rc -eq 0'), wrapper.index('test $collector_rc -eq 0'))
        self.assertIn('$WORK_ROOT/generated_evidence', wrapper)

    def test_collector_success_and_missing_output(self):
        collector = load_collector()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); work = root / 'work'; final = root / 'final'; work.mkdir(); final.mkdir()
            for name in collector.EXPECTED:
                (work / name).write_text('{}\n', encoding='utf-8')
            (work / 'compatibility.stdout').write_text('ok\n', encoding='utf-8')
            self.assertEqual(collector.collect(str(work), str(final), 0, 0), 0)
            self.assertTrue((final / 'EVIDENCE_MANIFEST.sha256').is_file())
            (work / 'STATUS.json').unlink()
            self.assertEqual(collector.collect(str(work), str(final), 0, 9), 1)
            report = json.loads((final / 'MISSING_EVIDENCE_REPORT.json').read_text(encoding='utf-8'))
            self.assertEqual(report[0]['generating_command_return_code'], 9)

    def test_manifests_identical_and_valid(self):
        for package in [CTL, FRC, REG]:
            self.assertEqual((package / 'F19_SHA256SUMS').read_bytes(), (package / 'SHA256SUMS').read_bytes())
            for line in (package / 'F19_SHA256SUMS').read_text(encoding='ascii').splitlines():
                expected, relative = line.split('  ', 1)
                import hashlib
                self.assertEqual(hashlib.sha256((package / relative).read_bytes()).hexdigest(), expected)

if __name__ == '__main__':
    unittest.main()
