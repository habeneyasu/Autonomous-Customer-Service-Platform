# Autonomous Customer Service Platform (ACSP)

An AI-powered customer assistant that handles customer requests through natural language over a web chat interface.

## How It Works

```
Customer
   │
   ▼
Web Chat UI
   │
   ▼
API Gateway          ← request validation, idempotency, masking
   │
   ▼
Customer FIFO Queue
   │
   ▼
AI Supervisor        ← intent classification, entity extraction, planning
   │
   ├─────────────────────────┐
   ▼                         ▼
Knowledge Request      Business Request
   │                         │
   ▼                         ▼
search_knowledge_base    Worker Agent    ← authorization, context, MCP client
MCP Tool                     │
   │                         ▼
   ▼                      MCP Tools     ← customer_account, payment, notification
  RAG                         │
   │                         ▼
   └──────────┬──────────────┘
              ▼
        Security Layer       ← OTP, session, verification
              │
              ▼
     Business Execution      ← transaction manager, rollback, notifications
              │
              ▼
    Response Generator       ← formatting, localization, delivery
              │
              ▼
           Customer
```

## Project Structure

```
├── gateway/        API ingress, validation, idempotency, queue
├── supervisor/     Intent classification, entity extraction, planner
├── worker/         Authorization, context assembly, MCP client
├── mcp/            MCP server and tool definitions
├── knowledge/      RAG pipeline — ingestion, retrieval, ranking
├── execution/      Transaction manager, rollback, OTP dispatch
├── security/       Auth, session, OTP, verification
├── response/       Answer generation, formatting, localization
├── observability/  Logging, tracing, metrics, audit
├── workflow/       LangGraph state machine and routing
├── shared/         Models, schemas, enums, config, exceptions, utils
└── database/       Schema and migrations
```

## Getting Started

**Prerequisites:** Python 3.12+, PostgreSQL 15+, Redis 7+

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # set DATABASE_URL, SECRET_KEY, REDIS_URL
psql -d acsp -f database/schema.sql
```

Key `.env` variables:

| Variable | Default | Description |
|---|---|---|
| `DATABASE_URL` | `postgresql+psycopg://...@localhost/acsp` | PostgreSQL |
| `REDIS_URL` | `redis://localhost:6379/0` | Redis |
| `MCP_SERVER_URL` | `http://localhost:8001` | Internal MCP server |
| `SECRET_KEY` | — | **Required in production** |
| `OTP_TTL_SECONDS` | `300` | OTP validity window |
| `IDEMPOTENCY_TTL_SECONDS` | `86400` | Idempotency key lifetime |
| `RATE_LIMIT_REQUESTS` | `100` | Requests per window |

See `.env.example` for the full list.

## License

See [LICENSE](LICENSE).
