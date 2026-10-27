from __future__ import print_function
import sys
import os

sys.path.insert(0, '/scratch9/pr21vyci/runs/mode1_candidate_donor_h0025_visual')
from extract_pkg76_checkpoint_full_state import extract_checkpoint_full_state

odb_path = '/scratch9/pr21vyci/runs/mode1_candidate_donor_h0025_visual/M1_CANDIDATE_DONOR_H0025_VISUAL.odb'
out_dir = '/scratch9/pr21vyci/runs/mode1_candidate_donor_h0025_visual/evidence_frame85'

manifest = extract_checkpoint_full_state(odb_path, out_dir, target_frame_idx=85)
print('Done. Frame 85 extracted successfully.')
