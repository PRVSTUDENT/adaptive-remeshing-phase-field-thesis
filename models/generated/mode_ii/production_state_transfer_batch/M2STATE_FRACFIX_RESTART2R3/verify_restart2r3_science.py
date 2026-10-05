import sys, os, re, json

def verify_inp_abi(inp_path):
    if not os.path.exists(inp_path):
        return False, "Input deck not found"
    text = open(inp_path).read()
    
    # Verify U1 active DOF is 3
    if "*USER ELEMENT, TYPE=U1" in text:
        idx = text.find("*USER ELEMENT, TYPE=U1")
        chunk = text[idx:idx+200]
        lines = chunk.splitlines()
        if len(lines) >= 2 and lines[1].strip() != "3":
            return False, f"U1 active DOFs in deck are '{lines[1].strip()}' instead of '3'"
            
    # Verify U3 active DOF is 3
    if "*USER ELEMENT, TYPE=U3" in text:
        idx = text.find("*USER ELEMENT, TYPE=U3")
        chunk = text[idx:idx+200]
        lines = chunk.splitlines()
        if len(lines) >= 2 and lines[1].strip() != "3":
            return False, f"U3 active DOFs in deck are '{lines[1].strip()}' instead of '3'"

    # Verify U2 active DOFs are 1, 2
    if "*USER ELEMENT, TYPE=U2" in text:
        idx = text.find("*USER ELEMENT, TYPE=U2")
        chunk = text[idx:idx+200]
        lines = chunk.splitlines()
        if len(lines) >= 2 and lines[1].strip() != "1, 2":
            return False, f"U2 active DOFs in deck are '{lines[1].strip()}' instead of '1, 2'"

    return True, "INP ABI PASS"

def main():
    run_dir = os.getcwd()
    inp_path = os.path.join(run_dir, "M2STATE_FRACFIX_RESTART2R3.inp")
    if not os.path.exists(inp_path):
        inp_path = os.path.join(run_dir, "M2STATE_FRACFIX_RESTART2R2.inp")
    if not os.path.exists(inp_path):
        inp_path = os.path.join(run_dir, "M2STATE_FRACFIX_RESTART2R1.inp")

    abi_pass, abi_msg = verify_inp_abi(inp_path)
    if not abi_pass:
        print(f"Scientific verification result: FAIL ({abi_msg})")
        sys.exit(1)

    all_text = ""
    for fname in ["M2STATE_FRACFIX_RESTART2R3.msg", "M2STATE_FRACFIX_RESTART2R3.dat", "M2STATE_FRACFIX_RESTART2R3.o1389063",
                  "M2STATE_FRACFIX_RESTART2R2.msg", "M2STATE_FRACFIX_RESTART2R2.dat", "M2STATE_FRACFIX_RESTART2R2.o1389063",
                  "M2STATE_FRACFIX_RESTART2R1.msg", "M2STATE_FRACFIX_RESTART2R1.dat", "M2STATE_FRACFIX_RESTART2R1.o1388961"]:
        fp = os.path.join(run_dir, fname)
        if os.path.exists(fp):
            all_text += open(fp).read()

    state_traces = re.findall(r'\[STATE_TRACE\].*', all_text)
    if state_traces:
        for line in state_traces:
            if "NaN" in line or "Inf" in line:
                print(f"Scientific verification result: FAIL (Non-finite trace line: {line.strip()})")
                sys.exit(1)

    print("Scientific verification result: PASS")

if __name__ == '__main__':
    main()
