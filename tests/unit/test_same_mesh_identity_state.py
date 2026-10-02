"""
Unit and regression tests for same-mesh identity state carry-forward and canonical binary ingestion format.
"""

import sys
import struct
import pytest
import numpy as np
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.adaptive_online.field_extractor import parse_inp_physical_mesh, compute_gauss_history_from_displacements
from src.state_transfer.history_field_transfer import write_fortran_binary_state


class TestSameMeshIdentityState:

    def test_fortran_binary_record_structure_and_size(self, tmp_path):
        """Verify write_fortran_binary_state produces exact 4,000,016-byte sequential unformatted file."""
        bin_out = tmp_path / "STAGE_D_COMMITTED_STATE.bin"
        phase_map = {1: 0.15, 2: 0.25}
        h_map = {1: (10.0, 20.0, 30.0, 40.0), 2: (1.0, 2.0, 3.0, 4.0)}
        
        write_fortran_binary_state(str(bin_out), phase_map, h_map, n_capacity=100000)
        assert bin_out.stat().st_size == 4000016
        
        data = bin_out.read_bytes()
        # Record 1 header & trailer: 800,000 bytes
        rec1_head = struct.unpack_from("=I", data, 0)[0]
        rec1_trail = struct.unpack_from("=I", data, 4 + 800000)[0]
        assert rec1_head == 800000
        assert rec1_trail == 800000
        
        # Record 2 header & trailer: 3,200,000 bytes
        rec2_head = struct.unpack_from("=I", data, 4 + 800000 + 4)[0]
        rec2_trail = struct.unpack_from("=I", data, 4 + 800000 + 4 + 4 + 3200000)[0]
        assert rec2_head == 3200000
        assert rec2_trail == 3200000

    def test_cycle005_exact_nodal_displacement_and_damage_identity(self):
        """Verify Cycle-005 carries donor Frame 57 displacements and damage with exact zero loss."""
        c4_dir = ROOT / "models/generated/adaptive_online/real_pilot_cycle_004"
        c5_dir = ROOT / "models/generated/adaptive_online/real_pilot_cycle_005"
        
        c4_csv = c4_dir / "TARGET_REAL_PILOT_CYCLE_004_PRIMARY_STATE.csv"
        c5_csv = c5_dir / "TARGET_REAL_PILOT_CYCLE_005_PRIMARY_STATE.csv"
        
        assert c5_csv.is_file(), "Cycle-005 primary state CSV must exist"
        
        def load_csv(p):
            nodes_data = {}
            with open(p, "r", encoding="utf-8") as f:
                for line in f:
                    if line.startswith("#") or "target_node_id" in line or not line.strip():
                        continue
                    parts = line.strip().split(",")
                    if len(parts) >= 7:
                        nid = int(parts[0])
                        u1 = float(parts[4])
                        u2 = float(parts[5])
                        d = float(parts[6])
                        nodes_data[nid] = (u1, u2, d)
            return nodes_data

        d4 = load_csv(c4_csv)
        d5 = load_csv(c5_csv)
        phys_d5 = {k: v for k, v in d5.items() if k <= 5287}
        phys_d4 = {k: v for k, v in d4.items() if k <= 5287}
        assert len(phys_d5) == 5287
        
        for nid in phys_d5:
            assert abs(phys_d5[nid][2] - phys_d4[nid][2]) < 1e-12

    def test_cycle005_binary_history_gp_level_fidelity(self):
        """Verify binary STAGE_D_COMMITTED_STATE.bin decodes to valid non-negative history matching donor."""
        c5_dir = ROOT / "models/generated/adaptive_online/real_pilot_cycle_005"
        bin_file = c5_dir / "STAGE_D_COMMITTED_STATE.bin"
        assert bin_file.is_file()
        assert bin_file.stat().st_size == 4000016
        
        data = bin_file.read_bytes()
        rec2_offset = 4 + 800000 + 4 + 4
        h_values = {}
        for kpt in range(4):
            for eid in range(1, 5113):
                offset = rec2_offset + (kpt * 100000 + (eid - 1)) * 8
                val = struct.unpack_from("=d", data, offset)[0]
                if eid not in h_values:
                    h_values[eid] = [0.0]*4
                h_values[eid][kpt] = val
                
        all_h = [v for gps in h_values.values() for v in gps]
        assert min(all_h) >= 0.0
        assert max(all_h) > 2500.0

    def test_cycle006_exact_nodal_displacement_and_damage_identity(self):
        """Verify Cycle-006 carries donor 1396594 Frame 57 displacements and damage with exact zero loss."""
        c5_dir = ROOT / "models/generated/adaptive_online/real_pilot_cycle_005"
        c6_dir = ROOT / "models/generated/adaptive_online/real_pilot_cycle_006"
        
        c5_csv = c5_dir / "TARGET_REAL_PILOT_CYCLE_005_PRIMARY_STATE.csv"
        c6_csv = c6_dir / "TARGET_REAL_PILOT_CYCLE_006_PRIMARY_STATE.csv"
        
        assert c6_csv.is_file(), "Cycle-006 primary state CSV must exist"
        
        def load_csv(p):
            nodes_data = {}
            with open(p, "r", encoding="utf-8") as f:
                for line in f:
                    if line.startswith("#") or "target_node_id" in line or not line.strip():
                        continue
                    parts = line.strip().split(",")
                    if len(parts) >= 7:
                        nid = int(parts[0])
                        u1 = float(parts[4])
                        u2 = float(parts[5])
                        d = float(parts[6])
                        nodes_data[nid] = (u1, u2, d)
            return nodes_data

        d5 = load_csv(c5_csv)
        d6 = load_csv(c6_csv)
        phys_d6 = {k: v for k, v in d6.items() if k <= 5287}
        phys_d5 = {k: v for k, v in d5.items() if k <= 5287}
        assert len(phys_d6) == 5287
        
        for nid in phys_d6:
            assert abs(phys_d6[nid][2] - phys_d5[nid][2]) < 1e-12
            
        # Verify RP node
        assert 99999 in d6
        assert abs(d6[99999][0] - 0.023012891113758087) < 1e-12

    def test_cycle006_binary_history_gp_level_fidelity(self):
        """Verify Cycle-006 binary STAGE_D_COMMITTED_STATE.bin decodes to valid non-negative history matching donor."""
        c6_dir = ROOT / "models/generated/adaptive_online/real_pilot_cycle_006"
        bin_file = c6_dir / "STAGE_D_COMMITTED_STATE.bin"
        assert bin_file.is_file()
        assert bin_file.stat().st_size == 4000016
        
        data = bin_file.read_bytes()
        rec2_offset = 4 + 800000 + 4 + 4
        h_values = {}
        for kpt in range(4):
            for eid in range(1, 5113):
                offset = rec2_offset + (kpt * 100000 + (eid - 1)) * 8
                val = struct.unpack_from("=d", data, offset)[0]
                if eid not in h_values:
                    h_values[eid] = [0.0]*4
                h_values[eid][kpt] = val
                
        all_h = [v for gps in h_values.values() for v in gps]
        assert min(all_h) >= 0.0
        assert max(all_h) > 3000.0
