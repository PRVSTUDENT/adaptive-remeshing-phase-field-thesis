#!/usr/bin/env python3
import os
import json
import sys

def main():
    target_dir = sys.argv[1] if len(sys.argv) > 1 else '.'
    
    req_files = [
        'compatibility.returncode',
        'cae_builder.returncode',
        'collector.returncode',
        'first_failure.returncode',
        'SOURCE_ENTITY_SPEC.json',
        'SOURCE_REGION_MAP.json',
        'SOURCE_OUTPUT_CONTRACT.json',
        'SOURCE_SLIT_TOPOLOGY_CONTRACT.json',
        'SOURCE_MODEL_INVENTORY.json',
        'INSTANCE_REPLACEMENT_API_AUDIT.json',
        'MODEL_ENTITY_REBINDING_AUDIT.json',
        'SLIT_GEOMETRY_AUDIT.json',
        'SLIT_MESH_TOPOLOGY_AUDIT.json',
        'GEOMETRY_BACKED_MODEL_AUDIT.json',
        'GENERATED_INPUT_AUDIT.json',
        'M2RMPROV1_GENERATED_INPUT.sha256',
        'EXECUTION_COUNTERS.json',
        'STATUS.json',
        'NOTIFICATION_START_TELEGRAM.json',
        'NOTIFICATION_TERMINAL_TELEGRAM.json',
        'NOTIFICATION_REDACTION_AUDIT.json'
    ]
    
    missing = [f for f in req_files if not os.path.exists(os.path.join(target_dir, f))]
    
    report = {
        'protocol_version': 1,
        'task_id': 'F29-INVALIDATE-F28-AND-PREPARE-TOPOLOGY-SAFE-CAE-BUILD',
        'target_directory': target_dir,
        'missing_file_count': len(missing),
        'missing_files': missing
    }
    
    out_file = os.path.join(target_dir, 'MISSING_EVIDENCE_REPORT.json')
    with open(out_file, 'w') as h:
        json.dump(report, h, indent=2)
        
    print('Generated MISSING_EVIDENCE_REPORT.json with %d missing files.' % len(missing))
    return 0

if __name__ == '__main__':
    sys.exit(main())
