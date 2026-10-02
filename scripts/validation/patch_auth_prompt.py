import os

target_path = r"C:\Users\pruth\OpenClawPAD\Antigravity-Autonomous-Loop.ps1"

with open(target_path, "r", encoding="utf-8", newline="") as f:
    content = f.read()

has_crlf = "\r\n" in content
content = content.replace("\r\n", "\n")

old_line = "6. Do not independently decide HPC authorization, job-monitoring counts, or workflow termination. Those are handled by the deterministic controller."
new_line = "6. If the human (user) has authorized today's tasks and jobs, you can decide and authorize the jobs of this project within that authorized scope."

assert old_line in content, "old_line not found in content"
content = content.replace(old_line, new_line, 1)

if has_crlf:
    content = content.replace("\n", "\r\n")

with open(target_path, "w", encoding="utf-8", newline="") as f:
    f.write(content)

print(f"Successfully updated authorization directive in {target_path}")
