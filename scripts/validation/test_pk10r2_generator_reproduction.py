import sys
import os
import hashlib
from pathlib import Path

repo_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(repo_root / "scripts" / "model_generation"))

import build_pk10r2_corrected_topology_candidate as gen

test_out = Path("/tmp/pk10r2_test") if os.name != "nt" else repo_root / "temp_pk10r2_test"
test_out.mkdir(parents=True, exist_ok=True)

gen.OUT_DIR = test_out
gen.generate_corrected_package()

frozen_inp = repo_root / "models/generated/mode_ii/production_control_batch/M2CORR_PK10R2_TOPOLOGY_CORRECTED/M2CORR_PK10R2_TOPOLOGY_CORRECTED.inp"
gen_inp = test_out / "M2CORR_PK10R2_TOPOLOGY_CORRECTED.inp"

frozen_sha = hashlib.sha256(frozen_inp.read_bytes()).hexdigest()
gen_sha = hashlib.sha256(gen_inp.read_bytes()).hexdigest()

print("Frozen INP SHA256:    %s" % frozen_sha)
print("Generated INP SHA256: %s" % gen_sha)

if frozen_sha == gen_sha:
    print("Reproduction Status: BYTE_IDENTICAL")
else:
    print("Reproduction Status: DIFFERENT_HASH")
