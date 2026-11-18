# -*- coding: utf-8 -*-
"""
Synchronize EXPECTED_INP_SHA in all F1859 PBS scripts with the actual SHA-256
of the LF-normalized production input decks.
"""
import os
import re
import json
import hashlib

BASE_DIR = r"models/pandey_kumar_mode1/286_f1859_four_benchmark_reference_comparison"
RECEIPT_PATH = os.path.join(BASE_DIR, "f1859_suite_receipt.json")

def sha256_file(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest().upper()

def main():
    with open(RECEIPT_PATH, "r", encoding="utf-8") as f:
        receipt = json.load(f)

    updated_jobs = []
    for jid, job in receipt["jobs"].items():
        deck_path = job["deck_path"]
        pbs_path = job["pbs_script"]

        if not os.path.exists(deck_path):
            raise FileNotFoundError(f"Deck not found: {deck_path}")
        if not os.path.exists(pbs_path):
            raise FileNotFoundError(f"PBS script not found: {pbs_path}")

        # Ensure deck is LF only
        with open(deck_path, "rb") as fp:
            deck_bytes = fp.read()
        if b"\r\n" in deck_bytes:
            deck_bytes = deck_bytes.replace(b"\r\n", b"\n")
            with open(deck_path, "wb") as fp:
                fp.write(deck_bytes)
            print(f"Normalized {deck_path} to LF")

        actual_deck_sha = sha256_file(deck_path)
        job["deck_sha256"] = actual_deck_sha

        # Read PBS script
        with open(pbs_path, "r", encoding="utf-8") as fp:
            pbs_text = fp.read()

        # Replace EXPECTED_INP_SHA
        pattern = r'EXPECTED_INP_SHA="[a-fA-F0-9]+"'
        replacement = f'EXPECTED_INP_SHA="{actual_deck_sha.lower()}"'
        if not re.search(pattern, pbs_text):
            raise ValueError(f"Pattern not found in {pbs_path}")

        new_pbs_text = re.sub(pattern, replacement, pbs_text)

        # Write PBS script with LF only
        with open(pbs_path, "w", encoding="utf-8", newline="\n") as fp:
            fp.write(new_pbs_text)

        actual_pbs_sha = sha256_file(pbs_path)
        job["pbs_sha256"] = actual_pbs_sha

        print(f"Updated {jid}:")
        print(f"  Deck: {os.path.basename(deck_path)} -> SHA: {actual_deck_sha.lower()}")
        print(f"  PBS:  {os.path.basename(pbs_path)} -> SHA: {actual_pbs_sha.lower()}")
        updated_jobs.append(jid)

    with open(RECEIPT_PATH, "w", encoding="utf-8", newline="\n") as f:
        json.dump(receipt, f, indent=2)

    print(f"\nSuccessfully synchronized {len(updated_jobs)} PBS scripts and updated receipt.")

if __name__ == "__main__":
    main()
