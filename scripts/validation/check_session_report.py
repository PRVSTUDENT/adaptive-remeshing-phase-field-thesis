import sys

report = "project_coordination/sessions/2026-10-29_gemini-antigravity_F1597_9e1fca8a-b36e-41df-8548-e49d81c1fe00.md"
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
