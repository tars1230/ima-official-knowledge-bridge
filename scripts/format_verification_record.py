#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


def mask_value(value: str, visible: int = 6) -> str:
    if not value:
        return ""
    if len(value) <= visible:
        return value
    return f"{value[:visible]}..."


def load_payload(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def sanitize_text(text: str, max_len: int = 120) -> str:
    text = re.sub(r"\s+", " ", text).strip()
    if len(text) <= max_len:
        return text
    return text[: max_len - 3] + "..."


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Format a public-safe verification snippet from a raw bridge JSON output."
    )
    parser.add_argument("json_file", help="Path to raw JSON output captured from ima_knowledge_ask.py --raw")
    parser.add_argument("--date", default="", help="Verification date in YYYY-MM-DD.")
    parser.add_argument("--target", choices=["personal_qa", "shared_qa", "followup_qa"], default="personal_qa")
    parser.add_argument("--app-version", default="未记录")
    parser.add_argument("--extension-version", default="4.27.12_0")
    parser.add_argument("--logged-in", default="是")
    parser.add_argument("--question", default="已脱敏")
    parser.add_argument("--command", default="已脱敏；建议保留命令结构，不公开真实 ID")
    args = parser.parse_args()

    payload = load_payload(Path(args.json_file))
    final_text = sanitize_text(str(payload.get("finalText") or ""))
    session_id = mask_value(str(payload.get("sessionId") or ""))
    context = payload.get("context") if isinstance(payload.get("context"), dict) else {}
    kb_id = mask_value(str(context.get("knowledgeBaseId") or ""))
    share_id = mask_value(str(context.get("shareId") or ""))

    target_map = {
        "personal_qa": "个人知识库问答",
        "shared_qa": "共享知识库试问",
        "followup_qa": "同会话追问",
    }

    lines = [
        f"### {args.date or 'YYYY-MM-DD'}",
        "",
        "#### IMA 环境",
        "",
        f"- App 版本：{args.app_version}",
        f"- 知识库扩展版本：{args.extension_version}",
        f"- 是否已登录：{args.logged_in}",
        "",
        "#### 验证目标",
        "",
        f"- {target_map[args.target]}",
        "",
        "#### 输入",
        "",
        f"- question：{args.question}",
        f"- knowledgeBaseId：{kb_id or '已脱敏'}",
        f"- shareId：{share_id or '未使用'}",
        f"- sessionId：{session_id or '未使用'}",
        "",
        "#### 命令",
        "",
        "```bash",
        args.command,
        "```",
        "",
        "#### 结果",
        "",
        f"- 是否成功：{'是' if payload.get('ok') else '否'}",
        f"- finalText：{final_text or '空'}",
        f"- sessionId：{session_id or '空'}",
        f"- sessionReused：{'true' if payload.get('sessionReused') else 'false'}",
        "",
        "#### 备注",
        "",
        "- 本记录默认对知识库 ID、shareId、sessionId 做截断脱敏",
        "- 建议只公开可以安全展示的问题与回答",
        "- 如涉及私有知识库正文，请保留验证结构，不公开原始内容",
    ]

    print("\n".join(lines))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
