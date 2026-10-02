import os
import sys
import subprocess

def main():
    key = os.path.expanduser("~/.ssh/tu_freiberg_codex")
    remote_host = "pr21vyci@mlogin01.hrz.tu-freiberg.de"
    remote_dir = "/home/pr21vyci/projects/adaptive-remeshing/models/generated/mode_ii/production_state_transfer_batch/M2STATE_FRACFIX_RESTART2R1"

    remote_python_code = """
import os, re, json

msg = open('M2STATE_FRACFIX_RESTART2R1.msg').read() if os.path.exists('M2STATE_FRACFIX_RESTART2R1.msg') else ''
dat = open('M2STATE_FRACFIX_RESTART2R1.dat').read() if os.path.exists('M2STATE_FRACFIX_RESTART2R1.dat') else ''
log = open('M2STATE_FRACFIX_RESTART2R1.o1388961').read() if os.path.exists('M2STATE_FRACFIX_RESTART2R1.o1388961') else ''

all_text = msg + dat + log

state_traces = re.findall(r'\\[STATE_TRACE\\].*', all_text)
force_traces = re.findall(r'\\[FORCE_TRACE\\].*', all_text)
startup_traces = re.findall(r'\\[H_STARTUP_TRACE\\].*', all_text)

nan_count = sum(1 for line in state_traces if 'NaN' in line)
finite_count = sum(1 for line in state_traces if 'NaN' not in line)

jtype_counts = {}
for line in state_traces:
    m = re.search(r'JTYPE=\\s*(\\d+)', line)
    if m:
        jt = int(m.group(1))
        jtype_counts[jt] = jtype_counts.get(jt, 0) + 1

print("TOTAL_STATE_TRACE_LINES:", len(state_traces))
print("NAN_STATE_TRACE_LINES:", nan_count)
print("FINITE_STATE_TRACE_LINES:", finite_count)
print("JTYPE_BREAKDOWN:", json.dumps(jtype_counts))
print("FORCE_TRACE_LINES:", len(force_traces))
print("H_STARTUP_TRACE_LINES:", len(startup_traces))

print("\\nDISTINCT STATE TRACE LINES:")
seen = set()
for line in state_traces:
    if line not in seen:
        print(line)
        seen.add(line)
"""

    cmd = [
        "ssh", "-i", key,
        "-o", "BatchMode=yes",
        "-o", "StrictHostKeyChecking=no",
        remote_host,
        f"cd {remote_dir} && python3 -c \"{remote_python_code}\""
    ]
    res = subprocess.run(cmd, capture_output=True, text=True)
    print(res.stdout)
    if res.stderr:
        print("STDERR:", res.stderr)

if __name__ == '__main__':
    main()
