#!/usr/bin/env python3
"""
Terminal state monitoring and mandatory notification dispatch for Stage F40 M2RMBISECT1.
"""
import sys
import os
import json
import time
import subprocess
from datetime import datetime, timezone

def parse_qstat_f(output_text):
    data = {}
    current_key = None
    for line in output_text.splitlines():
        sline = line.strip()
        if not sline:
            continue
        if "=" in sline:
            parts = sline.split("=", 1)
            k = parts[0].strip()
            v = parts[1].strip()
            data[k] = v
            current_key = k
        elif current_key:
            data[current_key] += sline
    return data

def main():
    job_id = sys.argv[1] if len(sys.argv) > 1 else ""
    if not job_id:
        last_job_file = "runs/hpc/stage_f/f40_f38_cae_invocation_model_building_bisect/LAST_JOB_ID.txt"
        if os.path.exists(last_job_file):
            with open(last_job_file, "r") as f:
                job_id = f.read().strip()

    if not job_id:
        print("ERROR: Job ID must be supplied or present in LAST_JOB_ID.txt", file=sys.stderr)
        sys.exit(1)

    evidence_dir = "runs/hpc/stage_f/f40_f38_cae_invocation_model_building_bisect/evidence/{}".format(job_id)
    os.makedirs(evidence_dir, exist_ok=True)
    notification_dispatcher = "scripts/hpc/notify_hpc_event.py"

    print("INFO: Monitoring terminal state for Job ID: {}...".format(job_id))
    started_utc = datetime.now(timezone.utc).isoformat()

    max_polls = 360  # 30 mins bounded timeout (360 * 5s)
    poll_interval = 5
    last_rc = -1
    last_state = "UNKNOWN"
    terminal_confirmed = False
    parsed_info = {}

    for poll_idx in range(max_polls):
        proc = subprocess.run(["qstat", "-x", "-f", job_id], stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
        if proc.returncode != 0:
            # Fallback to qstat -f
            proc = subprocess.run(["qstat", "-f", job_id], stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)

        last_rc = proc.returncode
        if proc.returncode != 0:
            print("WARNING: qstat query returned exit code {} at poll {}/{} ({})".format(proc.returncode, poll_idx+1, max_polls, proc.stderr.strip()), file=sys.stderr)
            time.sleep(poll_interval)
            continue

        parsed_info = parse_qstat_f(proc.stdout)
        last_state = parsed_info.get("job_state", "UNKNOWN")

        if last_state in ["F", "C"] and "Exit_status" in parsed_info:
            terminal_confirmed = True
            print("INFO: Job {} reached confirmed terminal state '{}'".format(job_id, last_state))
            break

        time.sleep(poll_interval)

    finished_utc = datetime.now(timezone.utc).isoformat()

    exit_status = parsed_info.get("Exit_status")
    exec_host = parsed_info.get("exec_host", "unknown")
    walltime = parsed_info.get("resources_used.walltime", "unknown")
    classification = "unknown"

    status_json = os.path.join(evidence_dir, "STATUS.json")
    if os.path.exists(status_json):
        try:
            with open(status_json, "r") as f:
                s_data = json.load(f)
                classification = s_data.get("overall_classification", classification)
                if exit_status is None and "exit_status" in s_data and s_data["exit_status"] is not None:
                    exit_status = str(s_data["exit_status"])
        except Exception:
            pass

    if exit_status is None:
        exit_status = "unknown"

    monitor_status = {
        "job_id": job_id,
        "scheduler_query_returncode": last_rc,
        "last_observed_state": last_state,
        "terminal_state_confirmed": terminal_confirmed,
        "exit_status": exit_status,
        "exec_host": exec_host,
        "walltime": walltime,
        "monitoring_started_utc": started_utc,
        "monitoring_finished_utc": finished_utc
    }

    with open(os.path.join(evidence_dir, "TERMINAL_MONITOR_STATUS.json"), "w") as f:
        json.dump(monitor_status, f, indent=2)

    if terminal_confirmed:
        if os.path.exists(notification_dispatcher):
            print("INFO: Dispatching terminal state notifications...")
            subprocess.run([
                sys.executable, notification_dispatcher,
                "--mode", "terminal",
                "--job-name", "M2RMBISECT1",
                "--job-id", job_id,
                "--exit-status", str(exit_status),
                "--host", exec_host,
                "--walltime", walltime,
                "--classification", classification,
                "--evidence-path", evidence_dir,
                "--audit-file", os.path.join(evidence_dir, "POST_TERMINAL_NOTIFICATION_AUDIT.json"),
                "--returncode-dir", evidence_dir
            ])
        print("SUCCESS: Terminal monitoring and notification closeout complete for {}.".format(job_id))
        sys.exit(0)
    else:
        print("ERROR: Terminal monitoring timed out or failed to confirm terminal state for {}.".format(job_id), file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
