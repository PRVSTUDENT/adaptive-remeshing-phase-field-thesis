with open("M2STATE_FRACFIX_RESTART2R3.msg", "r") as f:
    for i, line in enumerate(f):
        if "ITERATION" in line or "EQUILIBRIUM" in line or "RESIDUAL" in line or "CORRECTION" in line or "AVERAGE FORCE" in line:
            print(f"{i+1}: {line.strip()[:100]}")
