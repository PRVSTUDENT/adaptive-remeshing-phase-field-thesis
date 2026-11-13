#!/bin/bash
set -euo pipefail
RUN_DIR="/scratch9/pr21vyci/runs/f1728_case1_pilot"
cd "${RUN_DIR}"

echo "=== PREFLIGHT & DONOR ODB INSPECTION: TASK F1728 CASE 1 PILOT ==="
date -u +"%Y-%m-%dT%H:%M:%SZ"
hostname

# 1. Storage Capacity
AVAIL_KB=$(df -k . | awk 'NR==2 {print $4}')
echo "Scratch disk space available: $((AVAIL_KB / 1024 / 1024)) GB"

# 2. File Hashes
echo "--- Staged File Hashes ---"
sha256sum f1728_case1_mode1_edge_crack.json f42_mixed_uel.for reusable_2d_adaptive_framework.py submit_f1728_case1_pilot.pbs job_notifications.sh

# 3. Donor ODB Details
DONOR_ODB="/scratch9/pr21vyci/runs/mode1_package46_coarse_fine_preanalysis/PK_M1_COARSE_FINE_CONT.odb"
echo "--- Donor ODB Details ---"
ls -lh "${DONOR_ODB}"
sha256sum "${DONOR_ODB}"

# 4. Modules & Toolchains
echo "--- Modules & Toolchains ---"
if ! type module >/dev/null 2>&1; then source /etc/profile.d/lmod.sh; fi
module purge
module load gcc/11.4.0 intel/2024.2.0 abaqus/2023
abaqus whereami
ifort --version | sed -n '1p'

# 5. Donor ODB Step / Frame / Field Inspection via Abaqus Python
echo "--- Donor ODB Internal Structure ---"
cat << 'EOF' > inspect_donor.py
from odbAccess import openOdb
import sys

odb_path = '/scratch9/pr21vyci/runs/mode1_package46_coarse_fine_preanalysis/PK_M1_COARSE_FINE_CONT.odb'
o = openOdb(odb_path, readOnly=True)
print("ODB Title: %s" % o.description)
step_names = list(o.steps.keys())
print("Steps (%d): %s" % (len(step_names), step_names))

for name in step_names:
    st = o.steps[name]
    n_frames = len(st.frames)
    print("Step '%s': total frames = %d" % (name, n_frames))
    if n_frames > 0:
        f_last = st.frames[-1]
        print("  Last frame index: %d, time/val: %f" % (f_last.frameId, f_last.frameValue))
        field_keys = sorted(list(f_last.fieldOutputs.keys()))
        print("  Available field outputs (%d): %s" % (len(field_keys), field_keys))
        for k in ['MISESERI', 'MISESAVG', 'S', 'U', 'SDV']:
            matched = [fk for fk in field_keys if k in fk]
            if matched:
                print("  Matched '%s': %s" % (k, matched))
o.close()
print("DONOR_INSPECTION_COMPLETE")
EOF

abaqus python inspect_donor.py

# 6. Live Scheduler & Account Eligibility
echo "--- Live Scheduler / Account Eligibility ---"
qstat -u pr21vyci

echo "PREFLIGHT_SUCCESS"
