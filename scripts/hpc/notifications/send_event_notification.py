#!/usr/bin/env python3
import os
import sys
import json

ROOT = "/home/pr21vyci/projects/adaptive-remeshing"
sys.path.insert(0, ROOT)

from scripts.hpc.notifications.hpc_job_watcher import JobNotificationWatcher

if __name__ == "__main__":
    job_id = sys.argv[1] if len(sys.argv) > 1 else "1390098.mmaster02"
    job_name = sys.argv[2] if len(sys.argv) > 2 else "M2PK10R3_REFTIP"
    event_type = sys.argv[3] if len(sys.argv) > 3 else "SUBMITTED"
    details = sys.argv[4] if len(sys.argv) > 4 else "Repaired replacement job submitted to PBS queue entry_imfdfkmq"
    
    watcher = JobNotificationWatcher()
    res = watcher.notify_event(event_type, job_id, job_name, details)
    print(json.dumps(res, indent=2))
