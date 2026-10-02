with open("models/generated/mode_ii/production_state_transfer_batch/M2STATE_FRACFIX_RESTART2R3/M2STATE_FRACFIX_RESTART2R3.inp", "r") as f:
    lines = f.readlines()

in_u1 = in_u2 = in_u3 = in_u4 = in_cpe4 = in_cpe3 = False
elem_nodes = set()
bot_nodes = []
top_nodes = []
in_bot = in_top = False

for line in lines:
    ls = line.strip()
    if ls.startswith("*ELEMENT"):
        in_elem = True
        in_bot = in_top = False
        continue
    elif ls.startswith("*NSET, NSET=N_BOTTOM"):
        in_bot = True
        in_elem = in_top = False
        continue
    elif ls.startswith("*NSET, NSET=N_TOP"):
        in_top = True
        in_elem = in_bot = False
        continue
    elif ls.startswith("*"):
        in_elem = in_bot = in_top = False
        continue
        
    if in_elem and ls:
        parts = [p.strip() for p in ls.split(",")]
        for p in parts[1:]:
            if p.isdigit():
                elem_nodes.add(int(p))
    elif in_bot and ls:
        for p in ls.split(","):
            if p.strip().isdigit():
                bot_nodes.append(int(p.strip()))
    elif in_top and ls:
        for p in ls.split(","):
            if p.strip().isdigit():
                top_nodes.append(int(p.strip()))

print(f"Total element nodes: {len(elem_nodes)}")
print(f"Bottom nodes count: {len(bot_nodes)}, in element nodes: {all(n in elem_nodes for n in bot_nodes)}")
print(f"Top nodes count: {len(top_nodes)}, in element nodes: {all(n in elem_nodes for n in top_nodes)}")
top_not_in_elem = [n for n in top_nodes if n not in elem_nodes]
print(f"Top nodes not in element nodes: {len(top_not_in_elem)}")
