#!/usr/bin/env python3
"""
Audit and summary of all Gate-6 jobs (1403347, 1403357, 1403358, 1403359, 1403360, 1403361).
"""

import hashlib
import os

dirs = [
    ('1403347', 'PK_M1_C8_5PCT', '22_gate6_adaptive_cpe4_5pct', 'PK_MODE1_C8_5PCT_PFM.inp', 'serial (1 CPU)'),
    ('1403357', 'PK_M1_C7_2PCT', '21_gate6_adaptive_cpe4_2pct', 'PK_MODE1_C7_2PCT_PFM.inp', 'serial (1 CPU)'),
    ('1403358', 'PK_M1_C7_2PCT_TH4', '23_gate6_adaptive_cpe4_2pct_th4', 'PK_MODE1_C7_2PCT_PFM.inp', '1 rank x 4 threads'),
    ('1403359', 'PK_M1_C8_5PCT_TH4', '24_gate6_adaptive_cpe4_5pct_th4', 'PK_MODE1_C8_5PCT_PFM.inp', '1 rank x 4 threads'),
    ('1403360', 'PK_M1_C9_3PCT', '25_gate6_adaptive_cpe4_3pct', 'PK_MODE1_C9_3PCT_PFM.inp', 'serial (1 CPU)'),
    ('1403361', 'PK_M1_C9_3PCT_TH4', '26_gate6_adaptive_cpe4_3pct_th4', 'PK_MODE1_C9_3PCT_PFM.inp', '1 rank x 4 threads')
]

for job_id, job_name, dname, inp_name, mode in dirs:
    base = f'/home/pr21vyci/projects/adaptive-remeshing/models/pandey_kumar_mode1/{dname}'
    inp_path = f'{base}/{inp_name}'
    for_path = f'{base}/f42_mixed_uel.for'
    
    inp_hash = hashlib.sha256(open(inp_path, 'rb').read()).hexdigest() if os.path.exists(inp_path) else 'N/A'
    for_hash = hashlib.sha256(open(for_path, 'rb').read()).hexdigest() if os.path.exists(for_path) else 'N/A'
    
    # count elements and nodes from inp
    elems = 0
    nodes = 0
    in_elem = False
    in_node = False
    if os.path.exists(inp_path):
        with open(inp_path) as f:
            for line in f:
                l = line.strip().upper()
                if l.startswith('*ELEMENT'):
                    in_elem = True
                    in_node = False
                elif l.startswith('*NODE'):
                    in_node = True
                    in_elem = False
                elif l.startswith('*'):
                    in_elem = False
                    in_node = False
                elif in_elem and line.strip():
                    elems += 1
                elif in_node and line.strip():
                    nodes += 1
                    
    print(f'Job {job_id} | Name: {job_name:18} | Dir: {dname:30} | Mode: {mode:18} | Elements: {elems:6} | Nodes: {nodes:6} | INP: {inp_hash[:16]}... | FOR: {for_hash[:16]}...')
