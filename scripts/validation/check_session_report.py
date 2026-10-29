import sys

report = "project_coordination/sessions/2026-10-29_gemini-antigravity_F1597_61fb15aa-8392-4910-b4e6-65d6bdc0fc7a.md"
lines = open(report, "r", encoding="utf-8").readlines()
bad = [i+1 for i, l in enumerate(lines) if l.rstrip("\r\n") != l.rstrip()]
print("Trailing whitespace lines count:", len(bad))
if bad:
    print("Lines with trailing whitespace:", bad)
    # Strip them
    fixed = [l.rstrip() + "\n" for l in lines]
    open(report, "w", encoding="utf-8").writelines(fixed)
    print("Fixed trailing whitespace!")
else:
    print("Zero trailing whitespace verified!")
