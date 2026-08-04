#!/usr/bin/env python3
import os
import json
import sys
import re

def main():
    inp_path = sys.argv[1] if len(sys.argv) > 1 else 'M2RMPROV1.inp'
    out_audit_path = sys.argv[2] if len(sys.argv) > 2 else 'GENERATED_INPUT_AUDIT.json'
    
    if not os.path.exists(inp_path):
        print('GENERATED INPUT ERROR: File not found: %s' % inp_path)
        return 1
        
    with open(inp_path, 'r') as f:
        text = f.read()
        
    failures = []
    
    if not re.search(r'\*Instance,\s*name=Part-1-1', text, re.IGNORECASE):
        failures.append('missing *Instance, name=Part-1-1')
        
    if not re.search(r'\*Nset,\s*nset=bottom', text, re.IGNORECASE):
        failures.append('missing *Nset, nset=bottom')
        
    if not re.search(r'\*Nset,\s*nset=top', text, re.IGNORECASE):
        failures.append('missing *Nset, nset=top')

    if not re.search(r'\*Nset,\s*nset=RP', text, re.IGNORECASE):
        failures.append('missing *Nset, nset=RP')

    if not re.search(r'\*Elset,\s*elset=All_elem', text, re.IGNORECASE):
        failures.append('missing *Elset, elset=All_elem')

    if not re.search(r'\*Equation', text, re.IGNORECASE):
        failures.append('missing *Equation')

    if not re.search(r'\*Boundary', text, re.IGNORECASE):
        failures.append('missing *Boundary')

    if not re.search(r'MISESERI', text, re.IGNORECASE):
        failures.append('missing MISESERI in element output')

    if not re.search(r'\*Element Output.*elset=All_elem', text, re.IGNORECASE):
        failures.append('missing *Element Output, elset=All_elem')

    pass_contract = (len(failures) == 0)
    
    audit = {
        'protocol_version': 1,
        'task_id': 'F29-INVALIDATE-F28-AND-PREPARE-TOPOLOGY-SAFE-CAE-BUILD',
        'generated_input_path': inp_path,
        'verified_keywords': [
            '*Instance, name=Part-1-1',
            '*Nset, nset=bottom',
            '*Nset, nset=top',
            '*Nset, nset=RP',
            '*Elset, elset=All_elem',
            '*Equation',
            '*Boundary',
            '*Element Output, elset=All_elem (MISESERI)'
        ],
        'failures': failures,
        'contract_pass': pass_contract
    }
    
    with open(out_audit_path, 'w') as h:
        json.dump(audit, h, indent=2)
        
    if pass_contract:
        print('Generated input deck M2RMPROV1.inp successfully verified.')
        return 0
    else:
        print('GENERATED INPUT ERROR: Verification failed: %s' % str(failures))
        return 1

if __name__ == '__main__':
    sys.exit(main())
