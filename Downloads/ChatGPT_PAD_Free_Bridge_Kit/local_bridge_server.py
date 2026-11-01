#!/usr/bin/env python3
"""Loopback transport for the existing Invoke-ChatGPTBridge.ps1 file protocol.

No ChatGPT API/credentials, no PAD, no automatic controller/checkpoint mutation.
Uses standard-library Python only. Stores immutable request claims to fail closed
on reloads, stale browser tabs and process restarts.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import secrets
import tempfile
import threading
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

HANDOFF = re.compile(r"^\s*\[BRIDGE_HANDOFF_ID=(HND-[A-Za-z0-9_-]{1,100})\]\s*$", re.M)
CLIENT = re.compile(r"^[A-Za-z0-9_-]{12,100}$")
MAX_RESPONSE_BYTES = 200_000
MAX_REQUEST_BYTES = 200_000


def sha(data: str) -> str:
    return hashlib.sha256(data.encode("utf-8")).hexdigest()


def atomic_json(path: Path, obj: dict):
    path.parent.mkdir(parents=True, exist_ok=True)
    data = json.dumps(obj, ensure_ascii=False, indent=2).encode("utf-8")
    # Write a unique temp file and atomically publish it; no overwrite of a receipt.
    with tempfile.NamedTemporaryFile(prefix=path.name + ".", suffix=".tmp", dir=path.parent, delete=False) as f:
        temp = Path(f.name)
        f.write(data)
        f.flush()
        os.fsync(f.fileno())
    try:
        # Exclusive publication even across processes; exists()+replace() races.
        os.link(temp, path)
    finally:
        temp.unlink(missing_ok=True)


def clean_json_reply(raw: str) -> dict:
    s = raw.strip()
    m = re.fullmatch(r"```(?:json)?\s*\n([\s\S]*?)\n```", s, flags=re.I)
    if m:
        s = m.group(1).strip()
    obj = json.loads(s)
    if not isinstance(obj, dict):
        raise ValueError("Expected a single JSON object")
    return obj


class State:
    def __init__(self, root: Path, token: str):
        self.root = root.resolve()
        self.token = token
        self.control = self.root / "direct_bridge"
        self.control.mkdir(parents=True, exist_ok=True)
        self.mutex = threading.RLock()

    def active(self):
        request = self.root / "bridge_request.ready"
        lock = self.root / "bridge.lock"
        if not request.exists() or not lock.exists():
            return None
        try:
            prompt = request.read_text(encoding="utf-8-sig")
            if len(prompt.encode("utf-8")) > MAX_REQUEST_BYTES:
                raise ValueError("Bridge prompt exceeds size limit")
            m = HANDOFF.search(prompt)
            if not m:
                raise ValueError("Missing exact HND handoff marker")
            meta = json.loads(lock.read_text(encoding="utf-8-sig"))
            if meta.get("bridge_handoff_id") != m.group(1):
                raise ValueError("Bridge lock ID does not match pending request")
            return {"handoff_id": m.group(1), "prompt": prompt, "request_sha256": sha(prompt)}
        except (OSError, json.JSONDecodeError, ValueError) as e:
            raise ValueError(f"Invalid active bridge transaction: {e}") from e

    def claim_file(self, handoff_id):
        return self.control / "claims" / (handoff_id + ".json")

    def receipt_file(self, handoff_id):
        return self.control / "receipts" / (handoff_id + ".json")

    def intent_file(self, handoff_id):
        return self.control / "publish_intents" / (handoff_id + ".json")

    def next(self, client_id: str) -> tuple[int, dict]:
        if not CLIENT.fullmatch(client_id):
            return 400, {"status": "ERROR", "error": "INVALID_CLIENT_ID"}
        with self.mutex:
            tx = self.active()
            if tx is None:
                return 200, {"status": "IDLE"}
            ident = tx["handoff_id"]
            if self.receipt_file(ident).exists():
                return 200, {"status": "DELIVERED", "handoff_id": ident}
            if self.intent_file(ident).exists():
                return 409, {"status": "BLOCKED", "error": "UNCERTAIN_RESPONSE_PUBLICATION"}
            path = self.claim_file(ident)
            if path.exists():
                claim = json.loads(path.read_text(encoding="utf-8"))
                if claim.get("request_sha256") != tx["request_sha256"]:
                    return 409, {"status": "BLOCKED", "error": "CLAIM_REQUEST_CHANGED", "handoff_id": ident}
                if claim.get("client_id") != client_id:
                    return 200, {"status": "HELD_BY_OTHER_BROWSER", "handoff_id": ident}
            else:
                atomic_json(path, {"handoff_id": ident, "client_id": client_id,
                                   "request_sha256": tx["request_sha256"],
                                   "claimed_at": datetime.now(timezone.utc).isoformat()})
            return 200, {"status": "READY", **tx}

    def submit(self, body: dict) -> tuple[int, dict]:
        ident = body.get("handoff_id")
        client = body.get("client_id")
        digest = body.get("request_sha256")
        raw = body.get("response")
        if not isinstance(ident, str) or not HANDOFF.fullmatch(f"[BRIDGE_HANDOFF_ID={ident}]"):
            return 400, {"status": "ERROR", "error": "INVALID_HANDOFF_ID"}
        if not isinstance(raw, str) or len(raw.encode("utf-8")) > MAX_RESPONSE_BYTES or not raw.strip():
            return 400, {"status": "ERROR", "error": "INVALID_RESPONSE"}
        with self.mutex:
            tx = self.active()
            if not tx or tx["handoff_id"] != ident or tx["request_sha256"] != digest:
                return 409, {"status": "BLOCKED", "error": "STALE_OR_CHANGED_REQUEST"}
            path = self.claim_file(ident)
            if not path.exists():
                return 409, {"status": "BLOCKED", "error": "MISSING_CLIENT_CLAIM"}
            claim = json.loads(path.read_text(encoding="utf-8"))
            if claim.get("client_id") != client or claim.get("request_sha256") != digest:
                return 409, {"status": "BLOCKED", "error": "CLIENT_OWNERSHIP_MISMATCH"}
            if (self.receipt_file(ident).exists() or self.intent_file(ident).exists() or
                    (self.root / "bridge_response.ready").exists()):
                return 409, {"status": "BLOCKED", "error": "RESPONSE_ALREADY_PUBLISHED"}
            if "CHATGPT_SUPERVISOR_V1" in tx["prompt"]:
                try:
                    reply = clean_json_reply(raw)
                except (ValueError, json.JSONDecodeError):
                    return 422, {"status": "ERROR", "error": "SUPERVISOR_RESPONSE_NOT_JSON"}
                if reply.get("correlation_id") != ident:
                    return 422, {"status": "ERROR", "error": "SUPERVISOR_STALE_RESPONSE"}
                if reply.get("action") not in ("CONTINUE", "DIAGNOSE", "WAIT", "STOP"):
                    return 422, {"status": "ERROR", "error": "SUPERVISOR_INVALID_ACTION"}
                if not isinstance(reply.get("instruction"), str) or not reply["instruction"].strip():
                    return 422, {"status": "ERROR", "error": "SUPERVISOR_EMPTY_INSTRUCTION"}
            wire = {"bridge_handoff_id": ident, "status": "OK", "response": raw,
                    "response_chars": len(raw), "copied_at": datetime.now(timezone.utc).isoformat(),
                    "transport": "direct-local-bridge-v1"}
            response_path = self.root / "bridge_response.ready"
            # An immutable publish intent is written BEFORE the response.
            # Crash between intent and ready => block/reconcile, not repeat.
            atomic_json(self.intent_file(ident), {
                "handoff_id": ident, "client_id": client,
                "request_sha256": digest, "response_sha256": sha(raw),
                "intent_at": datetime.now(timezone.utc).isoformat()})
            # Existing Invoke-ChatGPTBridge.ps1 waits for bridge_response.ready.
            # It archives and removes that file; do not alter its lock/session policy.
            atomic_json(response_path, wire)
            atomic_json(self.receipt_file(ident), {"handoff_id": ident, "client_id": client,
                        "request_sha256": digest, "response_sha256": sha(raw),
                        "published_at": datetime.now(timezone.utc).isoformat()})
            return 200, {"status": "ACCEPTED", "handoff_id": ident, "response_sha256": sha(raw)}


def make_handler(state: State):
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, fmt, *args):
            # No prompt, response, token or credential content in HTTP logs.
            print("[loopback]", self.address_string(), fmt % args, flush=True)

        def answer(self, code: int, data: dict):
            b = json.dumps(data, ensure_ascii=False).encode("utf-8")
            self.send_response(code)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.send_header("Content-Length", str(len(b)))
            self.end_headers()
            self.wfile.write(b)

        def authorized(self):
            if self.headers.get("X-Bridge-Token", "") != state.token:
                self.answer(403, {"status": "ERROR", "error": "FORBIDDEN"})
                return False
            origin = self.headers.get("Origin", "")
            if origin and origin != "https://chatgpt.com":
                self.answer(403, {"status": "ERROR", "error": "INVALID_ORIGIN"})
                return False
            return True

        def do_GET(self):
            if not self.authorized():
                return
            u = urlsplit(self.path)
            if u.path == "/health":
                self.answer(200, {"status": "OK", "transport": "direct-local-bridge-v1"})
                return
            if u.path != "/next":
                self.answer(404, {"status": "ERROR", "error": "UNKNOWN_ENDPOINT"})
                return
            try:
                client = parse_qs(u.query).get("client_id", [""])[0]
                code, data = state.next(client)
                self.answer(code, data)
            except Exception as e:
                self.answer(409, {"status": "BLOCKED", "error": type(e).__name__})

        def do_POST(self):
            if not self.authorized():
                return
            if urlsplit(self.path).path != "/response":
                self.answer(404, {"status": "ERROR", "error": "UNKNOWN_ENDPOINT"})
                return
            try:
                length = int(self.headers.get("Content-Length", "0"))
                if length < 1 or length > MAX_RESPONSE_BYTES + 4096:
                    self.answer(413, {"status": "ERROR", "error": "INVALID_BODY_SIZE"})
                    return
                body = json.loads(self.rfile.read(length).decode("utf-8"))
                if not isinstance(body, dict):
                    raise ValueError("Expected JSON object")
                code, data = state.submit(body)
                self.answer(code, data)
            except (ValueError, UnicodeError, json.JSONDecodeError):
                self.answer(400, {"status": "ERROR", "error": "INVALID_JSON_BODY"})
            except Exception as e:
                self.answer(409, {"status": "BLOCKED", "error": type(e).__name__})
    return Handler


def main():
    parser = argparse.ArgumentParser(description="PAD-free ChatGPT Tampermonkey loopback bridge")
    parser.add_argument("--bridge-dir", type=Path,
                        default=Path(os.environ.get("USERPROFILE") or Path.home()) / "OpenClawPAD" / "ChatGPTBridge")
    parser.add_argument("--port", type=int, default=8765)
    args = parser.parse_args()
    root = args.bridge_dir.expanduser().resolve()
    root.mkdir(parents=True, exist_ok=True)
    token_path = root / "direct_bridge" / "secret.txt"
    token_path.parent.mkdir(parents=True, exist_ok=True)
    if not token_path.exists():
        with token_path.open("x", encoding="utf-8") as f:
            f.write(secrets.token_urlsafe(36))
        try:
            os.chmod(token_path, 0o600)
        except OSError:
            pass
    token = token_path.read_text(encoding="utf-8").strip()
    if len(token) < 40:
        raise RuntimeError("Weak or empty bridge token; inspect the local secret file")
    state = State(root, token)
    server = ThreadingHTTPServer(("127.0.0.1", args.port), make_handler(state))
    print(f"PAD-FREE bridge listening only on http://127.0.0.1:{args.port}")
    print(f"Token file: {token_path} (paste its content in the userscript locally; NEVER share it)")
    print("No HPC actions. Preserve pending supervisor records and original controller checkpoints.", flush=True)
    try:
        server.serve_forever(poll_interval=0.5)
    except KeyboardInterrupt:
        print("Stopping bridge")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
