import sys, os, json
from odbAccess import openOdb

def main():
    odb_path = sys.argv[1] if len(sys.argv) > 1 else 'M2STATE_FRACFIX_RESTART2R1.odb'
    out_json = sys.argv[2] if len(sys.argv) > 2 else 'extracted_restart2r1_odb.json'
    if not os.path.exists(odb_path):
        print("ODB not found:", odb_path)
        sys.exit(1)
    odb = openOdb(odb_path, readOnly=True)
    res = {"job_id": "M2STATE_FRACFIX_RESTART2R1", "steps": {}}
    for s_name in odb.steps.keys():
        s = odb.steps[s_name]
        res["steps"][s_name] = {"frame_count": len(s.frames)}
    with open(out_json, "w") as f:
        json.dump(res, f, indent=2)
    print("Saved extracted ODB summary to", out_json)

if __name__ == '__main__':
    main()
