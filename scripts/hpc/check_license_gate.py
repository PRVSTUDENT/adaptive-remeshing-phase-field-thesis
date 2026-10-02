#!/usr/bin/env python3
"""
Pre-submission FlexNet License Readiness Gate for Abaqus/Standard
Queries 25000@license4.imfd.tu-freiberg.de for 'standard' token availability.
Fails closed if server unreachable or free tokens < 5.
"""

import sys
import subprocess
import re
import json

LMUTIL_PATH = "/cluster/application/abaqus/2023/linux_a64/code/bin/lmutil"
LICENSE_SERVER = "25000@license4.imfd.tu-freiberg.de"
MIN_REQUIRED_TOKENS = 5  # Standard single-CPU Abaqus analysis requires 5 tokens

def check_license_gate():
    result = {
        "license_server_reachable": False,
        "standard_feature_found": False,
        "standard_tokens_total": 0,
        "standard_tokens_in_use": 0,
        "standard_tokens_free": 0,
        "license_ready_for_serial_standard_job": False,
        "error_message": None
    }

    try:
        proc = subprocess.Popen(
            [LMUTIL_PATH, "lmstat", "-c", LICENSE_SERVER, "-f", "standard"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True
        )
        stdout, stderr = proc.communicate(timeout=15)
        output = (stdout or "") + "\n" + (stderr or "")

        if proc.returncode == 0 and "license server UP" in output:
            result["license_server_reachable"] = True

        # Parse feature standard line
        # e.g.: Users of standard:  (Total of 300 licenses issued;  Total of 152 licenses in use)
        match = re.search(r"Users of standard:\s*\(Total of (\d+) licenses issued;\s*Total of (\d+) licenses in use\)", output)
        if match:
            total = int(match.group(1))
            in_use = int(match.group(2))
            free = total - in_use

            result["standard_feature_found"] = True
            result["standard_tokens_total"] = total
            result["standard_tokens_in_use"] = in_use
            result["standard_tokens_free"] = free

            if free >= MIN_REQUIRED_TOKENS:
                result["license_ready_for_serial_standard_job"] = True
            else:
                result["error_message"] = f"Insufficient free standard tokens ({free} free, required >= {MIN_REQUIRED_TOKENS})"
        else:
            if not result["license_server_reachable"]:
                result["error_message"] = "FlexNet license server unreachable or timed out"
            else:
                result["error_message"] = "standard feature not found in lmstat output"

    except Exception as e:
        result["error_message"] = str(e)

    return result

if __name__ == "__main__":
    gate = check_license_gate()
    print(json.dumps(gate, indent=2))
    if not gate["license_ready_for_serial_standard_job"]:
        sys.exit(1)
    sys.exit(0)
