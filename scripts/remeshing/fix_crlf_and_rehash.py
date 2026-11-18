# -*- coding: utf-8 -*-
import os
import hashlib
import json

base_dir = r"models/pandey_kumar_mode1/286_f1859_four_benchmark_reference_comparison"

def sha256_file(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest().upper()

converted = 0
for root, dirs, files in os.walk(base_dir):
    for f in files:
        if f.endswith(('.pbs', '.sh', '.for', '.inp', '.json')):
            if f.endswith('.json') and 'receipt' in f:
                continue
            p = os.path.join(root, f)
            with open(p, 'rb') as fp:
                data = fp.read()
            if b'\r\n' in data:
                data_lf = data.replace(b'\r\n', b'\n')
                with open(p, 'wb') as fp:
                    fp.write(data_lf)
                converted += 1
                print(f"Converted {f} to LF ({len(data)} -> {len(data_lf)} bytes)")

print(f"Total files converted to LF: {converted}")

# Now update f1859_suite_receipt.json with updated SHAs
receipt_path = os.path.join(base_dir, "f1859_suite_receipt.json")
with open(receipt_path, "r", encoding="utf-8") as f:
    receipt = json.load(f)

for jname, job in receipt["jobs"].items():
    deck_path = job["deck_path"]
    pbs_path = job["pbs_script"]
    if os.path.exists(deck_path):
        job["deck_sha256"] = sha256_file(deck_path)
    if os.path.exists(pbs_path):
        job["pbs_sha256"] = sha256_file(pbs_path)

with open(receipt_path, "w", encoding="utf-8", newline="\n") as f:
    json.dump(receipt, f, indent=2)

print("Updated f1859_suite_receipt.json with new hashes.")
