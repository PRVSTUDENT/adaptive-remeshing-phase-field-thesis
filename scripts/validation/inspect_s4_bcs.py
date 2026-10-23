with open('models/pandey_kumar_mode1/90_r1_c3_active_set_transfer/M1_C3_PACKAGE90_R1_TRANSFER.inp', 'r', encoding='utf-8') as f:
    lines = f.readlines()

s4_idx = -1
for i, l in enumerate(lines):
    if '*Step, name=FORWARD_CONTINUATION' in l:
        s4_idx = i
        break

pkg90_bcs = {}
for l in lines[s4_idx:]:
    if l.startswith('*Output'):
        break
    parts = [p.strip() for p in l.split(',')]
    if len(parts) == 4 and parts[1] == '3' and parts[2] == '3':
        pkg90_bcs[int(parts[0])] = float(parts[3])

print(f"Package 90-R1 clamped nodes: {len(pkg90_bcs)}")

# Now test our condition on nodes and d_mapped
nodes = {}
with open('models/pandey_kumar_mode1/90_r1_c3_active_set_transfer/candidate_crack_band_mesh_c3.inp', 'r', encoding='utf-8') as f:
    reading = False
    for l in f:
        t = l.strip()
        if t.startswith('*Node'):
            reading = True
            continue
        if t.startswith('*') and reading:
            break
        if reading and t:
            parts = [p.strip() for p in t.split(',')]
            if len(parts) >= 3 and parts[0].isdigit():
                nid = int(parts[0])
                if nid != 999999:
                    nodes[nid] = (float(parts[1]), float(parts[2]))

d_mapped = {}
with open('models/pandey_kumar_mode1/90_r1_c3_active_set_transfer/candidate_c3_frame89_mapped_state_table.csv', 'r', encoding='utf-8') as f:
    for row in f:
        parts = [p.strip() for p in row.split(',')]
        if parts and parts[0] == 'NODE':
            d_mapped[int(parts[1])] = float(parts[4])

test_bcs = {}
for nid in sorted(nodes.keys()):
    pt = nodes[nid]
    d = d_mapped[nid]
    dist_y = abs(pt[1] - 0.050)
    in_band = (0.035 <= pt[0] <= 0.075) and (dist_y <= 0.008)
    if (not in_band) or (d < 0.15):
        test_bcs[nid] = d

print(f"Calculated clamped nodes: {len(test_bcs)}")
diff_keys = set(pkg90_bcs.keys()) ^ set(test_bcs.keys())
print(f"Difference in clamped node IDs: {len(diff_keys)}")

max_d_diff = 0.0
for nid in pkg90_bcs:
    diff = abs(pkg90_bcs[nid] - test_bcs[nid])
    if diff > max_d_diff:
        max_d_diff = diff
print(f"Max difference in clamped d value: {max_d_diff}")
