#!/usr/bin/env python3
import sys
from pathlib import Path

pkg_dir = Path(__file__).resolve().parent
repo_dir = pkg_dir / "runtime"
sys.path.insert(0, str(repo_dir))

print("Testing Package 171-R9 imports...")
from scripts.state_transfer.driver_package171_r9_c6_coupled_pdas import Package171R9C6PDASDriver
from scripts.validation.extract_package148_iteration import extract_single_iteration

print("REMOTE_IMPORT_SUCCESS: True")
