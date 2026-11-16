# -*- coding: utf-8 -*-
"""
scripts/remeshing/clean_f1816_summary_paths.py
==============================================
Normalizes all absolute Windows paths in step2_envelope_summary.json to repo-relative forward-slash paths.
"""
import os
import json

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

def clean_dict(d):
    if isinstance(d, dict):
        new_d = {}
        for k, v in d.items():
            new_d[k] = clean_dict(v)
        return new_d
    elif isinstance(d, list):
        return [clean_dict(v) for v in d]
    elif isinstance(d, str):
        if d.startswith("D:\\Master thesis\\Adaptive remeshing\\"):
            rel = d.replace("D:\\Master thesis\\Adaptive remeshing\\", "")
            return rel.replace("\\", "/")
        return d
    else:
        return d

def main():
    json_path = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "263_f1816_multistep_narrowing", "step2_envelope", "step2_envelope_summary.json")
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    cleaned = clean_dict(data)
    
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(cleaned, f, indent=2)
    
    print("Cleaned step2_envelope_summary.json successfully.")

if __name__ == "__main__":
    main()
