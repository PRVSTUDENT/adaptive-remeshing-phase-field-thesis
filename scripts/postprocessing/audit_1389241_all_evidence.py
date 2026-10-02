import sys
import re

def main():
    dat_path = "/home/pr21vyci/projects/adaptive-remeshing/models/generated/mode_ii/production_state_transfer_batch/M2STATE_FRACFIX_RESTART1R1R8/M2STATE_FRACFIX_RESTART1R1R8.dat"
    msg_path = "/home/pr21vyci/projects/adaptive-remeshing/models/generated/mode_ii/production_state_transfer_batch/M2STATE_FRACFIX_RESTART1R1R8/M2STATE_FRACFIX_RESTART1R1R8.msg"
    sta_path = "/home/pr21vyci/projects/adaptive-remeshing/models/generated/mode_ii/production_state_transfer_batch/M2STATE_FRACFIX_RESTART1R1R8/M2STATE_FRACFIX_RESTART1R1R8.sta"
    inp_path = "/home/pr21vyci/projects/adaptive-remeshing/models/generated/mode_ii/production_state_transfer_batch/M2STATE_FRACFIX_RESTART1R1R8/M2STATE_FRACFIX_RESTART1R1R8.inp"

    print("=== Checking INP Output Requests ===")
    with open(inp_path, 'r') as f:
        inp_lines = f.readlines()
    for i, l in enumerate(inp_lines):
        if l.strip().startswith("*OUTPUT") or l.strip().startswith("*NODE OUTPUT") or l.strip().startswith("*ELEMENT OUTPUT") or l.strip().startswith("*NODE PRINT") or l.strip().startswith("*EL PRINT"):
            print("Line %d: %s" % (i+1, l.strip()))
            for j in range(1, 4):
                if i+j < len(inp_lines):
                    print("   + %s" % inp_lines[i+j].strip())

    print("\n=== Checking DAT File Tables ===")
    with open(dat_path, 'r') as f:
        dat_text = f.read()

    # Search for all step and increment occurrences in DAT
    step_inc_matches = list(re.finditer(r'STEP\s+(\d+)\s+INCREMENT\s+(\d+)', dat_text))
    print("Found %d STEP/INCREMENT blocks in DAT" % len(step_inc_matches))
    for m in step_inc_matches:
        print("  DAT block: Step %s, Increment %s at position %d" % (m.group(1), m.group(2), m.start()))

    # Check last occurrence (Step 2 Increment 15)
    if step_inc_matches:
        last_match = step_inc_matches[-1]
        chunk = dat_text[last_match.start():last_match.start()+10000]
        print("\n--- Snippet of Last DAT block ---")
        print(chunk[:3000])

    # Check if SDV or H or SDV16 is anywhere in DAT
    print("\n--- Checking SDV in DAT ---")
    sdv_count = dat_text.count("SDV")
    print("Total occurrences of 'SDV' in DAT:", sdv_count)
    if sdv_count > 0:
        idx = dat_text.find("SDV")
        print("First SDV context in DAT:")
        print(dat_text[max(0, idx-200):idx+500])

    print("\n=== Checking STA file ===")
    with open(sta_path, 'r') as f:
        print(f.read())

if __name__ == "__main__":
    main()
