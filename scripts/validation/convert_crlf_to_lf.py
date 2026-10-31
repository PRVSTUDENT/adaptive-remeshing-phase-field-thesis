from pathlib import Path
import hashlib
import json

repo = Path(__file__).resolve().parents[2]
pkg = repo / "models/pandey_kumar_mode1/150_c4_package150_c1_2_continuation"
pbs = pkg / "submit_M1_C4_P150_C1_2.pbs"

raw = pbs.read_bytes().replace(b"\r\n", b"\n")
pbs.write_bytes(raw)
print("Converted %s to LF, bytes: %d" % (pbs.name, len(raw)))

# Update manifests
for mname in ["PACKAGE_MANIFEST.json", "EXECUTION_MANIFEST.json"]:
    mpath = pkg / mname
    data = json.loads(mpath.read_text())
    data["files"][pbs.name] = hashlib.sha256(raw).hexdigest().lower()
    mpath.write_text(json.dumps(data, indent=2) + "\n")
    print("Updated %s: %s = %s" % (mname, pbs.name, data["files"][pbs.name]))
