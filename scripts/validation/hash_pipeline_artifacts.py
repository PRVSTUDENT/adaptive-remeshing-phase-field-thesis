import hashlib
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent

files_to_hash = [
    "scripts/postprocessing/evaluate_m2corr_pk10r2_topology.py",
    "scripts/postprocessing/evaluate_m2corr_pk10r1_samemesh_r6.py",
    "scripts/postprocessing/extract_validation_odb.py",
    "scripts/postprocessing/dual_validation_pipeline.py",
    "scripts/postprocessing/offline_qualify_pipeline.py",
    "runs/hpc/mode_ii_control_batch/evidence/QUALIFICATION_H1_1389686_TOPOLOGY_REPORT.json",
    "runs/hpc/mode_ii_control_batch/evidence/QUALIFICATION_H2_1389687_TOPOLOGY_REPORT.json",
    "runs/hpc/mode_ii_control_batch/evidence/QUALIFICATION_PK10R1_1389684_TOPOLOGY_REPORT.json",
    "runs/hpc/mode_ii_control_batch/evidence/QUALIFICATION_RESTART_R2_1389715_REPORT.json",
    "runs/hpc/mode_ii_control_batch/evidence/DUAL_VALIDATION_PIPELINE_SOFTWARE_QUALIFICATION_SUMMARY.json"
]

print("=== SHA256 HASHES FOR NEWLY PREPARED & QUALIFIED POSTPROCESSING ARTIFACTS ===")
for rel_path in files_to_hash:
    fp = ROOT / rel_path
    if fp.exists():
        h = hashlib.sha256(fp.read_bytes()).hexdigest()
        print(f"{rel_path}: {h}")
    else:
        print(f"{rel_path}: NOT FOUND")
