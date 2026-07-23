# ACSP · Agentic Customer Service Pipeline

**A Zero-Trust Model Context Protocol (MCP) Control Plane for Regulated Financial AI**

[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![MCP Control Plane](https://img.shields.io/badge/MCP-control%20plane-0B6E4F.svg)](#architecture-at-a-glance)
[![AAIF Ambassadorship](https://img.shields.io/badge/AAIF-ambassadorship%20contribution-6f42c1.svg)](#built-as-an-aaif-ambassadorship-contribution)
[![License](https://img.shields.io/badge/license-see%20LICENSE-lightgrey.svg)](LICENSE)

Prototype for banking/wallet customer service: agents reason in natural language; **enterprise truth and side effects only cross MCP**.

---

## The Core Rule

> **The model proposes. The platform tokenizes, authorizes, executes, and audits.**

Standard desktop MCP demos often wire an LLM straight to tools with global discovery and prompt-only safety. That is not enough for fintech:

| Playground MCP | ACSP Zero-Trust Control Plane |
|----------------|-------------------------------|
| Global auto-discovery of tools | **Intent-scoped manifests** (`tool_permissions.yaml`) |
| Raw PII / secrets in model context | **Spatial tokenization** before the LLM (`[ACC_A1B2]`) |
| Identity trusted from the prompt | **Platform-injected** `customerContext` |
| Writes as “just another tool call” | **OTP step-up** on state-modifying tools |
| Failures as free text | Structured statuses: `SUCCESS` / `ERROR` / `UNAUTHORIZED` / `UNAVAILABLE` |

```text
       Traditional Agent                      ACSP Zero-Trust Control Plane
┌───────────────────────────────┐          ┌───────────────────────────────────┐
│ LLM ──► Direct DB / Raw Tools │    VS    │ LLM Proposes ──► Tokenizer Vault  │
│       (Prompt-only Safety)    │          │              ──► Intent Manifest  │
└───────────────────────────────┘          │              ──► MCP Execution    │
                                           │              ──► OTP + Audit      │
                                           └───────────────────────────────────┘
```

> [!IMPORTANT]
> Agents never import SQL, the vector store, or domain services.  
> The sole enterprise interface is `POST /mcp/v1/tools/invoke` on the MCP server (`:8001`).  
> **MCP calls are intent-scoped** — the customer reply uses only results from tools allowed for that intent.

---

## Architecture at a Glance

End-to-end lifecycle: **user input → tokenize → LLM proposes → Worker authorizes → MCP executes (RAG or domain) → grounded reply**.

![ACSP Zero-Trust Control Plane](docs/assets/zero-trust-control-plane.png)

```text
 Customer / web chat
        │
        ▼
 ┌──────────────────────────────────────────────────────────┐
 │  Orchestrator  (LLM proposes tool calls)                 │
 │  tokenize PII → vault  ·  intent scope  ·  tool loop     │
 └────────────────────────────┬─────────────────────────────┘
                              │ proposed tools (tokenized args)
                              ▼
 ┌──────────────────────────────────────────────────────────┐
 │  Worker McpClient   worker/mcp_client.py (per intent)    │
 │  [ Manifest check ] [ Inject customerContext ] [ Cap ]   │  ← client enforcement
 └────────────────────────────┬─────────────────────────────┘
                              │ POST /mcp/v1/tools/invoke
                              │ HTTP boundary (scale + isolation)
                              ▼
 ┌──────────────────────────────────────────────────────────┐
 │  MCP Server   mcp/server.py  (:8001)                     │
 │  [ Validate ] [ Resolve tool ] [ Invoke ] [ Audit log ]  │  ← server execution
 └───────┬──────────────────┬──────────────────┬────────────┘
         │                  │                  │
         ▼                  ▼                  ▼
   RAG / Knowledge     Account reads      Writes (OTP)
   search_knowledge_   balance · history  freeze · P2P
   base                (customer-scoped)  transfer
         │
         ▼
 ┌──────────────────────────────────────────────────────────┐
 │  Knowledge / RAG  (behind MCP only — not agent-callable) │
 │  sources/ → load → chunk → embed/index (Chroma)          │
 │           → hybrid retrieve (semantic ~70% + keyword)    │
 │           → ranked excerpts in MCP data payload          │
 └────────────────────────────┬─────────────────────────────┘
                              │
              Structured status: SUCCESS | ERROR | UNAUTHORIZED | UNAVAILABLE
                              │
                              ▼
              Orchestrator replies from intent-allowed MCP results
              (e.g. GENERAL_INQUIRY → search_knowledge_base / RAG only)
                              │
                              ▼
                       Customer / web chat
```

| Stage | Who | Responsibility |
|-------|-----|----------------|
| **1. Ingress** | Chat UI / Gateway | Capture message, `sessionId`, `correlationId` |
| **2. Privacy** | Tokenizer | Replace PII with `[ACC_…]`; redact secrets before the LLM |
| **3. Propose** | Orchestrator + LLM | Classify intent; propose tool calls on **tokenized** context only |
| **4. Authorize** | Worker MCP client | Manifest allow-list **for that intent**, inject `customerContext`, rehydrate args, enforce invocation budget |
| **5. Execute** | MCP server `:8001` | Validate envelope, resolve registry, run handler, masked audit |
| **6a. RAG** | `search_knowledge_base` → `knowledge/` | Only when intent permits it; hybrid retrieve → ranked excerpts in MCP `data` |
| **6b. Domain** | Account / transfer tools | Only when intent permits it; reads = customer-scoped; writes = OTP + ownership |
| **7. Respond** | Orchestrator → UI | Answer from **intent-scoped** MCP results (RAG or domain) — never from tools outside the manifest |

### RAG path (`GENERAL_INQUIRY`)

Policy answers are **not** free-form model memory. Offline, docs in `knowledge/sources/` are loaded, chunked, and indexed into Chroma (`.knowledge/chroma`). Online, intent `GENERAL_INQUIRY` loads a manifest that allows **only** `search_knowledge_base`; MCP runs hybrid retrieval and returns evidence; the assistant reply (and workbench `via …` chip) is built from that payload.

```text
knowledge/sources/*.md → chunk/index (Chroma) → search_knowledge_base → ranked results → customer reply
```

**Why HTTP MCP over stdio?** Desktop stdio fits local agents; production banking needs a decoupled HTTP boundary for scale, network isolation, and centralized audit — implemented here as the MCP server on `:8001`.

---

## Key Security Innovations

| Control | What it does |
|---------|----------------|
| **Spatial PII tokenization** | Accounts/phones become `[ACC_A1B2]` before the model runs |
| **Intent-scoped manifests** | e.g. `GENERAL_INQUIRY` → only `search_knowledge_base`; abuse → `UNAUTHORIZED` |
| **Platform-owned context** | Worker injects `customerContext` — not prompt-trusted |
| **Out-of-band OTP gates** | `execute_p2p_transfer` / `freeze_account` require verified OTP |

Rehydration of vaulted values happens **at the MCP invoke boundary**, outside model context.

---

## Quickstart (≈5 minutes)

```bash
# 1. Environment
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# Set DATABASE_URL, REDIS_URL, SECRET_KEY (URL-encode @ in DB passwords)

# 2. MCP control plane (Terminal A) — http://localhost:8001
PYTHONPATH=. python mcp/run_server.py

# 3. Scripted demo — no LLM API key required (Terminal B)
PYTHONPATH=. python orchestrator/run_demo.py --scripted

# 4. Observability Workbench — http://127.0.0.1:7861
PYTHONPATH=. python run_dashboard.py

# 5. Customer Care chat (optional) — http://127.0.0.1:7860
PYTHONPATH=. python frontend/run_chat.py
```

Optional: after editing policy sources, rebuild the RAG index:

```bash
PYTHONPATH=. python knowledge/index/run_indexer.py
```

Gateway API (optional): `PYTHONPATH=. uvicorn main:app --reload --port 8000`

### Golden flows (workbench)

| Flow | Intent | What you should see |
|------|--------|---------------------|
| **Read** | `BALANCE_INQUIRY` | Tokenized account; `get_account_balance` via MCP |
| **Knowledge** | `GENERAL_INQUIRY` | `search_knowledge_base`; reply grounded in retrieved policy |
| **Write** | `FUND_TRANSFER` | Tokenized accounts; OTP gate **LISTENING**; `execute_p2p_transfer` |
| **Abuse** | `GENERAL_INQUIRY` + forced `freeze_account` | Block: `UNAUTHORIZED` / `tool_not_in_manifest` |

> Add a screenshot at `docs/assets/workbench-preview.png` when you capture the workbench UI.

---

## Repository Layout

```text
.
├── gateway/          # FastAPI ingress (auth, customers, accounts, OTP, …)
├── security/         # Tokenizer + session vault
├── orchestrator/     # Intent hint, LLM providers, tool-calling loop
├── worker/           # MCP client + intent manifest
├── mcp/              # MCP HTTP server (:8001), registry, tools
├── knowledge/        # RAG: load → chunk → index → retrieve
├── services/         # Domain services used by MCP tools
├── frontend/         # Customer Care chat (:7860)
├── workbench/        # Live Observability Workbench (:7861)
├── shared/           # Config, schemas, models, logging
├── database/         # ORM bootstrap (`init_db.py`)
├── docs/assets/      # Architecture diagram (and optional workbench preview)
├── run_dashboard.py
└── main.py
```

---

## MCP Tool Catalogue

| Tool | Type | Authorized intents |
|------|------|--------------------|
| `search_knowledge_base` | Read / RAG | `GENERAL_INQUIRY` |
| `get_account_balance` | Read | `BALANCE_INQUIRY`, `FUND_TRANSFER` |
| `get_transaction_history` | Read | `TRANSACTION_HISTORY` |
| `execute_p2p_transfer` | Write + OTP | `FUND_TRANSFER` |
| `freeze_account` | Write + OTP | `ACCOUNT_MANAGEMENT` |

Manifest: [`mcp/manifests/tool_permissions.yaml`](mcp/manifests/tool_permissions.yaml)

---

## Configuration

| Variable | Purpose |
|----------|---------|
| `DATABASE_URL` | PostgreSQL |
| `REDIS_URL` | Redis |
| `SECRET_KEY` | App secrets (change in production) |
| `MCP_SERVER_URL` | MCP base URL (default `http://localhost:8001`) |
| `MCP_MAX_INVOCATIONS` | Per-workflow tool-call budget |
| `LLM_API_KEY` | Optional; scripted/demo modes work without it |
| `KNOWLEDGE_INDEX_DIR` | Chroma path (default `.knowledge/chroma`) |

Full list: [`.env.example`](.env.example)

---

## License

See [LICENSE](LICENSE).

---

## Built as an AAIF Ambassadorship contribution

ACSP was built as part of an **Agentic AI Foundation (AAIF) Ambassadorship** contribution — a working reference for how customer-facing agents can operate in regulated settings without handing the model raw PII, open tool access, or unsupervised writes.

The aim is a story you can run in minutes (MCP server, scripted demo, workbench, chat) and that others can reuse: tokenization, intent manifests, platform-owned `customerContext`, MCP as the only enterprise boundary, RAG for policy questions, and OTP on state changes.

Start with the Quickstart, the architecture diagram, and the workbench golden flows.
