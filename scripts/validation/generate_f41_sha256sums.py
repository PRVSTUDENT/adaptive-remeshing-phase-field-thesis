#!/usr/bin/env python3
import glob
import hashlib
import os

def main():
    pkg_dir = os.path.normpath("models/generated/mode_ii/f41_crack_geometry_reconstruction")
    files = []
    for root, dirs, fnames in os.walk(pkg_dir):
        if "__pycache__" in dirs:
            dirs.remove("__pycache__")
        for fname in sorted(fnames):
            if fname in ("SHA256SUMS", "F41_SHA256SUMS") or fname.endswith(".pyc"):
                continue
            full_p = os.path.join(root, fname)
            files.append(full_p)


    files.sort()
    lines = []
    for fpath in files:
        with open(fpath, 'rb') as f:
            h = hashlib.sha256(f.read()).hexdigest()
        rel_p = os.path.relpath(fpath, pkg_dir).replace('\\', '/')
        lines.append("{0}  {1}".format(h, rel_p))

    content = "\n".join(lines) + "\n"
    with open(os.path.join(pkg_dir, "SHA256SUMS"), "w", newline="\n") as f:
        f.write(content)
    with open(os.path.join(pkg_dir, "F41_SHA256SUMS"), "w", newline="\n") as f:
        f.write(content)

    print("SHA256 checksums written for {0} files in {1}".format(len(files), pkg_dir))

if __name__ == "__main__":
    main()
