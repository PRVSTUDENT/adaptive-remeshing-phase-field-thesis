#!/usr/bin/env python3
import os
import hashlib
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent

def hash_file(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()

print("=== SEARCHING LOCAL COMMITTED STATE ARTIFACTS ===")
candidates = []
for p in ROOT.rglob("*"):
    if p.is_file() and (p.suffix in [".bin", ".inc"] or "STATE" in p.name.upper() or "1389684" in p.name or "1389707" in p.name):
        if ".git" in str(p) or "__pycache__" in str(p):
            continue
        try:
            sz = p.stat().st_size
            sha = hash_file(p) if sz < 50_000_000 else "TOO_LARGE"
            candidates.append((p, sz, sha))
        except Exception as e:
            pass

for p, sz, sha in sorted(candidates, key=lambda x: str(x[0])):
    if "PK10R1" in str(p) or "SOURCE_STATE" in str(p) or "INC29" in str(p):
        print(f"Path: {p.relative_to(ROOT)}")
        print(f"  Size: {sz} bytes | SHA256: {sha}")
