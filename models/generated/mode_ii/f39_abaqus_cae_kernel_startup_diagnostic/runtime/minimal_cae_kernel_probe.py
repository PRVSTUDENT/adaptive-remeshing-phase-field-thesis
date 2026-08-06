from __future__ import print_function
import json
import os
import sys

payload = {
    "protocol_version": 1,
    "marker": "CAE_KERNEL_STARTED",
    "python_version": sys.version,
    "working_directory": os.getcwd(),
    "executable": sys.executable
}

output_path = os.environ.get(
    "F39_KERNEL_AUDIT",
    "CAE_KERNEL_STARTUP_AUDIT.json"
)

with open(output_path, "w") as handle:
    json.dump(payload, handle, indent=2)

print("CAE_KERNEL_STARTED")
