with open("M2STATE_FRACFIX_RESTART2R3.msg", "r") as f:
    count = 0
    for i, line in enumerate(f):
        if any(w in line for w in ["***WARNING", "PIVOT", "SINGULAR", "NaN", "Error", "CONVERGENCE"]):
            print(f"{i+1}: {line.strip()}")
            count += 1
            if count > 50:
                break
