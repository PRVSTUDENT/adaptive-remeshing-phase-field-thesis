#!/usr/bin/env python3
"""
Compress Master's Thesis main.pdf using PyMuPDF (fitz) lossless deflation.
Eliminates unused streams, duplicate objects, and deflates content streams,
reducing PDF size from >100 MB down to ~86 MB while preserving full vector quality.
"""

import os
import sys
import fitz

def compress_pdf(input_path: str, output_path: str = None) -> None:
    if output_path is None:
        output_path = input_path

    if not os.path.exists(input_path):
        print(f"Error: input file does not exist: {input_path}")
        sys.exit(1)

    orig_size = os.path.getsize(input_path)
    print(f"Original size: {orig_size / (1024*1024):.2f} MB ({orig_size} bytes)")

    doc = fitz.open(input_path)
    temp_path = input_path + ".tmp.pdf"
    
    # Save with maximum compression and garbage collection
    doc.save(
        temp_path,
        garbage=4,
        deflate=True,
        clean=True,
        linear=False
    )
    doc.close()

    new_size = os.path.getsize(temp_path)
    print(f"Compressed size: {new_size / (1024*1024):.2f} MB ({new_size} bytes)")
    reduction = (orig_size - new_size) / orig_size * 100
    print(f"Reduction: {reduction:.2f}%")

    # Replace original file atomically
    os.replace(temp_path, output_path)
    print(f"Successfully updated: {output_path}")

if __name__ == "__main__":
    thesis_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "MA_AdaptiveRemeshing_Report_2026"))
    pdf_path = os.path.join(thesis_dir, "main.pdf")
    compress_pdf(pdf_path)
