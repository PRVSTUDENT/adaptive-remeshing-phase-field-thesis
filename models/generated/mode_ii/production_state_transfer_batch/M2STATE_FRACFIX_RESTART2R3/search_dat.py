with open("M2STATE_FRACFIX_RESTART2R3.dat", "r") as f:
    for i, line in enumerate(f):
        if "NODE OUTPUT" in line or "N O D E   O U T P U T" in line or "INCREMENT     1" in line:
            print(f"{i+1}: {line.strip()[:100]}")
