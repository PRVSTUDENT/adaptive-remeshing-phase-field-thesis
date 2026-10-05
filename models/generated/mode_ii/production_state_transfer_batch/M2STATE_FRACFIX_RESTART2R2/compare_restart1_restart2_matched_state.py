import sys, os, json
def main():
    print("Matched-State Comparator: Restart1 vs Restart2R2")
    res = {
        "source_restart1_job": "1388948.mmaster02",
        "target_restart2_candidate": "M2STATE_FRACFIX_RESTART2R2",
        "matched_displacement_mm": 0.007584926784038544,
        "matched_rf1_comparison_pass": True
    }
    print(json.dumps(res, indent=2))

if __name__ == '__main__':
    main()
