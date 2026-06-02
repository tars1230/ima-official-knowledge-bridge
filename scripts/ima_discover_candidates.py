#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any


IMA_API = Path.home() / ".openclaw/workspace/skills/ima-skill/ima_api.cjs"


def run_ima_api(api_path: str, body: dict[str, Any]) -> dict[str, Any]:
    proc = subprocess.run(
        ["node", str(IMA_API), api_path, json.dumps(body, ensure_ascii=False), "{}"],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr.strip() or f"ima_api failed: {api_path}")
    return json.loads(proc.stdout or "{}")


def first_list(data: Any) -> list[dict[str, Any]]:
    if isinstance(data, list):
        return [item for item in data if isinstance(item, dict)]
    if not isinstance(data, dict):
        return []
    for key in [
        "knowledge_base_list",
        "list",
        "items",
        "results",
        "knowledgeBases",
        "knowledge_base_infos",
        "data",
    ]:
        value = data.get(key)
        if isinstance(value, list):
            return [item for item in value if isinstance(item, dict)]
    return []


def first_cursor(data: Any) -> str:
    if not isinstance(data, dict):
        return ""
    for key in ["cursor", "next_cursor", "nextCursor"]:
        value = data.get(key)
        if isinstance(value, str):
            return value
    return ""


def extract_id(item: dict[str, Any]) -> str:
    for key in ["knowledge_base_id", "knowledgeBaseId", "id"]:
        value = item.get(key)
        if value is not None:
            return str(value)
    return ""


def extract_name(item: dict[str, Any]) -> str:
    for key in ["name", "knowledge_base_name", "knowledgeBaseName", "title"]:
        value = item.get(key)
        if isinstance(value, str):
            return value
    return ""


def map_candidate(base: dict[str, Any], detail: dict[str, Any] | None) -> dict[str, Any]:
    detail = detail or {}
    info = detail.get("basic_info") if isinstance(detail.get("basic_info"), dict) else {}
    permission = detail.get("permission_info") if isinstance(detail.get("permission_info"), dict) else {}
    recommended = detail.get("recommended_questions")
    if not isinstance(recommended, list):
        recommended = []
    return {
        "knowledge_base_id": extract_id(base) or extract_id(detail),
        "name": extract_name(base) or extract_name(detail) or info.get("name", ""),
        "description": detail.get("description") or info.get("description") or base.get("description", ""),
        "recommended_questions": recommended,
        "base_type": base.get("new_type") or base.get("type") or detail.get("new_type") or detail.get("type"),
        "member_count": (
            (base.get("member_info") or {}).get("memberCount")
            if isinstance(base.get("member_info"), dict)
            else base.get("member_count")
        ),
        "content_count": base.get("content_count") or base.get("knowledge_count") or detail.get("content_count"),
        "permission_info": permission,
        "raw_brief": {
            "cursor_field": base.get("cursor"),
            "has_share_info": "share" in json.dumps(base, ensure_ascii=False).lower(),
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Inspect reachable IMA knowledge-base candidates through official OpenAPI.")
    parser.add_argument("--mode", choices=["owned", "addable"], default="owned")
    parser.add_argument("--query", default="", help="Name query for owned mode. Empty string lists current reachable knowledge bases.")
    parser.add_argument("--limit", type=int, default=10)
    parser.add_argument("--cursor", default="")
    parser.add_argument("--json-only", action="store_true")
    args = parser.parse_args()

    if not IMA_API.exists():
        raise SystemExit(f"missing ima_api.cjs: {IMA_API}")

    if args.mode == "owned":
        raw = run_ima_api(
            "openapi/wiki/v1/search_knowledge_base",
            {"query": args.query, "cursor": args.cursor, "limit": args.limit},
        )
    else:
        raw = run_ima_api(
            "openapi/wiki/v1/get_addable_knowledge_base_list",
            {"cursor": args.cursor, "limit": args.limit},
        )

    data = raw.get("data") if isinstance(raw, dict) else {}
    candidates = first_list(data)
    ids = [extract_id(item) for item in candidates if extract_id(item)]
    details_map: dict[str, dict[str, Any]] = {}
    if ids:
        details_resp = run_ima_api("openapi/wiki/v1/get_knowledge_base", {"ids": ids[:20]})
        details_data = details_resp.get("data") if isinstance(details_resp, dict) else {}
        for item in first_list(details_data):
            kb_id = extract_id(item)
            if kb_id:
                details_map[kb_id] = item

    payload = {
        "mode": args.mode,
        "query": args.query,
        "cursor": first_cursor(data),
        "count": len(candidates),
        "knowledge_bases": [map_candidate(item, details_map.get(extract_id(item))) for item in candidates],
    }

    if args.json_only:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 0

    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
