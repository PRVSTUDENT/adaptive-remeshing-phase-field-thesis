# -*- coding: utf-8 -*-
"""Stage F1648 finer mesh files to cluster scratch."""
import subprocess
import os
import hashlib
from pathlib import Path

config = os.path.expanduser("~/.ssh/codex_config")
local_dir = Path("models/pandey_kumar_mode1/176_method_a_plate_with_hole")
remote_dir = "tu_freiberg:/scratch9/pr21vyci/runs/mode1_method_a_hole_finer"

files_to_upload = [
    "PK_HOLE_METHOD_A_FINER.inp",
    "f42_mixed_uel.for",
    "job_notifications.sh",
    "submit_M1_HOLE_METHOD_A_FINER.pbs"
]

print("=== Staging F1648 Files to Cluster ===")
for f in files_to_upload:
    local_path = local_dir / f
    if not local_path.exists():
        raise FileNotFoundError("Missing local file: %s" % local_path)
    
    with open(local_path, "rb") as fp:
        h = hashlib.sha256(fp.read()).hexdigest()
    print("Uploading: %s (SHA256: %s, size: %d bytes)..." % (f, h, local_path.stat().st_size))
    
    remote_target = "%s/%s" % (remote_dir, f)
    cmd = [
        "scp.exe", "-B", "-o", "BatchMode=yes", "-o", "ConnectTimeout=30",
        "-F", config, str(local_path), remote_target
    ]
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode != 0:
        print("SCP Failed for %s!" % f)
        print("STDERR:", res.stderr.strip())
        raise RuntimeError("SCP upload failed: %s" % res.stderr)
    print("  -> Upload OK!")

print("All files staged successfully.")
