#!/usr/bin/env python3
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
p = ROOT / "models/generated/mode_ii/reference_convergence/M2REF_BATCH_MANIFEST.json"

if p.is_file():
    text = p.read_text(encoding="utf-8-sig")
    data = json.loads(text)
    p.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    print("Cleaned UTF-8 BOM from M2REF_BATCH_MANIFEST.json")
