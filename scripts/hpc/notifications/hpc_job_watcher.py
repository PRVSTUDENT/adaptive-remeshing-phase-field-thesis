#!/usr/bin/env python3
"""
HPC Job Notification Watcher (Persistent Login-Node Sidecar Architecture)

Runs on the network-capable login node (mlogin01).
Can run interactively or as a detached daemon (surviving SSH logout).
Monitors PBS scheduler status via `qstat -x -w <JOB_ID>` and directory state markers,
and dispatches dual-channel (Telegram + Email) notifications from the login node.

Strict Multi-Agent Governance:
- Transport Acknowledgement (HTTP 200 / SMTP exit 0) is recorded separately from Human Delivery Observation.
- `telegram_delivery_observed` and `email_delivery_observed` remain False until explicit user-side verification.
"""

import os
import sys
import time
import json
import signal
import subprocess
import urllib.request
import urllib.parse
from datetime import datetime, timezone

PID_FILE = os.path.expanduser("~/.config/adaptive-remeshing/hpc_job_watcher.pid")
LOG_FILE = os.path.expanduser("~/.config/adaptive-remeshing/hpc_job_watcher.log")

class JobNotificationWatcher:
    def __init__(self, config_path=None):
        self.config = self.load_config(config_path)
        self.bot_token = self.config.get("TELEGRAM_BOT_TOKEN") or self.config.get("telegram_bot_token")
        self.chat_id = self.config.get("TELEGRAM_CHAT_ID") or self.config.get("telegram_chat_id")
        self.email = self.config.get("NOTIFY_EMAIL") or self.config.get("email_recipients") or "pr21vyci@mailserver.tu-freiberg.de"
        if isinstance(self.email, list):
            self.email = self.email[0]
        self.tracked_jobs = {}

    def load_config(self, config_path):
        candidates = [
            config_path,
            os.path.expanduser("~/.config/adaptive-remeshing/notifications.json"),
            os.path.expanduser("~/.config/adaptive-remeshing/notifications.env"),
            "/home/pr21vyci/.config/adaptive-remeshing/notifications.json",
            "/home/pr21vyci/.config/adaptive-remeshing/notifications.env"
        ]
        for c in candidates:
            if c and os.path.exists(c):
                if c.endswith(".json"):
                    with open(c) as f:
                        return json.load(f)
                else:
                    cfg = {}
                    with open(c) as f:
                        for l in f:
                            l = l.strip()
                            if l and not l.startswith("#") and "=" in l:
                                k, v = l.split("=", 1)
                                cfg[k.strip()] = v.strip().strip("'\"")
                    return cfg
        return {}

    def send_telegram(self, text):
        """Sends Telegram message and returns transport acknowledgement status"""
        if not self.bot_token or not self.chat_id:
            return {"transport_ack": False, "status_code": None, "error": "Missing token or chat_id"}
        url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
        data = urllib.parse.urlencode({
            "chat_id": self.chat_id,
            "text": text,
            "disable_web_page_preview": "true"
        }).encode("utf-8")
        req = urllib.request.Request(url, data=data)
        try:
            with urllib.request.urlopen(req, timeout=10) as resp:
                status_code = resp.getcode()
                res = json.loads(resp.read().decode())
                is_ok = res.get("ok", False)
                return {
                    "channel": "telegram",
                    "transport_ack": is_ok,
                    "status_code": status_code,
                    "human_delivery_observed": False  # Invariant: transport ACK != user receipt
                }
        except Exception as e:
            return {
                "channel": "telegram",
                "transport_ack": False,
                "status_code": None,
                "error": str(e),
                "human_delivery_observed": False
            }

    def send_email(self, subject, body):
        """Sends email via local mail/sendmail MTA on login node"""
        if not self.email:
            return {"transport_ack": False, "error": "Missing recipient email"}
        try:
            p = subprocess.Popen(
                ["mail", "-s", subject, self.email],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True
            )
            stdout, stderr = p.communicate(input=body, timeout=10)
            ack = (p.returncode == 0)
            return {
                "channel": "email",
                "transport_ack": ack,
                "exit_code": p.returncode,
                "recipient": self.email,
                "error": stderr.strip() if stderr else None,
                "human_delivery_observed": False  # Invariant: MTA queue != user inbox receipt
            }
        except Exception as e:
            return {
                "channel": "email",
                "transport_ack": False,
                "error": str(e),
                "human_delivery_observed": False
            }

    def notify_event(self, event_type, job_id, job_name, details=""):
        host = os.uname().nodename
        ts = datetime.now(timezone.utc).isoformat()
        msg = f"[PRV_ADAPTIVE_REMESHING - {event_type.upper()}]\nJob Name: {job_name}\nPBS Job ID: {job_id}\nHost: {host}\nTimestamp: {ts}\nDetails: {details}"
        
        t_res = self.send_telegram(msg)
        e_res = self.send_email(f"[{event_type.upper()}] {job_name} ({job_id})", msg)
        
        return {
            "event": event_type,
            "job_id": job_id,
            "telegram": t_res,
            "email": e_res
        }

    def query_pbs_job(self, pbs_job_id):
        """Queries qstat -x -w <JOB_ID> for state: Q, R, F, E, etc."""
        clean_id = pbs_job_id.split(".")[0].rstrip("*") + ".mmaster02" if "." in pbs_job_id else pbs_job_id
        try:
            out = subprocess.check_output(["qstat", "-x", "-w", clean_id], stderr=subprocess.STDOUT, universal_newlines=True, timeout=10)
            lines = out.strip().split("\n")
            if len(lines) >= 3:
                parts = lines[2].split()
                if len(parts) >= 10:
                    return parts[9]
                elif len(parts) >= 5:
                    return parts[4]
        except Exception:
            pass
        return "UNKNOWN"

    def discover_pbs_jobs(self, is_initial=False):
        """Discovers active and recently finished jobs for the current user using wide-format qstat"""
        try:
            out = subprocess.check_output(["qstat", "-u", "pr21vyci", "-x", "-w"], stderr=subprocess.STDOUT, universal_newlines=True, timeout=15)
            lines = out.strip().split("\n")
            for line in lines:
                parts = line.split()
                if len(parts) >= 10 and ("mmaster02" in parts[0] or "cluster" in parts[0] or parts[0][0].isdigit()):
                    jid = parts[0]
                    if "*" in jid:
                        jid = jid.split(".")[0].rstrip("*") + ".mmaster02"
                    jname = parts[3]
                    state = parts[9]
                    if jid not in self.tracked_jobs:
                        initial_state = state if is_initial else "DISCOVERED"
                        self.tracked_jobs[jid] = {
                            "job_name": jname,
                            "state": "COMPLETED" if (is_initial and state == "F") else ("RUNNING" if (is_initial and state == "R") else ("QUEUED" if (is_initial and state in ("Q", "H")) else "DISCOVERED")),
                            "first_seen": datetime.now(timezone.utc).isoformat()
                        }
        except Exception as e:
            print(f"[WATCHER ERROR] Error discovering PBS jobs: {e}", flush=True)

    def watch_loop(self, poll_interval=15):
        """Persistent watcher polling loop"""
        os.makedirs(os.path.dirname(PID_FILE), exist_ok=True)
        with open(PID_FILE, "w") as fp:
            fp.write(str(os.getpid()))

        print(f"[WATCHER DAEMON] Started with PID {os.getpid()} (polling interval: {poll_interval}s)...", flush=True)
        # Prime existing historical jobs so we only alert on live transitions going forward
        self.discover_pbs_jobs(is_initial=True)
        print(f"[WATCHER DAEMON] Primed {len(self.tracked_jobs)} existing jobs into tracking state.", flush=True)

        while True:
            self.discover_pbs_jobs(is_initial=False)
            for job_id, info in list(self.tracked_jobs.items()):
                if info.get("state") in ("COMPLETED", "TERMINATED"):
                    continue
                job_name = info.get("job_name", "UNKNOWN")
                prev_state = info.get("state", "UNKNOWN")
                
                current_pbs_state = self.query_pbs_job(job_id)
                
                if current_pbs_state == "R" and prev_state not in ("RUNNING", "STARTED"):
                    print(f"[WATCHER] Job {job_id} ({job_name}) entered state RUNNING. Dispatching STARTED notification...", flush=True)
                    self.notify_event("STARTED", job_id, job_name, "Job transitioned to RUNNING on compute node")
                    info["state"] = "RUNNING"

                elif current_pbs_state == "F" and prev_state not in ("COMPLETED", "TERMINATED"):
                    print(f"[WATCHER] Job {job_id} ({job_name}) entered state FINISHED. Dispatching COMPLETED notification...", flush=True)
                    self.notify_event("COMPLETED", job_id, job_name, "Job completed on cluster")
                    info["state"] = "COMPLETED"

                self.tracked_jobs[job_id] = info

            sys.stdout.flush()
            sys.stderr.flush()
            time.sleep(poll_interval)

def start_daemon():
    os.makedirs(os.path.dirname(PID_FILE), exist_ok=True)
    if os.path.exists(PID_FILE):
        try:
            with open(PID_FILE) as fp:
                old_pid = int(fp.read().strip())
            os.kill(old_pid, 0)
            print(f"[WATCHER] Daemon already running with PID {old_pid}")
            return True
        except (OSError, ValueError):
            pass

    script_path = os.path.abspath(__file__)
    cmd = f"nohup python3 {script_path} --run-loop > {LOG_FILE} 2>&1 &"
    subprocess.Popen(cmd, shell=True)
    time.sleep(1)
    status_daemon()
    return True

def stop_daemon():
    if not os.path.exists(PID_FILE):
        print("[WATCHER] No daemon PID file found (already stopped)")
        return True
    try:
        with open(PID_FILE) as fp:
            pid = int(fp.read().strip())
        os.kill(pid, signal.SIGTERM)
        print(f"[WATCHER] Stopped daemon PID {pid}")
    except Exception as e:
        print(f"[WATCHER] Error stopping PID: {e}")
    if os.path.exists(PID_FILE):
        os.remove(PID_FILE)
    return True

def status_daemon():
    if not os.path.exists(PID_FILE):
        print("[WATCHER STATUS] INACTIVE (PID file missing)")
        return False
    try:
        with open(PID_FILE) as fp:
            pid = int(fp.read().strip())
        os.kill(pid, 0)
        print(f"[WATCHER STATUS] ACTIVE (PID {pid})")
        return True
    except OSError:
        print("[WATCHER STATUS] STALE (Process not running)")
        return False

if __name__ == "__main__":
    if len(sys.argv) > 1:
        mode = sys.argv[1]
        if mode == "--start-daemon":
            start_daemon()
            sys.exit(0)
        elif mode == "--stop-daemon":
            stop_daemon()
            sys.exit(0)
        elif mode == "--status-daemon":
            is_active = status_daemon()
            sys.exit(0 if is_active else 1)
        elif mode == "--run-loop":
            watcher = JobNotificationWatcher()
            watcher.watch_loop()
            sys.exit(0)
        elif mode == "--test-telegram":
            watcher = JobNotificationWatcher()
            res = watcher.send_telegram("[PRV_ADAPTIVE_REMESHING - TELEGRAM_TEST]\nTesting persistent login sidecar Telegram transport.")
            print(json.dumps(res, indent=2))
            sys.exit(0 if res.get("transport_ack") else 1)
        elif mode == "--test-email":
            watcher = JobNotificationWatcher()
            res = watcher.send_email("[PRV_ADAPTIVE_REMESHING - EMAIL_TEST]", "Testing persistent login sidecar Email transport.")
            print(json.dumps(res, indent=2))
            sys.exit(0 if res.get("transport_ack") else 1)
        elif mode == "--test-all":
            watcher = JobNotificationWatcher()
            res = watcher.notify_event("PERSISTENT_QUAL_TEST", "LOGIN_PERSIST_TEST_004", "PERSISTENT_NOTIFICATION_QUALIFICATION", "Testing persistent login-node sidecar dispatch")
            print(json.dumps(res, indent=2))
            t_ok = res.get("telegram", {}).get("transport_ack", False)
            sys.exit(0 if t_ok else 1)
