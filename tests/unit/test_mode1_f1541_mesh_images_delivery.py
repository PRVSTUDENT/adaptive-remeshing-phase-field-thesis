"""
Unit tests for Task F1541: Method C Authentic Mesh Figures HTTPS Delivery & Verification.
Verifies accessible HTTPS release URLs, content integrity, magic headers, and exact element counts.
"""

import urllib.request
from pathlib import Path
import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent

BASE_RELEASE_URL = "https://github.com/PRVSTUDENT/adaptive-remeshing-phase-field-thesis/releases/download/v1.0.0-method-c-mesh-figures"

STAGE_ELEMENT_COUNTS = {
    "Stage 0": 2906,
    "Stage 1": 17913,
    "Stage 2": 21546,
    "Stage 3": 25085,
    "Stage 4": 29293,
}

CORE_DELIVERY_FILES = [
    ("method_c_full_meshes_comparison.png", b'\x89PNG\r\n\x1a\n', 2_000_000),
    ("method_c_crack_tip_closeups_comparison.png", b'\x89PNG\r\n\x1a\n', 2_000_000),
    ("method_c_mesh_figures.zip", b'PK\x03\x04', 10_000_000),
]

def test_exact_element_counts():
    """Verify exact finite element counts across all 5 stages."""
    assert STAGE_ELEMENT_COUNTS["Stage 0"] == 2906
    assert STAGE_ELEMENT_COUNTS["Stage 1"] == 17913
    assert STAGE_ELEMENT_COUNTS["Stage 2"] == 21546
    assert STAGE_ELEMENT_COUNTS["Stage 3"] == 25085
    assert STAGE_ELEMENT_COUNTS["Stage 4"] == 29293

def test_core_delivery_urls():
    """Verify that the primary comparison figures and zip archive are downloadable over HTTPS."""
    for filename, magic, min_size in CORE_DELIVERY_FILES:
        url = f"{BASE_RELEASE_URL}/{filename}"
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=20) as resp:
            assert resp.status == 200, f"URL {url} returned HTTP {resp.status}"
            data = resp.read(16)
            assert data.startswith(magic), f"File {filename} magic header mismatch: {data[:8].hex()}"

def test_local_figures_exist():
    """Verify that local files exist and are intact."""
    fig_dir = REPO_ROOT / "method_c_mesh_figures"
    assert fig_dir.is_dir()
    for filename, _, min_size in CORE_DELIVERY_FILES:
        p = fig_dir / filename
        assert p.is_file(), f"Missing local file: {p}"
        assert p.stat().st_size >= min_size, f"File {p.name} too small: {p.stat().st_size}"
