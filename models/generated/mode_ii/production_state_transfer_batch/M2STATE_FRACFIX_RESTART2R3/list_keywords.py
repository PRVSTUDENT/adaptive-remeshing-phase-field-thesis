with open("M2STATE_FRACFIX_RESTART2R3.inp", "r") as f:
    for i, line in enumerate(f):
        if line.startswith("*") and not line.startswith("**"):
            print(f"{i+1}: {line.strip()[:80]}")
