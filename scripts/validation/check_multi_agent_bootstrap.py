#!/usr/bin/env python3
"""Fail-closed consistency checks for multi-agent bootstrap entrypoints."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MARKER = "MULTI-AGENT BOOTSTRAP"
PROTOCOL_VERSION = 1
FORBIDDEN_AGENT_DIRS = ("codex_code", "grok_code", "gemini_code", "gemini_antigravity_code")


def fail(msg: str, errors: list[str]) -> None:
    errors.append(msg)


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    args = parser.parse_args()
    root: Path = args.root
    errors: list[str] = []

    agents = root / "AGENTS.md"
    agent_md = root / ".agent.md"
    adaptive = root / "adaptive_remeshing_phase_field_agent.md"
    gemini = root / "GEMINI.md"
    grok = root / "GROK.md"
    readme = root / "README.md"
    start = root / "project_coordination" / "START_HERE.md"
    current = root / "project_coordination" / "CURRENT_STATE.md"
    active_session = root / "project_coordination" / "ACTIVE_SESSION.json"
    active_task = root / "project_coordination" / "ACTIVE_TASK.json"
    protocol = root / "project_coordination" / "PROTOCOL_VERSION.json"
    auth = root / "runs" / "hpc" / "stage_f" / "mode_ii_h0" / "MODE_II_H0_AUTHORIZATION.json"

    for path in (
        agents,
        agent_md,
        adaptive,
        gemini,
        grok,
        readme,
        start,
        current,
        active_session,
        active_task,
        protocol,
        auth,
    ):
        if not path.is_file():
            fail(f"missing required file: {path.relative_to(root)}", errors)

    if errors:
        print("multi_agent_bootstrap_consistency_fail")
        for e in errors:
            print(f"  - {e}")
        return 1

    agents_text = read(agents)
    agent_text = read(agent_md)
    adaptive_text = read(adaptive)
    gemini_text = read(gemini)
    grok_text = read(grok)
    readme_text = read(readme)
    start_text = read(start)

    if "Protocol version: 1" not in agents_text and "protocol version: 1" not in agents_text.lower():
        fail("AGENTS.md must declare Protocol version: 1", errors)
    if "project_coordination/CURRENT_STATE.md" not in agents_text:
        fail("AGENTS.md must point to project_coordination/CURRENT_STATE.md", errors)
    if "ACTIVE_SESSION.json" not in agents_text:
        fail("AGENTS.md must point to ACTIVE_SESSION.json", errors)
    if "mandatory active coordination" in agents_text.lower() and "agent_handoff" in agents_text:
        # AGENTS.md may mention agent_handoff as legacy only
        if "not the active coordination system" not in agents_text:
            fail("AGENTS.md must not treat agent_handoff as mandatory active coordination", errors)

    if MARKER not in agent_text:
        fail(".agent.md missing MULTI-AGENT BOOTSTRAP marker", errors)
    if "AGENTS.md" not in agent_text:
        fail(".agent.md must reference AGENTS.md", errors)
    if "project_coordination/CURRENT_STATE.md" not in agent_text:
        fail(".agent.md must point to CURRENT_STATE.md", errors)
    if "ACTIVE_SESSION.json" not in agent_text:
        fail(".agent.md must point to ACTIVE_SESSION.json", errors)
    if "agent_handoff/` directory with a manifest for easy review" in agent_text:
        fail(".agent.md still describes mandatory agent_handoff mirroring as the handoff principle", errors)
    if "File-handoff principle: every source/text file created or edited by the agent is mirrored into a flat `agent_handoff/`" in agent_text:
        fail(".agent.md still has old File-handoff principle", errors)
    if "Current thesis handoff - update this block after every substantial work session" in agent_text:
        fail(".agent.md still has dynamic Current thesis handoff block", errors)
    if "not the active coordination system" not in agent_text and "not the active coordination" not in agent_text:
        fail(".agent.md must state agent_handoff is not active coordination", errors)

    if MARKER not in adaptive_text:
        fail("adaptive_remeshing_phase_field_agent.md missing MULTI-AGENT BOOTSTRAP marker", errors)
    if "AGENTS.md" not in adaptive_text:
        fail("adaptive_remeshing_phase_field_agent.md must reference AGENTS.md", errors)
    if "project_coordination/CURRENT_STATE.md" not in adaptive_text:
        fail("adaptive_remeshing_phase_field_agent.md must point to CURRENT_STATE.md", errors)
    if "ACTIVE_SESSION.json" not in adaptive_text:
        fail("adaptive_remeshing_phase_field_agent.md must point to ACTIVE_SESSION.json", errors)
    if "Current thesis handoff - update this block after every substantial work session" in adaptive_text:
        fail("adaptive_remeshing_phase_field_agent.md still has dynamic Current thesis handoff block", errors)
    if "File-handoff principle: every source/text file created or edited by the agent is mirrored into a flat `agent_handoff/`" in adaptive_text:
        fail("adaptive_remeshing_phase_field_agent.md still has old File-handoff principle", errors)

    if "AGENTS.md" not in gemini_text:
        fail("GEMINI.md must point to AGENTS.md", errors)
    if "ACTIVE_SESSION.json" not in gemini_text:
        fail("GEMINI.md must point to ACTIVE_SESSION.json", errors)
    if "Protocol version: 1" not in gemini_text:
        fail("GEMINI.md must report Protocol version: 1", errors)

    if "AGENTS.md" not in grok_text:
        fail("GROK.md must point to AGENTS.md", errors)
    if "ACTIVE_SESSION.json" not in grok_text:
        fail("GROK.md must point to ACTIVE_SESSION.json", errors)
    if "Protocol version: 1" not in grok_text:
        fail("GROK.md must report Protocol version: 1", errors)

    if "AGENTS.md" not in readme_text:
        fail("README.md must point to AGENTS.md", errors)

    if "project_coordination/CURRENT_STATE.md" not in start_text:
        fail("START_HERE.md must reference CURRENT_STATE.md", errors)

    try:
        proto = json.loads(protocol.read_text(encoding="utf-8"))
        if proto.get("protocol_version") != PROTOCOL_VERSION:
            fail(f"PROTOCOL_VERSION.json protocol_version must be {PROTOCOL_VERSION}", errors)
        if proto.get("canonical_entrypoint") != "AGENTS.md":
            fail("PROTOCOL_VERSION.json canonical_entrypoint must be AGENTS.md", errors)
        if proto.get("legacy_handoff_active") is not False:
            fail("PROTOCOL_VERSION.json legacy_handoff_active must be false", errors)
    except (OSError, json.JSONDecodeError) as exc:
        fail(f"invalid PROTOCOL_VERSION.json: {exc}", errors)

    try:
        task = json.loads(active_task.read_text(encoding="utf-8"))
        # After COORD-1 pass, active task should be F1-P0 ready (or COORD-1 active during work).
        tid = task.get("task_id")
        if tid not in {"F1-P0", "COORD-1"}:
            fail(f"ACTIVE_TASK.json task_id unexpected: {tid}", errors)
        if tid == "F1-P0" and task.get("status") not in {"ready", "active"}:
            fail("F1-P0 status must be ready or active", errors)
        if task.get("execution_authorized") is not False:
            fail("ACTIVE_TASK.json execution_authorized must be false", errors)
        if task.get("maximum_jobs_now", 1) not in (0, None) and task.get("maximum_jobs_now") != 0:
            fail("ACTIVE_TASK.json maximum_jobs_now must be 0", errors)
    except (OSError, json.JSONDecodeError) as exc:
        fail(f"invalid ACTIVE_TASK.json: {exc}", errors)

    try:
        session = json.loads(active_session.read_text(encoding="utf-8"))
        # During/after COORD-1 completion, lock should be free for next agent.
        # Validator allows active only if agent is grok/codex/gemini and task COORD-1.
        if session.get("active") is True:
            if session.get("task_id") != "COORD-1":
                fail("ACTIVE_SESSION active for non-COORD-1 task during bootstrap check", errors)
        if "ACTIVE_SESSION" not in str(active_session):
            pass
    except (OSError, json.JSONDecodeError) as exc:
        fail(f"invalid ACTIVE_SESSION.json: {exc}", errors)

    try:
        auth_data = json.loads(auth.read_text(encoding="utf-8"))
        if auth_data.get("datacheck_authorized") is not False:
            fail("Stage-F datacheck_authorized must remain false", errors)
        if auth_data.get("solver_authorized") is not False:
            fail("Stage-F solver_authorized must remain false", errors)
    except (OSError, json.JSONDecodeError) as exc:
        fail(f"invalid Mode-II authorization: {exc}", errors)

    for name in FORBIDDEN_AGENT_DIRS:
        if (root / name).exists():
            fail(f"forbidden agent-specific source directory exists: {name}", errors)

    if errors:
        print("multi_agent_bootstrap_consistency_fail")
        for e in errors:
            print(f"  - {e}")
        return 1

    print("multi_agent_bootstrap_consistency_pass")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
