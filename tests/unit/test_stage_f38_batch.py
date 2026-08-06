import os
import sys
import json
import unittest
import tempfile
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from scripts.validation.validate_f38_comprehensive_cae_diagnostic_gate import validate_f38_static_gate

class TestStageF38Batch(unittest.TestCase):

    def test_f38_static_gate(self):
        self.assertTrue(validate_f38_static_gate())

    def test_entrypoint_has_no_file_token(self):
        entry_path = ROOT / "models/generated/mode_ii/f38_comprehensive_cae_diagnostic_matrix/runtime/run_f38_cae_diagnostic.py"
        content = entry_path.read_text(encoding="utf-8")
        self.assertNotIn("__file__", content)

    def test_entrypoint_execution_without_file_global(self):
        runtime_dir = ROOT / "models/generated/mode_ii/f38_comprehensive_cae_diagnostic_matrix/runtime"
        os.environ["F38_RUNTIME_DIR"] = str(runtime_dir)
        
        tmp_dir = tempfile.mkdtemp()
        try:
            audit_file = os.path.join(tmp_dir, "CAE_INVOCATION_CONTEXT_AUDIT.json")
            os.environ["F38_INVOCATION_AUDIT"] = audit_file
            
            entry_path = runtime_dir / "run_f38_cae_diagnostic.py"
            code = compile(entry_path.read_text(encoding="utf-8"), str(entry_path), "exec")
            
            globs = {
                "__name__": "__main__",
                "__builtins__": __builtins__
            }
            self.assertNotIn("__file__", globs)
            
            class MockMatrix:
                @staticmethod
                def main():
                    pass
                    
            sys.modules["f38_cae_diagnostic_matrix"] = MockMatrix
            
            exec(code, globs)
            
            self.assertTrue(os.path.exists(audit_file))
            with open(audit_file, "r") as f:
                audit_data = json.load(f)
            self.assertFalse(audit_data["file_global_defined"])
            self.assertTrue(audit_data["bootstrap_passed"])
        finally:
            shutil.rmtree(tmp_dir)

    def test_f37_package_unmodified(self):
        f37_dir = ROOT / "models/generated/mode_ii/f37_cae_python_compatibility_repair"
        manifest_path = f37_dir / "PACKAGE_MANIFEST.json"
        self.assertTrue(manifest_path.exists())
        with open(manifest_path, "r") as f:
            manifest = json.load(f)
        
        import hashlib
        files_map = manifest.get("package_files") or manifest.get("files") or {}
        for rel_path, expected_hash in files_map.items():
            file_path = f37_dir / rel_path
            self.assertTrue(file_path.exists(), f"F37 file {rel_path} missing")
            h = hashlib.sha256(file_path.read_bytes()).hexdigest()
            self.assertEqual(h, expected_hash, f"F37 file {rel_path} modified!")

if __name__ == "__main__":
    unittest.main()
