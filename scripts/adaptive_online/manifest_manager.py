#!/usr/bin/env python3
"""
Cryptographic Provenance and Cycle Manifest Manager.
Constructs immutable, traceable JSON manifests for every adaptive remeshing cycle.
"""

import os
import json
import time
import hashlib
from pathlib import Path
from typing import Dict, Any, Optional, List


def compute_sha256_file(path: Path) -> str:
    """Computes SHA-256 of file on disk."""
    p = Path(path)
    if not p.is_file():
        return "FILE_NOT_FOUND"
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


class CycleManifest:
    """
    Constructs and records complete provenance for an adaptive cycle.
    """

    def __init__(self, cycle_id: str, output_dir: Path):
        self.cycle_id = cycle_id
        self.output_dir = Path(output_dir).resolve()
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.manifest_path = self.output_dir / f"{cycle_id.upper()}_MANIFEST.json"
        self.data: Dict[str, Any] = {
            "cycle_id": cycle_id,
            "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "predecessor_cycle": None,
            "donor_state": {},
            "target_state": {},
            "trigger_evaluation": {},
            "mesh_statistics": {},
            "material_parameters": {
                "E_kN_mm2": 210.0,
                "nu": 0.30,
                "Gc_kN_mm": 0.0027,
                "l0_mm": 0.015,
                "k_res": 1.0e-7,
                "thickness_mm": 1.0
            },
            "segment_interval": {},
            "transfer_statistics": {},
            "invariant_audit": {},
            "cryptographic_hashes": {},
            "execution_plan": {},
            "status": "INITIALIZED"
        }

    def set_donor(
        self,
        donor_job: str,
        donor_frame: int,
        donor_u1: float,
        donor_dmax: float,
        donor_inp_sha: str,
        synthetic: bool = False,
        provenance_details: Optional[Dict[str, Any]] = None
    ) -> None:
        self.data["donor_state"] = {
            "donor_job": donor_job,
            "donor_frame": donor_frame,
            "donor_u1_mm": donor_u1,
            "donor_dmax": donor_dmax,
            "donor_inp_sha256": donor_inp_sha,
            "synthetic": synthetic,
            "provenance": provenance_details or {}
        }

    def set_target_mesh_stats(self, n_phys: int, n_nodes: int, n_layered: int, h_min: float, h_max: float, area: float, strategy: str = "STRUCTURED_CORRIDOR_EXPERIMENTAL") -> None:
        self.data["mesh_statistics"] = {
            "strategy": strategy,
            "num_physical_elements": n_phys,
            "num_physical_nodes": n_nodes,
            "num_layered_elements": n_layered,
            "h_min_mm": h_min,
            "h_max_mm": h_max,
            "total_domain_area_mm2": area
        }

    def set_trigger(self, fired_triggers: List[str], metrics: Dict[str, Any], rationale: str, classifications: Optional[Dict[str, str]] = None) -> None:
        self.data["trigger_evaluation"] = {
            "fired_triggers": fired_triggers,
            "remesh_required": len(fired_triggers) > 0,
            "metrics": metrics,
            "rationale": rationale,
            "classifications": classifications or {}
        }

    def set_segment(self, u1_start: float, u1_end: float) -> None:
        self.data["segment_interval"] = {
            "u1_start_mm": u1_start,
            "u1_end_mm": u1_end,
            "delta_u1_mm": u1_end - u1_start
        }

    def set_transfer_audit(self, transfer_metrics: Dict[str, Any]) -> None:
        self.data["transfer_statistics"] = transfer_metrics
        self.data["invariant_audit"] = {
            "passed": transfer_metrics.get("passed", False),
            "violations": transfer_metrics.get("violations", [])
        }

    def record_hashes(self, files_to_hash: Dict[str, Path]) -> None:
        for key, p in files_to_hash.items():
            self.data["cryptographic_hashes"][key] = compute_sha256_file(p)

    def set_execution_plan(self, solver_command: str, pbs_command: str, dry_run: bool = True, datacheck_mode: bool = False) -> None:
        self.data["execution_plan"] = {
            "solver_command": solver_command,
            "pbs_command": pbs_command,
            "dry_run": dry_run,
            "datacheck_mode": datacheck_mode,
            "qsub_authorized": False
        }

    def save(self, status: Optional[str] = None) -> Path:
        if status:
            self.data["status"] = status
        self.data["updated_at"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        with open(self.manifest_path, "w", encoding="utf-8") as f:
            json.dump(self.data, f, indent=2, sort_keys=True)
            f.write("\n")
        return self.manifest_path
