#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import socket
import subprocess
import sys
import time
from pathlib import Path
from typing import Final
from urllib.parse import urlencode


ROOT = Path(__file__).resolve().parents[1]
BRIDGE_JS = ROOT / "scripts" / "ima_official_knowledge_bridge.js"
SERVER = ROOT / "scripts" / "ima_knowledge_bridge_server.py"
DEFAULT_APP_PATH = Path("/Applications/ima.copilot.app")
EXTENSION_ID = "nkohmbngmopdajidckglcoehlaeepeoi"
EXTENSION_DIR = (
    Path.home()
    / "Library/Application Support/com.tencent.imamac/Default/Extensions"
    / EXTENSION_ID
    / "4.27.12_0"
)
EXTENSION_INDEX = EXTENSION_DIR / "index.html"
EXTENSION_BUNDLE = EXTENSION_DIR / "assets" / "index-C9nu0TtZ.js"
PATCHED_INDEX_SNIPPET: Final[str] = '\n    <script src="/ima-kb-codex-bridge.js"></script>'
DI_EXPORT_SNIPPET: Final[str] = 'globalThis.__IMA_KB_CODEX_DI__={container:A,tokens:h};'


def free_port(start: int = 19795, stop: int = 19860) -> int:
    for port in range(start, stop):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            try:
                sock.bind(("127.0.0.1", port))
            except OSError:
                continue
            return port
    raise RuntimeError(f"no free localhost port in {start}-{stop - 1}")


def run(cmd: list[str], *, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=check)


def resolve_app_path() -> Path:
    candidates = [
        DEFAULT_APP_PATH,
        Path("/Volumes/MacWorkCache2/chengchen/app-support/apps/ima.copilot.app"),
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    raise SystemExit(f"missing IMA app, checked: {', '.join(str(path) for path in candidates)}")


def patch_index(index_text: str) -> str:
    if 'src="/ima-kb-codex-bridge.js"' in index_text:
        return index_text
    script_tag = '<script type="module" crossorigin src="/assets/index-C9nu0TtZ.js"></script>'
    if script_tag in index_text:
        return index_text.replace(script_tag, f"{PATCHED_INDEX_SNIPPET}\n{script_tag}", 1)
    raise RuntimeError("unable to patch knowledge index.html with bridge script")


def patch_bundle(bundle_text: str) -> str:
    if "__IMA_KB_CODEX_DI__" in bundle_text:
        return bundle_text
    marker = "A.snapshot();"
    if marker not in bundle_text:
        raise RuntimeError("unable to patch knowledge bundle with DI export")
    return bundle_text.replace(marker, f"{DI_EXPORT_SNIPPET}{marker}", 1)


def parse_last_json(stdout: str) -> dict:
    decoder = json.JSONDecoder()
    last: dict | None = None
    index = 0
    while index < len(stdout):
        while index < len(stdout) and stdout[index].isspace():
            index += 1
        if index >= len(stdout):
            break
        try:
            value, end = decoder.raw_decode(stdout[index:])
        except json.JSONDecodeError:
            next_newline = stdout.find("\n", index)
            if next_newline < 0:
                break
            index = next_newline + 1
            continue
        if isinstance(value, dict):
            last = value
        index += end
    if last is None:
        raise RuntimeError(f"server did not print JSON result:\n{stdout}")
    return last


def build_extension_url(port: int, knowledge_base_id: str, share_id: str, folder_id: str) -> str:
    params = {
        "codex_reload": str(int(time.time())),
        "bridge": str(port),
    }
    if knowledge_base_id:
        params["knowledgeBaseId"] = knowledge_base_id
    if share_id:
        params["shareId"] = share_id
    if folder_id:
        params["folderId"] = folder_id
    return f"chrome-extension://{EXTENSION_ID}/index.html?{urlencode(params)}"


def main() -> int:
    parser = argparse.ArgumentParser(description="Ask the official IMA knowledge-base QA through the verified page bridge.")
    parser.add_argument("question", nargs="?", default="请用一句中文短句回答：知识库问答桥已收到吗？")
    parser.add_argument("--knowledge-base-id", default="", help="Target personal knowledgeBaseId.")
    parser.add_argument("--share-id", default="", help="Target shared knowledge shareId for direct QA without joining.")
    parser.add_argument("--folder-id", default="", help="Optional folderId within the knowledge base.")
    parser.add_argument("--session-id", default="", help="Reuse an existing knowledge-base QA session for follow-up questions.")
    parser.add_argument("--port", type=int, default=0, help="Local bridge port. Default: auto-pick from 19795.")
    parser.add_argument("--timeout", type=int, default=120)
    parser.add_argument("--open-wait", type=float, default=1.5)
    parser.add_argument("--raw", action="store_true", help="Print the full server summary instead of compact output.")
    args = parser.parse_args()

    if not args.knowledge_base_id and not args.share_id:
        raise SystemExit("knowledge-base ask requires --knowledge-base-id or --share-id")
    if args.share_id and args.share_id.startswith("test-"):
        raise SystemExit("share-id looks like a placeholder; pass a real IMA shareId")
    if not BRIDGE_JS.exists():
        raise SystemExit(f"missing bridge JS: {BRIDGE_JS}")
    if not SERVER.exists():
        raise SystemExit(f"missing bridge server: {SERVER}")
    if not EXTENSION_DIR.exists():
        raise SystemExit(f"missing IMA knowledge extension dir: {EXTENSION_DIR}")
    app_path = resolve_app_path()

    port = args.port or free_port()
    target_bridge = EXTENSION_DIR / "ima-kb-codex-bridge.js"
    original_index = EXTENSION_INDEX.read_text(encoding="utf-8")
    original_bundle = EXTENSION_BUNDLE.read_text(encoding="utf-8")
    patched_index = patch_index(original_index)
    patched_bundle = patch_bundle(original_bundle)
    bridge_exists_before = target_bridge.exists()
    bridge_backup = target_bridge.read_text(encoding="utf-8") if bridge_exists_before else None

    try:
        target_bridge.write_text(BRIDGE_JS.read_text(encoding="utf-8"), encoding="utf-8")
        EXTENSION_INDEX.write_text(patched_index, encoding="utf-8")
        EXTENSION_BUNDLE.write_text(patched_bundle, encoding="utf-8")

        url = build_extension_url(port, args.knowledge_base_id, args.share_id, args.folder_id)
        open_proc = run(["open", "-a", str(app_path), url], check=False)
        if open_proc.returncode != 0:
            raise SystemExit(open_proc.stderr.strip() or "failed to open IMA app")

        time.sleep(args.open_wait)
        server_proc = run(
            [
                sys.executable,
                str(SERVER),
                "--port",
                str(port),
                "--timeout",
                str(args.timeout),
                "--session-id",
                args.session_id,
                "--question",
                args.question,
            ],
            check=False,
        )
        if server_proc.returncode != 0:
            print(server_proc.stdout, end="")
            print(server_proc.stderr, end="", file=sys.stderr)
            return server_proc.returncode

        result = parse_last_json(server_proc.stdout)
        if args.raw:
            print(json.dumps(result, ensure_ascii=False, indent=2))
            return 0 if result.get("ok") and result.get("finalText") else 3

        compact = {
            "ok": result.get("ok"),
            "port": port,
            "bridgeVersion": result.get("bridgeVersion"),
            "finalText": result.get("finalText"),
            "sessionId": result.get("sessionId"),
            "officialKnowledge": bool((result.get("authShape") or {}).get("officialKnowledge")),
            "sessionIdPresent": result.get("sessionIdPresent"),
            "sessionReused": bool(result.get("sessionReused")),
            "context": result.get("context"),
        }
        print(json.dumps(compact, ensure_ascii=False, indent=2))
        return 0 if compact["ok"] and compact["finalText"] and compact["officialKnowledge"] else 3
    finally:
        EXTENSION_INDEX.write_text(original_index, encoding="utf-8")
        EXTENSION_BUNDLE.write_text(original_bundle, encoding="utf-8")
        if bridge_exists_before and bridge_backup is not None:
            target_bridge.write_text(bridge_backup, encoding="utf-8")
        else:
            target_bridge.unlink(missing_ok=True)


if __name__ == "__main__":
    os.environ.pop("PYTHONINSPECT", None)
    raise SystemExit(main())
