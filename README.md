# IMA Official Knowledge Bridge

Programmatic bridge for the official Tencent IMA desktop app knowledge-base QA.

This repository provides a practical, automation-friendly path for working with
the **official IMA knowledge-base page inside `ima.copilot.app`**.

Instead of relying on GUI clicking, screenshot coordinates, or a local RAG
substitute, it aims to drive the official product surface more directly and
more predictably.

## Highlights

- Official knowledge-base QA bridge for personal knowledge bases
- Same-session follow-up support
- Shared knowledge-base direct QA when a valid `shareId` is already known
- Candidate inspection through IMA OpenAPI
- Temporary patch / restore flow instead of permanent extension modification

This project targets the **official IMA knowledge-base page inside `ima.copilot.app`** and focuses on a narrow, practical goal:

- ask a question inside a specific personal knowledge base
- reuse the same knowledge-base QA session for follow-up questions
- ask a shared knowledge base directly when a valid `shareId` is already known
- inspect reachable knowledge-base candidates through IMA OpenAPI

It is designed for users who want a more stable alternative to GUI clicking, screenshot automation, or local RAG pretending to be IMA.

## Status

Current maturity:

- The repository structure, scripts, and skill entrypoint are in place.
- Static validation has passed for the Python and JavaScript bridge files.
- The bridge is built around the official IMA knowledge-base extension page and its internal presenter/session stack.
- Live end-to-end validation still depends on having a real `knowledgeBaseId` or `shareId` available in the target IMA account.

So the honest status is:

- **architecture and implementation are ready**
- **real-world execution requires valid IMA context**

## Project Goals

This project is intentionally narrow.

Primary goals:

- make official IMA knowledge-base QA callable from automation
- preserve session continuity for follow-up questions
- reduce brittle desktop automation
- keep the implementation inspectable and easy to adapt

Non-goals:

- broad reverse-engineering of unrelated IMA features
- bypassing account, permission, or product restrictions
- pretending that OpenAPI-only operations are equivalent to official QA

## What This Is

This repository contains:

- a skill entrypoint: [`SKILL.md`](./SKILL.md)
- a temporary extension bridge injector
- a local bridge server
- a one-command wrapper for official knowledge-base QA
- a candidate inspector for reachable knowledge bases

Main scripts:

- [`scripts/ima_knowledge_ask.py`](./scripts/ima_knowledge_ask.py)
- [`scripts/ima_official_knowledge_bridge.js`](./scripts/ima_official_knowledge_bridge.js)
- [`scripts/ima_knowledge_bridge_server.py`](./scripts/ima_knowledge_bridge_server.py)
- [`scripts/ima_discover_candidates.py`](./scripts/ima_discover_candidates.py)

## What This Is Not

This project does **not** aim to be:

- a general-purpose IMA reverse-engineering toolkit
- a GUI automation package
- an unofficial cloud service for IMA
- a substitute for valid IMA account access

It also does not claim that all IMA "发现" shared knowledge-base flows are already fully automated. The main remaining gap is still **automatic extraction of a usable `shareId` from discovery results**.

## Architecture

The preferred route is:

1. temporarily patch the official IMA knowledge-base extension
2. export the page DI container
3. open the official extension page inside the IMA app
4. ask through the page's own presenter/store stack
5. collect the final answer from official section updates
6. restore the original extension files

This keeps the control surface close to the real product behavior instead of trying to fake it from the outside.

At a high level:

- `ima_knowledge_ask.py` is the main entry wrapper
- `ima_knowledge_bridge_server.py` hosts the short-lived local control channel
- `ima_official_knowledge_bridge.js` runs inside the official knowledge-base page
- `ima_discover_candidates.py` helps inspect reachable knowledge-base candidates

## Requirements

Environment assumptions:

- macOS
- Tencent IMA desktop app installed
- logged-in IMA desktop session
- local access to the IMA extension directory under:
  `~/Library/Application Support/com.tencent.imamac/Default/Extensions/`
- Python 3
- Node.js

Optional but useful:

- valid IMA OpenAPI credentials for candidate inspection

## Installation

This repository is currently structured as a Codex/OpenClaw skill folder.

If you want to use it as a standalone local repository:

1. clone or copy this repository to a local directory
2. keep the relative layout unchanged
3. ensure Python 3 and Node are available
4. update any absolute paths in your own automation layer if needed

No package installation step is required for the current scripts.

## Quick Start

### Ask a personal knowledge base

```bash
python3 scripts/ima_knowledge_ask.py \
  '请基于这个知识库给我一个简短判断' \
  --knowledge-base-id '<kb_id>' \
  --timeout 120
```

### Reuse the same session

```bash
python3 scripts/ima_knowledge_ask.py \
  '继续追问三条最关键风险' \
  --knowledge-base-id '<kb_id>' \
  --session-id '<returned_session_id>' \
  --timeout 120
```

## Usage

### 1. Ask a personal knowledge base

```bash
python3 scripts/ima_knowledge_ask.py \
  '请基于这个知识库给我一个简短判断' \
  --knowledge-base-id '<kb_id>' \
  --timeout 120
```

### 2. Reuse the same knowledge-base session

```bash
python3 scripts/ima_knowledge_ask.py \
  '继续追问三条最关键风险' \
  --knowledge-base-id '<kb_id>' \
  --session-id '<returned_session_id>' \
  --timeout 120
```

### 3. Ask a shared knowledge base directly

```bash
python3 scripts/ima_knowledge_ask.py \
  '这个共享知识库最擅长回答什么问题？' \
  --share-id '<share_id>' \
  --knowledge-base-id '<kb_id_if_known>' \
  --timeout 120
```

### 4. Inspect reachable knowledge-base candidates

```bash
python3 scripts/ima_discover_candidates.py \
  --query '' \
  --limit 10
```

Addable list mode:

```bash
python3 scripts/ima_discover_candidates.py \
  --mode addable \
  --limit 10
```

## Safety Notes

- The bridge uses **temporary patching** of the local IMA extension files.
- The wrapper restores original files in `finally`.
- You should still avoid running multiple overlapping bridge calls against the same extension page at the same time.
- Placeholder values such as fake `shareId` inputs are rejected on purpose to avoid long, meaningless waits.

## Limitations

Known limitations:

- discovery-market `shareId` extraction is not yet fully automated
- live success depends on a valid logged-in local IMA context
- extension version changes may require maintenance
- this currently targets a verified local extension version rather than every future IMA release

## Repository Layout

```text
.
├── README.md
├── SKILL.md
├── LICENSE
├── .gitignore
├── references/
└── scripts/
    ├── ima_discover_candidates.py
    ├── ima_knowledge_ask.py
    ├── ima_knowledge_bridge_server.py
    └── ima_official_knowledge_bridge.js
```

## Roadmap

Near-term improvements:

- add one verified live transcript example
- add a reproducible troubleshooting section for common local failures
- narrow the gap around discovery-market `shareId` extraction
- add version compatibility notes as the IMA extension evolves

## Recommended Next Step

The most valuable next milestone is:

- run a fresh live validation with a real `knowledgeBaseId` or real `shareId`
- capture one successful transcript
- add a short verification note under `references/`

That will turn the project from "well-structured bridge" into "well-structured bridge with reproducible live evidence".
