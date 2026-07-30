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
CONTROL_CHARS = tuple(chr(i) for i in range(32) if i not in (9, 10, 13))
FORBIDDEN_WORKFLOW_PHRASES = (
    "Refresh `agent_handoff/`",
    "Refresh agent_handoff/",
    "mirror the touched files",
    "At the end of a Codex edit operation, mirror",
    "python scripts/sync_agent_handoff.py",
    "For current Stage D work",
)
ALLOWED_TASK_IDS = frozenset(
    {
        "F5-H2-COMPILER-RECOVERY-AND-MISESERI-REMESH-READINESS",
        "COORD-0",
        "COORD-1",
        "COORD-1R",
        "F1-P0",
        "F1-J0-AUTH",
        "F1-J0",
        "F1-J1-PREP",
        "F1-J1-PREP-R1",
        "F1-J1-PREP-R2",
        "F1-J1-AUTH",
        "F1-J1-AUTH-R1",
        "F1-J1-R1-PREP",
        "F1-J1-R1-AUTH",
        "F1-J1-R1",
        "F1-J1-R2-PREP",
        "F1-J1-R2-PREP-R1",
        "F1-J1-R2-PREP-R2",
        "F1-J1-R2-PREP-R3",
        "F1-J1-R2-AUTH",
        "F1-J1-R2",
        "F1-J1-R2-CLOSE",
        "F1-J1-R2-CLOSE-R1",
        "F1-C0-ENDPOINT-AUDIT",
        "F1-C1-CORRECTED-H0-PREP",
        "F1-C2-DATACHECK-AUTH",
        "F1-C2-DATACHECK",
        "F1-C2-DATACHECK-CLOSE",
        "F1-C2-R1-PREP",
        "F1-C2-R1-AUTH",
        "F1-C2-R1-DATACHECK",
        "F1-C2-R1-CLOSE",
        "F1-C2-R1-SOLVER-AUTH",
        "F1-C2-R1-SOLVER-PREP",
        "F1-C2-R1-SOLVER-PREP-CORRECTION",
        "F1-C2-R1-SOLVER-REAUTH",
        "F1-C2-R1-SOLVER",
        "F1-C2-R1-SOLVER-CLOSE",
        "F1-C2-R1-H0-VALIDATOR-FIX",
        "F2-H1-BASELINE-PREP",
        "F2-H1-DATACHECK-LANE-FIX",
        "F2-H1-DATACHECK",
        "F2-H1-DATACHECK-CLOSE",
        "F2-H1-SOLVER",
        "F2-H1-SOLVER-CLOSE",
        "F2-H1-ENDPOINT-SWEEP-BATCH",
        "F2-H1-ENDPOINT-SWEEP-BATCH-CLOSE",
        "F2-H1-REFERENCE-FREEZE-AND-F3-PREP",
        "F3-STAGE-F3-BATCH-READINESS-FIX",
        "F3-STAGE-F3-PLANE-STRAIN-PARITY-PUBLISH",
        "F3-STAGE-F3-SUBMIT",
        "F3-STAGE-F3-AUTH-CONSUME-AND-MISESERI-EXTRACT",
        "F3-STAGE-F3-AUTH-PUBLISH-AND-ODB-VERIFY",
        "F4-H2-U020-AND-MISESERI-PBS-READINESS",
        "F4-TWO-JOB-BATCH-GUARD-REPAIR",
        "F4-FINAL-PBS-EXECUTION-CONTRACT-REPAIR",
        "F1-J1",
    }
)






def fail(msg: str, errors: list[str]) -> None:
    errors.append(msg)


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def has_control_chars(path: Path) -> list[int]:
    data = path.read_bytes()
    return sorted({b for b in data if b < 32 and b not in (9, 10, 13)})


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

    entrypoint_paths = (agents, agent_md, adaptive, gemini, grok, readme, start)
    for path in entrypoint_paths:
        bad = has_control_chars(path)
        if bad:
            fail(
                f"{path.relative_to(root)} contains C0 control characters: {bad}",
                errors,
            )
        text = read(path)
        for phrase in FORBIDDEN_WORKFLOW_PHRASES:
            if phrase in text:
                # Allow explicit prohibition of the sync script, but not a command recipe.
                if phrase == "python scripts/sync_agent_handoff.py":
                    # Fail only if it appears as an instruction to run, not "Do not run ...".
                    for line in text.splitlines():
                        if phrase in line and "do not" not in line.lower() and "not run" not in line.lower() and "not use" not in line.lower():
                            fail(
                                f"{path.relative_to(root)} still instructs running {phrase}: {line.strip()[:120]}",
                                errors,
                            )
                else:
                    fail(
                        f"{path.relative_to(root)} contains forbidden workflow phrase: {phrase}",
                        errors,
                    )

    # Malformed fence: doubled ```text openers
    for path, text in ((agent_md, agent_text), (adaptive, adaptive_text)):
        fence = "```"
        doubled = fence + "text\n" + fence + "text"
        if doubled in text:
            fail(f"{path.name} has malformed doubled code fence openers", errors)

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
    if "project_coordination/" not in readme_text or "Dynamic task, authorization, and job state" not in readme_text:
        fail("README.md must state dynamic state lives under project_coordination/", errors)
    if "Codex Starter Pack" in readme_text:
        fail("README.md still describes Codex-only starter pack branding", errors)
    if "First use" in readme_text and "mirror" in readme_text.lower():
        fail("README.md still contains obsolete First-use handoff workflow", errors)

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
        if tid not in ALLOWED_TASK_IDS:
            fail(f"ACTIVE_TASK.json task_id unexpected: {tid}", errors)
        if tid == "F1-P0" and task.get("status") not in {"ready", "active"}:
            fail("F1-P0 status must be ready or active", errors)
        if task.get("submission_approved") is not True and task.get("execution_authorized") is not False:
            fail("ACTIVE_TASK.json execution_authorized must be false when submission_approved is not true", errors)
        if task.get("submission_approved") is not True and task.get("maximum_jobs_now", 1) not in (0, None) and task.get("maximum_jobs_now") != 0:
            fail("ACTIVE_TASK.json maximum_jobs_now must be 0 when submission_approved is not true", errors)
    except (OSError, json.JSONDecodeError) as exc:
        fail(f"invalid ACTIVE_TASK.json: {exc}", errors)

    try:
        session = json.loads(active_session.read_text(encoding="utf-8"))
        # After bootstrap/integrity tasks, lock should normally be free.
        # Allow temporary claim only for COORD-1 / COORD-1R.
        if session.get("active") is True:
            if session.get("task_id") not in ALLOWED_TASK_IDS:
                fail("ACTIVE_SESSION active for non-allowed task during bootstrap check", errors)
    except (OSError, json.JSONDecodeError) as exc:
        fail(f"invalid ACTIVE_SESSION.json: {exc}", errors)

    try:
        auth_data = json.loads(auth.read_text(encoding="utf-8"))
        task_data = json.loads(active_task.read_text(encoding="utf-8"))
        tid = task_data.get("task_id")
        if tid not in {"F1-J1-AUTH", "F1-J1"} and auth_data.get("solver_authorized") is not False:
            fail("Stage-F solver_authorized must remain false until solver auth", errors)
        if auth_data.get("automatic_retry_authorized") is not False:
            fail("Stage-F automatic_retry_authorized must remain false", errors)
        if auth_data.get("maximum_datacheck_submissions") != 1:
            fail("Stage-F maximum_datacheck_submissions must equal 1", errors)
        used = auth_data.get("datacheck_submissions_used")
        if not isinstance(used, int) or isinstance(used, bool) or used not in (0, 1):
            fail("Stage-F datacheck_submissions_used invalid", errors)
        if auth_data.get("datacheck_authorized") is True:
            if auth_data.get("classification") != "stage_f_mode_ii_h0_datacheck_authorized":
                fail(
                    "datacheck_authorized true requires classification "
                    "stage_f_mode_ii_h0_datacheck_authorized",
                    errors,
                )
            if used != 0:
                fail(
                    "authorized unused datacheck must have datacheck_submissions_used=0",
                    errors,
                )
        elif auth_data.get("datacheck_authorized") is not False:
            fail("Stage-F datacheck_authorized must be boolean", errors)
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
