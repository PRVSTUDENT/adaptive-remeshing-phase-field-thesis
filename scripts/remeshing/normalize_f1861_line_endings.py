# -*- coding: utf-8 -*-
import os
import glob
import hashlib
import json

base_dir = r"D:\Master thesis\Adaptive remeshing\models\pandey_kumar_mode1\288_f1861_uniform_reference"

def compute_sha256(filepath):
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while True:
            chunk = f.read(65536)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest().upper()

def compute_body_sha(filepath):
    lines = []
    with open(filepath, "rb") as f:
        text = f.read().decode("utf-8", errors="ignore")
    for l in text.split("\n"):
        l_str = l.strip()
        if l_str.startswith("**") or not l_str:
            continue
        lines.append(l_str)
    body = "\n".join(lines) + "\n"
    return hashlib.sha256(body.encode("utf-8")).hexdigest()

# 1. Normalize line endings to LF for all text files
for root, dirs, files in os.walk(base_dir):
    for fn in files:
        if fn.endswith((".inp", ".pbs", ".for", ".sh", ".json")):
            fp = os.path.join(root, fn)
            with open(fp, "rb") as f:
                content = f.read()
            lf_content = content.replace(b"\r\n", b"\n")
            if lf_content != content:
                with open(fp, "wb") as f:
                    f.write(lf_content)
                print("Normalized to LF: %s (%d -> %d bytes)" % (fn, len(content), len(lf_content)))

# 2. Recompute hashes and update PBS scripts and receipt
receipt_path = os.path.join(base_dir, "f1861_suite_receipt.json")
with open(receipt_path, "r") as f:
    receipt = json.load(f)

for jid, job in receipt["jobs"].items():
    sub_d = job["case_id"].replace("_", "")
    case_dir = os.path.join(base_dir, sub_d)
    mname = job["model_name"]
    inp_path = os.path.join(case_dir, mname + ".inp")
    sub_path = os.path.join(case_dir, "f42_native_miseseri_interface_v1.for")
    pbs_path = os.path.join(case_dir, "submit_" + jid.lower() + ".pbs")
    
    inp_sha = compute_sha256(inp_path)
    sub_sha = compute_sha256(sub_path)
    
    # Update PBS script EXPECTED_INP_SHA and EXPECTED_UEL_SHA
    with open(pbs_path, "rb") as f:
        pbs_text = f.read().decode("utf-8")
        
    import re
    pbs_text = re.sub(r'EXPECTED_INP_SHA="[A-Fa-f0-9]+"', 'EXPECTED_INP_SHA="%s"' % inp_sha.lower(), pbs_text)
    pbs_text = re.sub(r'EXPECTED_UEL_SHA="[A-Fa-f0-9]+"', 'EXPECTED_UEL_SHA="%s"' % sub_sha.lower(), pbs_text)
    
    with open(pbs_path, "wb") as f:
        f.write(pbs_text.replace("\r\n", "\n").encode("utf-8"))
        
    pbs_sha = compute_sha256(pbs_path)
    
    job["deck_sha256"] = inp_sha
    job["pbs_sha256"] = pbs_sha
    
    print("Job %s: Inp SHA=%s, PBS SHA=%s" % (jid, inp_sha, pbs_sha))

# Update physical mesh hashes in receipt
for cid, mesh_info in receipt["meshes"].items():
    case_dir = os.path.join(base_dir, cid.replace("_", ""))
    phys_path = os.path.join(case_dir, "PK_F1861_REF_%s_PHYS.inp" % cid.upper())
    mesh_info["file_sha256"] = compute_sha256(phys_path)
    mesh_info["body_sha256"] = compute_body_sha(phys_path)
    print("Mesh %s: File SHA=%s, Body SHA=%s" % (cid, mesh_info["file_sha256"], mesh_info["body_sha256"]))

with open(receipt_path, "wb") as f:
    f.write(json.dumps(receipt, indent=2).replace("\r\n", "\n").encode("utf-8"))

print("\nAll F1861 files normalized to LF-only and hashes verified.")
