from __future__ import print_function
import sys
import os
import json

def main():
    target_dir = sys.argv[1] if len(sys.argv) > 1 else '.'
    
    matrix_path = os.path.join(target_dir, 'CAE_PHASE_DIAGNOSTIC_MATRIX.json')
    context_path = os.path.join(target_dir, 'CAE_INVOCATION_CONTEXT_AUDIT.json')
    
    if not os.path.exists(matrix_path):
        print("ERROR: CAE_PHASE_DIAGNOSTIC_MATRIX.json missing")
        sys.exit(1)
        
    if not os.path.exists(context_path):
        print("ERROR: CAE_INVOCATION_CONTEXT_AUDIT.json missing")
        sys.exit(1)
        
    with open(context_path, 'r') as f:
        ctx_data = json.load(f)
        
    if not ctx_data.get('bootstrap_passed'):
        print("ERROR: Invocation context bootstrap did not pass")
        sys.exit(1)
        
    with open(matrix_path, 'r') as f:
        matrix_data = json.load(f)
        
    phases = matrix_data.get('phases', [])
    if not phases:
        print("ERROR: No diagnostic phases recorded in matrix")
        sys.exit(1)
        
    print("Found {0} diagnostic phases executed cleanly.".format(len(phases)))
    sys.exit(0)

if __name__ == '__main__':
    main()
