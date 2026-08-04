import os
import hashlib
import datetime

def main():
    evidence_dir = "runs/hpc/stage_f/f31_m2rmbuild6_static_gate/evidence"
    cluster_base = "/home/pr21vyci/projects/adaptive-remeshing/runs/hpc/stage_f/f31_m2rmbuild6_static_gate/evidence"
    now_utc = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    job_id = "1383394.mmaster02"
    task_id = "F31-CORRECT-M2RMBUILD6-AUTHORIZATION-RECORD"
    source_rev = "2baf0a961671f84b81d4071ca5f0940ceef1613a"

    files = sorted([f for f in os.listdir(evidence_dir) if f != "EVIDENCE_FILE_INVENTORY.csv"])
    lines = ["repository_relative_path,source_cluster_path,file_size,sha256,copied_at_utc,job_id,task_id,source_revision"]

    for f in files:
        path = os.path.join(evidence_dir, f).replace("\\", "/")
        cluster_path = f"{cluster_base}/{f}"
        size = os.path.getsize(path)
        with open(path, "rb") as fp:
            sha = hashlib.sha256(fp.read()).hexdigest()
        lines.append(f"{path},{cluster_path},{size},{sha},{now_utc},{job_id},{task_id},{source_rev}")

    inv_path = os.path.join(evidence_dir, "EVIDENCE_FILE_INVENTORY.csv")
    with open(inv_path, "w", encoding="utf-8") as fp:
        fp.write("\n".join(lines) + "\n")

    print(f"Wrote {len(files)} items to {inv_path}")

if __name__ == "__main__":
    main()
