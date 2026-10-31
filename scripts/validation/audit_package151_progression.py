import json
import glob
import os

def main():
    base = '/scratch9/pr21vyci/runs/mode1_c4_package150_c1_2_continuation_r1/continuation_1418950.mmaster02'
    mech_dirs = sorted(glob.glob(os.path.join(base, 'P150_S1_*_00_mechanical')))
    
    print(f"Found {len(mech_dirs)} mechanical solves in Step 1:")
    records = []
    for md in mech_dirs:
        rpath = os.path.join(md, 'receipt.json')
        epath = os.path.join(md, 'endpoint.json')
        if os.path.exists(rpath) and os.path.exists(epath):
            rec = json.load(open(rpath))
            ep = json.load(open(epath))
            nodes = {r[0]: (float(r[1]), float(r[2]), float(r[3])) for r in ep['nodes']}
            records.append({
                'outer': rec['outer'],
                'rf2': float(ep['rf2_kN']),
                'fracture': float(ep['fracture_kNmm']),
                'elastic': float(ep['elastic_kNmm']),
                'nodes': nodes
            })
            print(f"  Outer {rec['outer']:02d}: RF2 = {ep['rf2_kN']:.6f} kN, E_frac = {ep['fracture_kNmm']:.6e} kN-mm, E_el = {ep['elastic_kNmm']:.6e} kN-mm")
    
    for i in range(1, len(records)):
        prev = records[i-1]
        curr = records[i]
        delta_rf = curr['rf2'] - prev['rf2']
        pct_rf = (delta_rf / prev['rf2']) * 100.0
        
        du = max(((curr['nodes'][k][0] - prev['nodes'][k][0])**2 + (curr['nodes'][k][1] - prev['nodes'][k][1])**2)**0.5 for k in curr['nodes'])
        dd = max(abs(curr['nodes'][k][2] - prev['nodes'][k][2]) for k in curr['nodes'])
        print(f"Convergence Iter {prev['outer']} -> {curr['outer']}:")
        print(f"  Delta RF2 = {delta_rf:+.6f} kN ({pct_rf:+.3f}%)")
        print(f"  Delta u_max = {du:.6e} mm")
        print(f"  Delta d_max = {dd:.6e}")

if __name__ == '__main__':
    main()
