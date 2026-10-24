#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import csv
import json
import re
from pathlib import Path

def extract():
    dat_file = Path('M1_C5_PACKAGE103_H1_PILOT.dat')
    msg_file = Path('M1_C5_PACKAGE103_H1_PILOT.msg')
    sta_file = Path('M1_C5_PACKAGE103_H1_PILOT.sta')
    csv_file = Path('uel_energy_balance.csv')

    results = {'status': 'UNKNOWN', 'rf2_N': None, 'e_frac_mJ': None, 'e_elas_mJ': None}
    if csv_file.exists():
        with open(csv_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            if rows:
                last = rows[-1]
                results['e_frac_mJ'] = float(last['E_fracture_kNmm']) * 1000.0
                results['e_elas_mJ'] = float(last['E_elastic_kNmm']) * 1000.0
                results['step'] = int(last['Step'])
                results['inc'] = int(last['Increment'])

    if dat_file.exists():
        text = dat_file.read_text(encoding='utf-8', errors='ignore')
        m = re.findall(r'999999\s+[-+0-9.E]+\s+([-+0-9.E]+)', text)
        if m:
            results['rf2_N'] = float(m[-1]) * 1000.0

    with open('package103_deliverable_evaluation.json', 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2)
    print('Extracted Package 103 deliverables:', results)

if __name__ == '__main__':
    extract()
