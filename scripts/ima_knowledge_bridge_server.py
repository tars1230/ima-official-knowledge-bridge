#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any


class State:
    def __init__(self, question: str, timeout: int, max_events: int, session_id: str) -> None:
        self.job = {
            "id": f"job-{int(time.time())}",
            "question": question,
            "maxEvents": max_events,
            "mode": "official-knowledge",
        }
        if session_id:
            self.job["sessionId"] = session_id
        self.result: dict[str, Any] | None = None
        self.timeout = timeout
        self.job_claimed = False


def summarize_result(result: dict[str, Any]) -> dict[str, Any]:
    if not result.get("ok"):
        return {"ok": False, "error": result.get("error", "")}
    payload = result.get("result") or {}
    events = payload.get("events") or []
    return {
        "ok": True,
        "bridgeVersion": payload.get("bridgeVersion"),
        "finalText": payload.get("finalText", ""),
        "sessionId": payload.get("sessionId"),
        "sessionIdPresent": payload.get("sessionIdPresent"),
        "sessionReused": payload.get("sessionReused"),
        "authShape": payload.get("authShape"),
        "currentUrl": payload.get("currentUrl"),
        "context": payload.get("context"),
        "finalSectionSummary": payload.get("finalSectionSummary"),
        "eventsSeen": [
            {
                "event": item.get("event"),
                "contentPreview": item.get("data", {}).get("contentPreview", "")
                if isinstance(item.get("data"), dict)
                else "",
                "isFinish": item.get("data", {}).get("isFinish")
                if isinstance(item.get("data"), dict)
                else None,
                "sectionId": item.get("data", {}).get("sectionId")
                if isinstance(item.get("data"), dict)
                else None,
                "closeMsg": item.get("data", {}).get("closeMsg")
                if isinstance(item.get("data"), dict)
                else None,
                "errorCode": item.get("data", {}).get("errorCode")
                if isinstance(item.get("data"), dict)
                else None,
            }
            for item in events[:40]
        ],
    }


def make_handler(state: State):
    class Handler(BaseHTTPRequestHandler):
        server_version = "IMAKnowledgeBridge/0.1"

        def _send(self, status: int, data: bytes = b"", content_type: str = "application/json") -> None:
            self.send_response(status)
            self.send_header("access-control-allow-origin", "*")
            self.send_header("access-control-allow-methods", "GET, POST, OPTIONS")
            self.send_header("access-control-allow-headers", "content-type")
            self.send_header("cache-control", "no-store")
            if data:
                self.send_header("content-type", content_type)
                self.send_header("content-length", str(len(data)))
            self.end_headers()
            if data:
                self.wfile.write(data)

        def log_message(self, fmt: str, *args: Any) -> None:
            return

        def do_OPTIONS(self) -> None:
            self._send(204)

        def do_GET(self) -> None:
            if self.path == "/job":
                if state.job_claimed:
                    self._send(204)
                    return
                state.job_claimed = True
                self._send(200, json.dumps(state.job, ensure_ascii=False).encode("utf-8"))
                return
            if self.path == "/health":
                self._send(200, b'{"ok":true}')
                return
            self._send(404, b'{"error":"not found"}')

        def do_POST(self) -> None:
            if self.path != "/result":
                self._send(404, b'{"error":"not found"}')
                return
            length = int(self.headers.get("content-length") or "0")
            raw = self.rfile.read(length)
            try:
                state.result = json.loads(raw.decode("utf-8"))
            except Exception as exc:
                state.result = {"ok": False, "error": f"invalid result json: {exc}"}
            self._send(200, b'{"ok":true}')

    return Handler


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--question", default="请用一句中文短句回答：知识库问答桥已收到吗？")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=19795)
    parser.add_argument("--timeout", type=int, default=90)
    parser.add_argument("--max-events", type=int, default=80)
    parser.add_argument("--session-id", default="")
    args = parser.parse_args()

    state = State(args.question, args.timeout, args.max_events, args.session_id)
    server = ThreadingHTTPServer((args.host, args.port), make_handler(state))
    server.timeout = 1
    deadline = time.time() + args.timeout
    print(json.dumps({"server": f"http://{args.host}:{args.port}", "job_id": state.job["id"]}, ensure_ascii=False))
    while time.time() < deadline and state.result is None:
        server.handle_request()
    server.server_close()
    if state.result is None:
        print(
            json.dumps(
                {"ok": False, "error": "timeout waiting for bridge result", "job_claimed": state.job_claimed},
                ensure_ascii=False,
                indent=2,
            )
        )
        return 2
    print(json.dumps(summarize_result(state.result), ensure_ascii=False, indent=2))
    return 0 if state.result.get("ok") else 3


if __name__ == "__main__":
    raise SystemExit(main())
