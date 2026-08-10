#!/usr/bin/env python
import sys
import os
import json

sys.path.insert(0, ".")
from scripts.validation.audit_pointwise_irreversibility import audit_odb_pointwise

if __name__ == "__main__":
    odb_path = sys.argv[1] if len(sys.argv) > 1 else "models/generated/mode_ii/verification_batch/M2REF_ONEEL_FRACFIX_VERIFY_R2/M2REF_ONEEL_FRACFIX_VERIFY_R2.odb"
    res = audit_odb_pointwise(odb_path, "Job 1386364 (ONEEL R2)")
    out_json = "models/generated/mode_ii/verification_batch/M2REF_ONEEL_FRACFIX_VERIFY_R2/evidence/1386364.mmaster02/ONEEL_R2_POINTWISE_AUDIT.json"
    with open(out_json, "w") as f:
        json.dump(res, f, indent=2)
    print(json.dumps(res, indent=2))
