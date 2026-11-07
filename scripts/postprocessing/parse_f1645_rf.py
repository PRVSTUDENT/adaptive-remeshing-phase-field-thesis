import csv

with open('results/validation/f1645_prop_PK_HOLE_METHOD_A_PROP.dat', 'r') as f:
    lines = f.readlines()

records = []
inc = 1
for line in lines:
    parts = line.strip().split()
    if len(parts) == 3 and parts[0] == '999999':
        try:
            u2 = float(parts[1])
            rf2 = float(parts[2])
            records.append({'increment': inc, 'u2_mm': u2, 'rf2_kN': rf2})
            inc += 1
        except ValueError:
            pass

with open('results/validation/f1645_prop_rf_displacement.csv', 'w', newline='') as f:
    writer = csv.DictWriter(f, fieldnames=['increment', 'u2_mm', 'rf2_kN'])
    writer.writeheader()
    for r in records:
        writer.writerow(r)

print('Parsed %d RF-displacement records.' % len(records))
if records:
    max_rf = max(records, key=lambda x: x['rf2_kN'])
    print('Max RF: %s' % str(max_rf))
