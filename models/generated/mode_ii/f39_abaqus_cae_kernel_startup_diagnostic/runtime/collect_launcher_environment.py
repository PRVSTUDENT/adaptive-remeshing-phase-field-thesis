#!/usr/bin/env python3
import json
import os
import re
import socket
import subprocess
import sys
import datetime

REDACT_KEYWORDS = re.compile(
    r"(token|password|passwd|pass|secret|key|cookie|auth|credential|connection|string)",
    re.IGNORECASE
)

WHITELISTED_VARS = {"USER", "LOGNAME", "MAIL", "USERNAME"}

def run_cmd(cmd):
    try:
        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            shell=True,
            universal_newlines=True
        )
        out, _ = proc.communicate(timeout=30)
        return proc.returncode, out.strip()
    except Exception as exc:
        return -1, str(exc)

def sanitize_env(env_dict):
    sanitized = {}
    for k, v in env_dict.items():
        if k in WHITELISTED_VARS:
            sanitized[k] = v
        elif REDACT_KEYWORDS.search(k):
            sanitized[k] = "[REDACTED]"
        else:
            sanitized[k] = v
    return sanitized

def main():
    work_dir = os.getcwd()
    evidence_dir = os.environ.get("F39_EVIDENCE_DIR", os.path.join(work_dir, "evidence"))
    os.makedirs(evidence_dir, exist_ok=True)

    hostname = socket.gethostname()
    timestamp = datetime.datetime.utcnow().isoformat() + "Z"

    rc_mod, out_mod = run_cmd("module list 2>&1")
    with open(os.path.join(evidence_dir, "module_list.txt"), "w") as f:
        f.write(out_mod + "\n")

    rc_rel, out_rel = run_cmd("abaqus information=release 2>&1")
    with open(os.path.join(evidence_dir, "abaqus_information_release.txt"), "w") as f:
        f.write(out_rel + "\n")

    rc_sys, out_sys = run_cmd("abaqus information=system 2>&1")
    with open(os.path.join(evidence_dir, "abaqus_information_system.txt"), "w") as f:
        f.write(out_sys + "\n")

    rc_which, out_which = run_cmd("command -v abaqus 2>&1")
    rc_type, out_type = run_cmd("type -a abaqus 2>&1")
    rc_readlink, out_readlink = run_cmd("readlink -f \"$(command -v abaqus)\" 2>&1")

    with open(os.path.join(evidence_dir, "resolved_abaqus_launcher.txt"), "w") as f:
        f.write("command -v abaqus:\n" + out_which + "\n\n")
        f.write("type -a abaqus:\n" + out_type + "\n\n")
        f.write("readlink -f abaqus:\n" + out_readlink + "\n")

    abaqus_vars = {k: v for k, v in os.environ.items() if "ABAQUS" in k.upper() or "SIMULIA" in k.upper()}

    installation_checks = {}
    candidate_paths = [
        "/var/DassaultSystemes",
        "/usr/DassaultSystemes",
        "/opt/DassaultSystemes",
        "/scratch/pr21vyci",
        out_readlink if rc_readlink == 0 else ""
    ]
    for p in candidate_paths:
        if p:
            installation_checks[p] = os.path.exists(p)

    sanitized_env = sanitize_env(dict(os.environ))

    audit_data = {
        "protocol_version": 1,
        "timestamp": timestamp,
        "hostname": hostname,
        "python_version": sys.version,
        "command_v_abaqus": out_which,
        "type_a_abaqus": out_type,
        "resolved_abaqus_launcher": out_readlink,
        "module_list": out_mod,
        "abaqus_information_release": out_rel,
        "abaqus_information_system": out_sys,
        "path": sanitized_env.get("PATH", ""),
        "ld_library_path": sanitized_env.get("LD_LIBRARY_PATH", ""),
        "abaqus_environment_variables": sanitize_env(abaqus_vars),
        "installation_checks": installation_checks,
        "sanitized_environment": sanitized_env
    }

    audit_path = os.environ.get(
        "F39_LAUNCHER_AUDIT",
        "ABAQUS_LAUNCHER_ENVIRONMENT_AUDIT.json"
    )
    with open(audit_path, "w") as f:
        json.dump(audit_data, f, indent=2)

    # Copy to evidence directory as well
    evidence_audit_path = os.path.join(evidence_dir, "ABAQUS_LAUNCHER_ENVIRONMENT_AUDIT.json")
    with open(evidence_audit_path, "w") as f:
        json.dump(audit_data, f, indent=2)

    print("ABAQUS_LAUNCHER_ENVIRONMENT_COLLECTED")
    return 0

if __name__ == "__main__":
    sys.exit(main())
