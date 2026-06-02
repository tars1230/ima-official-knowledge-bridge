---
name: ima-official-knowledge-bridge
description: |
  Call the official IMA knowledge-base QA inside the desktop app, including
  direct question asking on a personal knowledge base or a shared knowledge
  base when a shareId is known. Use this when the user wants IMA's knowledge
  base page itself, not Copilot, not OpenAPI-only list operations, and not GUI
  clicking.
---

# IMA Official Knowledge Bridge

## Scope

This skill targets the official knowledge-base page inside `ima.copilot.app`.

Use it for:

- asking a question inside a specific personal knowledge base
- reusing the same knowledge-base QA session for follow-up questions
- asking a shared knowledge base directly when `shareId` is already known
- validating a knowledge base before deciding whether to join or keep using it

Do not replace this with:

- GUI coordinate clicking
- OpenAPI pretending to be QA
- local RAG pretending to be IMA

## Current verified product facts

- Knowledge-base extension id:
  `nkohmbngmopdajidckglcoehlaeepeoi`
- Extension version verified in the local app:
  `4.27.12_0`
- Main bundle:
  `~/Library/Application Support/com.tencent.imamac/Default/Extensions/nkohmbngmopdajidckglcoehlaeepeoi/4.27.12_0/assets/index-C9nu0TtZ.js`
- Main page params include:
  - `knowledgeBaseId`
  - `shareId`
  - `folderId`
  - `question`
  - `action`
- Knowledge-base page has its own session / chat stack:
  - `SessionKnowledgePresenter`
  - `ChatListPresenter`
- The page can auto-init QA from URL params, and it can also ask through its
  own presenter methods once the session is ready.

## Stable route

The preferred route is the same pattern used for official Copilot:

1. temporary patch the official knowledge-base extension bundle
2. export the page DI container
3. open the official extension page in IMA
4. ask through the page's own presenter/store stack
5. collect the official answer text from the live section updates
6. restore the original extension files

## Scripts

- bridge JS:
  `~/.openclaw/workspace/skills/ima-official-knowledge-bridge/scripts/ima_official_knowledge_bridge.js`
- local bridge server:
  `~/.openclaw/workspace/skills/ima-official-knowledge-bridge/scripts/ima_knowledge_bridge_server.py`
- one-command wrapper:
  `~/.openclaw/workspace/skills/ima-official-knowledge-bridge/scripts/ima_knowledge_ask.py`
- candidate helper:
  `~/.openclaw/workspace/skills/ima-official-knowledge-bridge/scripts/ima_discover_candidates.py`

## One-command usage

### 1. Ask a personal knowledge base

```bash
python3 ~/.openclaw/workspace/skills/ima-official-knowledge-bridge/scripts/ima_knowledge_ask.py \
  '请基于这个知识库给我一个简短判断' \
  --knowledge-base-id '<kb_id>' \
  --timeout 120
```

### 2. Same-session follow-up

```bash
python3 ~/.openclaw/workspace/skills/ima-official-knowledge-bridge/scripts/ima_knowledge_ask.py \
  '继续追问三条最关键风险' \
  --knowledge-base-id '<kb_id>' \
  --session-id '<returned_session_id>' \
  --timeout 120
```

### 3. Ask a shared knowledge base directly without joining

When `shareId` is already known:

```bash
python3 ~/.openclaw/workspace/skills/ima-official-knowledge-bridge/scripts/ima_knowledge_ask.py \
  '这个共享知识库最擅长回答什么问题？' \
  --share-id '<share_id>' \
  --knowledge-base-id '<kb_id_if_known>' \
  --timeout 120
```

`knowledgeBaseId` is optional in share mode, but pass it when already known.

## Candidate helper

Use this to inspect owned / addable knowledge bases through official OpenAPI:

```bash
python3 ~/.openclaw/workspace/skills/ima-official-knowledge-bridge/scripts/ima_discover_candidates.py \
  --query '' \
  --limit 10
```

Addable list mode:

```bash
python3 ~/.openclaw/workspace/skills/ima-official-knowledge-bridge/scripts/ima_discover_candidates.py \
  --mode addable \
  --limit 10
```

## What this skill solves well

1. Official knowledge-base QA
2. Follow-up inside one knowledge-base QA session
3. Shared knowledge-base direct QA when `shareId` is known
4. Candidate inspection for already reachable knowledge bases

## Remaining gap

The hardest remaining gap is still:

- extracting `shareId` directly from the "发现" market search results in a
  fully automated way

That is now a narrower problem. Once `shareId` is available, this skill can ask
the shared knowledge base without joining it first.
