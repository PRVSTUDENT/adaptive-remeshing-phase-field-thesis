#!/usr/bin/env python3
"""
Persistent Finite State Machine for Closed-Loop Adaptive Remeshing.
Tracks cycle state, history transitions, and execution payload with atomic JSON persistence.
Explicitly distinguishes dry-run package generation, datacheck qualification, and real solver execution.
"""

import json
import os
import time
from enum import Enum
from pathlib import Path
from typing import Dict, Any, Optional, List


class AdaptiveState(str, Enum):
    # Active execution states
    INITIALIZE = "INITIALIZE"
    SEGMENT_READY = "SEGMENT_READY"
    SEGMENT_SOLVED = "SEGMENT_SOLVED"
    FIELDS_EXTRACTED = "FIELDS_EXTRACTED"
    REMESH_DECISION = "REMESH_DECISION"
    REMESH_GENERATED = "REMESH_GENERATED"
    STATE_TRANSFERRED = "STATE_TRANSFERRED"
    TRANSFER_VALIDATED = "TRANSFER_VALIDATED"
    PACKAGE_GENERATED = "PACKAGE_GENERATED"
    RESTART_PACKAGE_READY = "RESTART_PACKAGE_READY"
    DATACHECK_QUALIFIED = "DATACHECK_QUALIFIED"
    SOLVER_EXECUTED = "SOLVER_EXECUTED"
    RESTART_COMPLETED = "RESTART_COMPLETED"
    DRY_RUN_ACCEPTED = "DRY_RUN_ACCEPTED"
    NEXT_SEGMENT = "NEXT_SEGMENT"
    COMPLETE = "COMPLETE"

    # Terminal / Exception states
    FAILED_TECHNICAL = "FAILED_TECHNICAL"
    FAILED_SCIENTIFIC = "FAILED_SCIENTIFIC"
    TRANSFER_REJECTED = "TRANSFER_REJECTED"
    REMESH_REJECTED = "REMESH_REJECTED"
    WAITING_FOR_HUMAN_AUTHORIZATION = "WAITING_FOR_HUMAN_AUTHORIZATION"


VALID_TRANSITIONS = {
    AdaptiveState.INITIALIZE: [
        AdaptiveState.SEGMENT_READY,
        AdaptiveState.FAILED_TECHNICAL,
        AdaptiveState.WAITING_FOR_HUMAN_AUTHORIZATION
    ],
    AdaptiveState.SEGMENT_READY: [
        AdaptiveState.SEGMENT_SOLVED,
        AdaptiveState.FAILED_TECHNICAL,
        AdaptiveState.WAITING_FOR_HUMAN_AUTHORIZATION
    ],
    AdaptiveState.SEGMENT_SOLVED: [
        AdaptiveState.FIELDS_EXTRACTED,
        AdaptiveState.FAILED_TECHNICAL,
        AdaptiveState.FAILED_SCIENTIFIC
    ],
    AdaptiveState.FIELDS_EXTRACTED: [
        AdaptiveState.REMESH_DECISION,
        AdaptiveState.FAILED_TECHNICAL
    ],
    AdaptiveState.REMESH_DECISION: [
        AdaptiveState.REMESH_GENERATED,
        AdaptiveState.NEXT_SEGMENT,
        AdaptiveState.COMPLETE,
        AdaptiveState.REMESH_REJECTED,
        AdaptiveState.FAILED_SCIENTIFIC
    ],
    AdaptiveState.REMESH_GENERATED: [
        AdaptiveState.STATE_TRANSFERRED,
        AdaptiveState.REMESH_REJECTED,
        AdaptiveState.FAILED_TECHNICAL
    ],
    AdaptiveState.STATE_TRANSFERRED: [
        AdaptiveState.TRANSFER_VALIDATED,
        AdaptiveState.FAILED_TECHNICAL
    ],
    AdaptiveState.TRANSFER_VALIDATED: [
        AdaptiveState.RESTART_PACKAGE_READY,
        AdaptiveState.PACKAGE_GENERATED,
        AdaptiveState.TRANSFER_REJECTED,
        AdaptiveState.FAILED_SCIENTIFIC
    ],
    AdaptiveState.PACKAGE_GENERATED: [
        AdaptiveState.RESTART_PACKAGE_READY,
        AdaptiveState.DRY_RUN_ACCEPTED,
        AdaptiveState.DATACHECK_QUALIFIED,
        AdaptiveState.WAITING_FOR_HUMAN_AUTHORIZATION,
        AdaptiveState.FAILED_TECHNICAL
    ],
    AdaptiveState.RESTART_PACKAGE_READY: [
        AdaptiveState.PACKAGE_GENERATED,
        AdaptiveState.DATACHECK_QUALIFIED,
        AdaptiveState.SOLVER_EXECUTED,
        AdaptiveState.RESTART_COMPLETED,
        AdaptiveState.DRY_RUN_ACCEPTED,
        AdaptiveState.WAITING_FOR_HUMAN_AUTHORIZATION,
        AdaptiveState.FAILED_TECHNICAL
    ],
    AdaptiveState.DATACHECK_QUALIFIED: [
        AdaptiveState.WAITING_FOR_HUMAN_AUTHORIZATION,
        AdaptiveState.SOLVER_EXECUTED,
        AdaptiveState.FAILED_TECHNICAL
    ],
    AdaptiveState.SOLVER_EXECUTED: [
        AdaptiveState.RESTART_COMPLETED,
        AdaptiveState.FIELDS_EXTRACTED,
        AdaptiveState.FAILED_TECHNICAL,
        AdaptiveState.FAILED_SCIENTIFIC
    ],
    AdaptiveState.DRY_RUN_ACCEPTED: [
        AdaptiveState.NEXT_SEGMENT,
        AdaptiveState.COMPLETE
    ],
    AdaptiveState.RESTART_COMPLETED: [
        AdaptiveState.NEXT_SEGMENT,
        AdaptiveState.COMPLETE,
        AdaptiveState.FAILED_TECHNICAL,
        AdaptiveState.FAILED_SCIENTIFIC
    ],
    AdaptiveState.NEXT_SEGMENT: [
        AdaptiveState.SEGMENT_READY,
        AdaptiveState.FIELDS_EXTRACTED,
        AdaptiveState.REMESH_DECISION,
        AdaptiveState.COMPLETE,
        AdaptiveState.FAILED_TECHNICAL
    ],
    AdaptiveState.COMPLETE: [],
    AdaptiveState.FAILED_TECHNICAL: [],
    AdaptiveState.FAILED_SCIENTIFIC: [],
    AdaptiveState.TRANSFER_REJECTED: [],
    AdaptiveState.REMESH_REJECTED: [],
    AdaptiveState.WAITING_FOR_HUMAN_AUTHORIZATION: [
        AdaptiveState.SEGMENT_READY,
        AdaptiveState.DATACHECK_QUALIFIED,
        AdaptiveState.SOLVER_EXECUTED,
        AdaptiveState.RESTART_COMPLETED,
        AdaptiveState.FAILED_TECHNICAL
    ]
}


class AdaptiveStateMachine:
    """
    Persistent Finite State Machine backed by an atomic JSON state file.
    """

    def __init__(self, state_file_path: Path):
        self.state_file_path = Path(state_file_path).resolve()
        self.state_file_path.parent.mkdir(parents=True, exist_ok=True)
        self.data: Dict[str, Any] = {}
        if self.state_file_path.is_file():
            self.load()
        else:
            self._init_default()

    def _init_default(self) -> None:
        self.data = {
            "version": "1.0.0",
            "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "updated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "current_state": AdaptiveState.INITIALIZE.value,
            "current_cycle": "cycle_000",
            "cycle_index": 0,
            "history": [],
            "cycle_records": {},
            "global_config": {},
            "diagnostics": {}
        }
        self.save()

    def save(self) -> None:
        """Atomic write to state file using temporary file and atomic replace."""
        self.data["updated_at"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        tmp_path = self.state_file_path.with_suffix(".tmp")
        with open(tmp_path, "w", encoding="utf-8") as f:
            json.dump(self.data, f, indent=2, sort_keys=True)
            f.write("\n")
        os.replace(tmp_path, self.state_file_path)

    def load(self) -> None:
        """Loads state from disk."""
        with open(self.state_file_path, "r", encoding="utf-8") as f:
            self.data = json.load(f)

    @property
    def current_state(self) -> str:
        return self.data.get("current_state", AdaptiveState.INITIALIZE.value)

    @property
    def current_cycle(self) -> str:
        return self.data.get("current_cycle", "cycle_000")

    @property
    def cycle_index(self) -> int:
        return self.data.get("cycle_index", 0)

    def is_terminal(self) -> bool:
        terminals = {
            AdaptiveState.COMPLETE.value,
            AdaptiveState.FAILED_TECHNICAL.value,
            AdaptiveState.FAILED_SCIENTIFIC.value,
            AdaptiveState.TRANSFER_REJECTED.value,
            AdaptiveState.REMESH_REJECTED.value
        }
        return self.current_state in terminals

    def is_waiting_for_human(self) -> bool:
        return self.current_state == AdaptiveState.WAITING_FOR_HUMAN_AUTHORIZATION.value

    def transition_to(
        self,
        new_state: AdaptiveState,
        payload: Optional[Dict[str, Any]] = None,
        force: bool = False
    ) -> None:
        """
        Executes a validated transition from current state to new_state.
        Records transition in history and updates persisted payload.
        """
        curr = AdaptiveState(self.current_state)
        target = AdaptiveState(new_state)

        if not force:
            allowed = VALID_TRANSITIONS.get(curr, [])
            if target not in allowed:
                raise ValueError(
                    f"Invalid state transition: {curr.value} -> {target.value}. "
                    f"Allowed targets: {[s.value for s in allowed]}"
                )

        transition_entry = {
            "from_state": curr.value,
            "to_state": target.value,
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "cycle": self.current_cycle,
            "payload_summary": list(payload.keys()) if payload else []
        }

        self.data["history"].append(transition_entry)
        self.data["current_state"] = target.value

        if payload:
            cycle_key = self.current_cycle
            if cycle_key not in self.data["cycle_records"]:
                self.data["cycle_records"][cycle_key] = {}
            self.data["cycle_records"][cycle_key].update(payload)

        self.save()

    def advance_cycle(self, next_cycle_id: Optional[str] = None) -> str:
        """Increments cycle counter and advances cycle ID."""
        curr_idx = self.cycle_index
        next_idx = curr_idx + 1
        if next_cycle_id is None:
            next_cycle_id = f"cycle_{next_idx:03d}"
        
        self.data["cycle_index"] = next_idx
        self.data["current_cycle"] = next_cycle_id
        if next_cycle_id not in self.data["cycle_records"]:
            self.data["cycle_records"][next_cycle_id] = {
                "predecessor": f"cycle_{curr_idx:03d}",
                "started_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
            }
        self.save()
        return next_cycle_id

    def set_cycle_data(self, key: str, value: Any) -> None:
        cycle_key = self.current_cycle
        if cycle_key not in self.data["cycle_records"]:
            self.data["cycle_records"][cycle_key] = {}
        self.data["cycle_records"][cycle_key][key] = value
        self.save()

    def get_cycle_data(self, key: str, default: Any = None) -> Any:
        cycle_key = self.current_cycle
        return self.data.get("cycle_records", {}).get(cycle_key, {}).get(key, default)

    def set_global(self, key: str, value: Any) -> None:
        self.data["global_config"][key] = value
        self.save()

    def get_global(self, key: str, default: Any = None) -> Any:
        return self.data.get("global_config", {}).get(key, default)
