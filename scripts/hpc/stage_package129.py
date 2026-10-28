import os
import sys
import json
import base64
import tarfile
import gzip
import traceback
from pathlib import Path

try:
    REPO_ROOT = Path("D:/Master thesis/Adaptive remeshing")
    PKG_DIR = REPO_ROOT / "models/pandey_kumar_mode1/129_c4_inc87_h9_continuation"
    REMOTE_DIR = "/scratch9/pr21vyci/runs/mode1_c4_inc87_h9_continuation"

    manifest_path = PKG_DIR / "PACKAGE_MANIFEST.json"
    with open(manifest_path, "r", encoding="utf-8") as f:
        manifest = json.load(f)

    files_to_stage = list(manifest.get("files", {}).keys())
    print("Files to stage count:", len(files_to_stage), flush=True)

    plain_tar = REPO_ROOT / "scripts/hpc/package129_stage_bundle.tar"
    gz_tar = REPO_ROOT / "scripts/hpc/package129_stage_bundle.tar.gz"

    with tarfile.open(plain_tar, mode="w") as tar:
        for fname in sorted(files_to_stage):
            p = (PKG_DIR / fname).resolve()
            if p.is_file():
                print("Adding:", fname, flush=True)
                tar.add(str(p), arcname=fname)
            else:
                raise FileNotFoundError(f"Missing file: {p}")

    print("Plain tar created, size:", plain_tar.stat().st_size, flush=True)

    with open(plain_tar, "rb") as f_in, open(gz_tar, "wb") as f_out:
        f_out.write(gzip.compress(f_in.read(), compresslevel=6))

    print("Gz tar created, size:", gz_tar.stat().st_size, flush=True)
    plain_tar.unlink()

    with open(gz_tar, "rb") as f:
        tar_bytes = f.read()

    tar_b64 = base64.b64encode(tar_bytes).decode("ascii")

    print("Bundle size: %d bytes, base64 length: %d chars" % (len(tar_bytes), len(tar_b64)), flush=True)

    out_sh = REPO_ROOT / "scripts/hpc/stage_package129_remote.sh"
    with open(out_sh, "w", newline="\n", encoding="utf-8") as f:
        f.write("#!/bin/bash\nset -euo pipefail\n")
        f.write("mkdir -p %s\n" % REMOTE_DIR)
        f.write("python3 -c \"import base64, tarfile, io, os; os.makedirs('%s', exist_ok=True); tarfile.open(fileobj=io.BytesIO(base64.b64decode('%s'))).extractall('%s')\"\n" % (REMOTE_DIR, tar_b64, REMOTE_DIR))
        f.write("chmod +x %s/*.sh %s/*.pbs 2>/dev/null || true\n" % (REMOTE_DIR, REMOTE_DIR))
        f.write("echo 'STAGING_COMPLETE'\n")

    print("Wrote stage script to", str(out_sh), flush=True)

except Exception as e:
    print("FATAL ERROR IN SCRIPT:")
    traceback.print_exc()
    sys.exit(1)
