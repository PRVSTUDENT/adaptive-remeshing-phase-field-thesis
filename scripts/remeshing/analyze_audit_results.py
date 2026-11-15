import json

with open('runs/case2_odb_audit_results.json') as f:
    data = json.load(f)

for d in data:
    if d.get('exists') and d.get('probe') and not d['probe'].get('error'):
        has_nonzero = any(s.get('has_any_nonzero_miseseri') for s in d['probe'].get('steps', {}).values())
        if has_nonzero:
            print("=================================================================")
            print(f"Path: {d['path']}")
            print(f"Size: {d['size_bytes']:,} bytes, SHA256: {d['sha256']}")
            for sname, s in d['probe']['steps'].items():
                print(f"  Step '{sname}': {s['num_frames']} frames, procedure={s.get('procedure')}")
                print(f"    has_any_nonzero_miseseri: {s.get('has_any_nonzero_miseseri')}")
                for fr in s.get('frames', []):
                    if fr.get('has_miseseri'):
                        stats = fr.get('miseseri_stats')
                        print(f"    Frame {fr['frame_id']} (val={fr['frame_value']}): count={stats['count']}, non_zero={stats['non_zero_count']}, min={stats['min']:.4f}, max={stats['max']:.4f}, mean={stats['mean']:.4f}")
