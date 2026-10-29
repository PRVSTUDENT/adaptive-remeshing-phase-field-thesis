import os
import tarfile

pkg_dir = os.path.join("models", "pandey_kumar_mode1", "140_c4_inc92_h31_underrelaxed_forward_continuation")
tar_path = os.path.join(pkg_dir, "package140_bundle.tar.gz")

files_to_pack = [
    "active_set_boundary_cards.inc",
    "driver_c4_inc92_h31_continuation.py",
    "d_lower_bounds.csv",
    "f42_unified_12dof_active_set_uel.for",
    "job_notifications.sh",
    "M1_C4_INC92_H31_AUTHORIZATION.json",
    "M1_C4_INC92_H31_CONT.inp",
    "mode1_am_state_checkpoint.py",
    "nodal_displacements_initial.csv",
    "PACKAGE_MANIFEST.json",
    "run_c4_inc92_h31_cont_datacheck.sh",
    "stage_a_all_d0_boundary_cards.inc",
    "submit_M1_C4_INC92_H31_CONT.pbs"
]

if os.path.exists(tar_path):
    os.remove(tar_path)

with tarfile.open(tar_path, "w:gz") as tar:
    for fname in files_to_pack:
        fpath = os.path.join(pkg_dir, fname)
        tar.add(fpath, arcname=fname)

print("Packed %d files into %s, size=%d bytes" % (len(files_to_pack), tar_path, os.path.getsize(tar_path)))
