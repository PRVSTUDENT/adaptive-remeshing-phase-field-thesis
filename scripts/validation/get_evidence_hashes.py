import hashlib
import pathlib

files = [
    'docs/validation/METHOD_C_LPANEL_DYNAMIC_ADAPTIVE_CAMPAIGN_REPORT.md',
    'models/mode_II_or_l_panel/295_method_c_lpanel/local_windows_adaptive_run/PK_METHOD_C_LPANEL_CYCLE10_SUMMARY.json',
    'models/mode_II_or_l_panel/295_method_c_lpanel/local_windows_adaptive_run/PK_METHOD_C_LPANEL_CYCLE10_mesh_damage.png',
    'models/mode_II_or_l_panel/295_method_c_lpanel/local_windows_adaptive_run/image_manifest.json',
    'models/mode_II_or_l_panel/295_method_c_lpanel/local_windows_adaptive_run/PK_METHOD_C_LPANEL_CYCLE11.sta',
    'models/mode_II_or_l_panel/295_method_c_lpanel/local_windows_adaptive_run/PK_METHOD_C_LPANEL_CYCLE11.dat',
    'models/mode_II_or_l_panel/295_method_c_lpanel/local_windows_adaptive_run/PK_METHOD_C_LPANEL_CYCLE11.msg',
    'tests/unit/test_method_c_lpanel.py'
]

for f in files:
    p = pathlib.Path(f)
    if p.exists():
        h = hashlib.sha256(p.read_bytes()).hexdigest().upper()
        print(f"{f}: {h}")
    else:
        print(f"MISSING: {f}")
