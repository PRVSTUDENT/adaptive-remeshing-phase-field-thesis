import os
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent

def search_session_logs():
    print("=== SEARCHING SESSIONS AND PROJECT COORDINATION ===")
    sessions_dir = ROOT / "project_coordination/sessions"
    for p in sorted(sessions_dir.glob("*.md")):
        txt = p.read_text(encoding="utf-8", errors="ignore")
        matches = []
        for pat in ["0.29483", "0.29957", "0.8593", "0.8557", "0.29", "0.85", "529.01", "639.80", "1389351", "1389352", "1389684", "1389707", "1389719", "1389721", "M2CORR_H1", "M2CORR_H2"]:
            if pat in txt:
                matches.append(pat)
        if matches:
            print(f"[{p.name}] matches: {set(matches)}")
            for pat in ["0.29483", "0.29957", "0.8593", "0.8557", "1389351", "1389352", "529.01", "639.80"]:
                if pat in txt:
                    for line in txt.splitlines():
                        if pat in line:
                            print(f"    {line.strip()[:120]}")

if __name__ == "__main__":
    search_session_logs()
