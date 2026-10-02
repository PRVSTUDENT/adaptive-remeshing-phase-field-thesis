import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent

def inspect_runs_evidence():
    print("=== INSPECTING RUNS / EVIDENCE FOR REFERENCE VALUES ===")
    for p in ROOT.rglob("*.json"):
        if "runs" in str(p) or "models" in str(p):
            try:
                txt = p.read_text(encoding="utf-8", errors="ignore")
                if any(k in txt for k in ["0.29483", "0.29957", "0.859", "0.855", "529.01", "639.80", "533.42", "peak_force", "peak_rf1"]):
                    print(f"\n--- MATCH IN {p.relative_to(ROOT)} ---")
                    try:
                        data = json.loads(txt)
                        # print keys or summary
                        if isinstance(data, dict):
                            for k, v in list(data.items())[:15]:
                                print(f"  {k}: {str(v)[:100]}")
                        elif isinstance(data, list):
                            print(f"  List of {len(data)} items; item 0: {str(data[0])[:100]}")
                    except Exception:
                        for line in txt.splitlines()[:10]:
                            print(f"  {line[:120]}")
            except Exception:
                pass

if __name__ == "__main__":
    inspect_runs_evidence()
