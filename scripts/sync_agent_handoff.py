#!/usr/bin/env python3
"""Create a flat, reviewable snapshot of files touched in one agent operation.

Usage:
    python scripts/sync_agent_handoff.py path/to/file1 path/to/file2

The destination defaults to <workspace>/agent_handoff. Existing files in that
folder are removed before the new snapshot is copied. Large/generated Abaqus
outputs are rejected by default.
"""

from __future__ import annotations

import argparse
import hashlib
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

EXCLUDED_EXTENSIONS = {
    ".odb",
    ".sim",
    ".stt",
    ".res",
    ".mdl",
    ".prt",
    ".dat",
    ".msg",
    ".lck",
    ".023",
    ".cax",
    ".abq",
    ".pac",
    ".sel",
}
DEFAULT_MAX_BYTES = 25 * 1024 * 1024


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def find_workspace_root(start: Path) -> Path:
    current = start.resolve()
    for candidate in (current, *current.parents):
        if (candidate / ".agent.md").exists():
            return candidate
    return current


def clear_directory(directory: Path) -> None:
    directory.mkdir(parents=True, exist_ok=True)
    for child in directory.iterdir():
        if child.is_dir():
            shutil.rmtree(child)
        else:
            child.unlink()


def resolve_files(raw_paths: Iterable[str], workspace: Path) -> list[Path]:
    resolved: list[Path] = []
    for raw in raw_paths:
        candidate = Path(raw).expanduser()
        if not candidate.is_absolute():
            candidate = workspace / candidate
        candidate = candidate.resolve()
        if not candidate.exists():
            raise FileNotFoundError(f"File does not exist: {candidate}")
        if not candidate.is_file():
            raise ValueError(f"Not a regular file: {candidate}")
        resolved.append(candidate)
    return resolved


def relative_or_absolute(path: Path, workspace: Path) -> str:
    try:
        return path.relative_to(workspace).as_posix()
    except ValueError:
        return str(path)


def flat_mirror_name(path: Path, workspace: Path, duplicate_basenames: set[str]) -> str:
    if path.name not in duplicate_basenames:
        return path.name
    relative = relative_or_absolute(path, workspace)
    safe = (
        relative.replace("\\", "/")
        .replace("/", "__")
        .replace(":", "")
        .replace(" ", "_")
    )
    return safe


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("files", nargs="+", help="Files created or edited in the current operation")
    parser.add_argument("--workspace", type=Path, help="Workspace root; defaults to nearest folder containing .agent.md")
    parser.add_argument("--destination", type=Path, help="Destination directory; defaults to <workspace>/agent_handoff")
    parser.add_argument("--allow-large", action="store_true", help="Allow files larger than the default 25 MiB limit")
    parser.add_argument("--allow-generated", action="store_true", help="Allow excluded Abaqus-generated extensions")
    args = parser.parse_args()

    workspace = (args.workspace or find_workspace_root(Path.cwd())).resolve()
    destination = (args.destination or (workspace / "agent_handoff")).resolve()

    try:
        files = resolve_files(args.files, workspace)
    except (FileNotFoundError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    basenames = [path.name for path in files]
    duplicate_basenames = {name for name in basenames if basenames.count(name) > 1}

    for path in files:
        if path.suffix.lower() in EXCLUDED_EXTENSIONS and not args.allow_generated:
            print(f"ERROR: generated/large Abaqus output is excluded: {path}", file=sys.stderr)
            return 2
        if path.stat().st_size > DEFAULT_MAX_BYTES and not args.allow_large:
            print(f"ERROR: file exceeds 25 MiB; use --allow-large only after review: {path}", file=sys.stderr)
            return 2

    clear_directory(destination)

    timestamp = datetime.now(timezone.utc).isoformat()
    manifest_rows: list[str] = []
    for source in files:
        mirrored_name = flat_mirror_name(source, workspace, duplicate_basenames)
        target = destination / mirrored_name
        shutil.copy2(source, target)
        manifest_rows.append(
            "| `{}` | `{}` | {} | `{}` |".format(
                mirrored_name,
                relative_or_absolute(source, workspace),
                source.stat().st_size,
                sha256(source),
            )
        )

    manifest = destination / "MANIFEST.md"
    manifest.write_text(
        "\n".join(
            [
                "# Agent Handoff Manifest",
                "",
                f"Created (UTC): {timestamp}",
                "",
                "This directory contains only files from the latest mirrored operation.",
                "",
                "| Mirrored file | Original path | Bytes | SHA-256 |",
                "|---|---|---:|---|",
                *manifest_rows,
                "",
            ]
        ),
        encoding="utf-8",
    )

    print(f"Mirrored {len(files)} file(s) to {destination}")
    print(f"Manifest: {manifest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
