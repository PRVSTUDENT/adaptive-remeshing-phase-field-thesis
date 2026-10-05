import os, sys, json, hashlib

def sha256_file(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(65536), b''):
            h.update(chunk)
    return h.hexdigest()

def main():
    manifest_path = 'PACKAGE_MANIFEST.json'
    if not os.path.exists(manifest_path):
        print("ERROR: PACKAGE_MANIFEST.json not found")
        sys.exit(1)
    with open(manifest_path, 'r') as f:
        data = json.load(f)
    files = data.get('file_hashes', data.get('files', {}))
    for fname, expected_hash in files.items():
        if not os.path.exists(fname):
            print(f"ERROR: missing file {fname}")
            sys.exit(1)
        actual_hash = sha256_file(fname)
        if actual_hash != expected_hash:
            print(f"ERROR: Hash mismatch for {fname}: expected {expected_hash}, got {actual_hash}")
            sys.exit(1)
    print("ALL_MANIFEST_FILES_VERIFIED_PASS")

if __name__ == '__main__':
    main()
