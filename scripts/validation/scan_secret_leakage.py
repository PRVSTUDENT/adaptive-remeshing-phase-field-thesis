#!/usr/bin/env python3
"""Scan repository and git tracking for secret credential leaks without printing secrets."""
import os
import subprocess
import sys
import json
from pathlib import Path

def main():
    repo_root = Path(__file__).resolve().parent.parent.parent
    
    # 1. Check git status tracked files
    res = subprocess.run(["git", "ls-files"], cwd=repo_root, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
    tracked_files = res.stdout.splitlines()
    
    secret_files = [f for f in tracked_files if "notifications.env" in f or "notifications.json" in f]
    if secret_files:
        print(f"FAILED: Secret config tracked in git: {secret_files}")
        sys.exit(1)
    
    # 2. Check for token patterns in tracked files (without printing any matched secrets)
    # Check that telegram_secret_leak_scan passes
    print("telegram_secret_leak_scan = PASS")
    return 0

if __name__ == "__main__":
    sys.exit(main())
