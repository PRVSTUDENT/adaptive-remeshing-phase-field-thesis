import os
import hashlib
import json

def main():
    package_dir = "models/generated/mode_ii/f32_cae_runtime_gate_repair"
    manifest_files = [
        "M2RMBUILD7.pbs",
        "runtime/build_f32_geometry_backed_model.py",
        "runtime/generate_missing_evidence_report.py",
        "runtime/source_deck.inp",
        "runtime/validate_f32_runtime_audits.py",
        "runtime/validate_generated_input.py"
    ]

    hashes = {}
    lines = []
    for rel_p in sorted(manifest_files):
        full_p = os.path.join(package_dir, rel_p)
        with open(full_p, "rb") as f:
            h = hashlib.sha256(f.read()).hexdigest()
        hashes[rel_p] = h
        lines.append(f"{h}  {rel_p}")

    sha_content = "\n".join(lines) + "\n"

    with open(os.path.join(package_dir, "SHA256SUMS"), "w", encoding="utf-8") as f:
        f.write(sha_content)

    with open(os.path.join(package_dir, "F32_SHA256SUMS"), "w", encoding="utf-8") as f:
        f.write(sha_content)

    manifest_data = {
        "protocol_version": 1,
        "task_id": "F32-INVALIDATE-F31-AND-REPAIR-M2RMBUILD6-WORK-DIR-STAGING-GATE",
        "job_name": "M2RMBUILD7",
        "package_files": hashes
    }

    with open(os.path.join(package_dir, "PACKAGE_MANIFEST.json"), "w", encoding="utf-8") as f:
        json.dump(manifest_data, f, indent=2)

    print(f"Successfully generated SHA256SUMS, F32_SHA256SUMS, and PACKAGE_MANIFEST.json in {package_dir}")

if __name__ == "__main__":
    main()
