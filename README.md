# AIboarding 🚀

AI-powered onboarding assistant. Generates **personalized 90-Day Success Plans**, answers
new-hire questions with **reasoning + cited sources**, tells you **who to connect with**, tracks
your **progress**, and works across a **web app**, **Slack**, a **REST API**, and a **CLI** —
built on **LangGraph** with a full **audit trail** for every interaction.

## Features

- **Personalized answers (RAG + reasoning)** — the assistant reasons over your **profile**, your
  **90-day plan**, relevant **teammates**, **code repos**, and ingested **docs** to give an
  actionable recommendation (not just a list of links), with cited sources.
- **90-Day Success Plan generator** — 30/60/90 phases per role (engineer, product, devops, data,
  security, qa, default), auto-selected from your team, linked to *real* teammates and *real* docs.
- **Progress tracking & persistence** — users, plans (with per-item done state) and conversation
  history persist in **SQLite** locally or **Postgres** when hosted.
- **People connector** — "who knows about kubernetes?" → expertise-matched contacts with reasons.
- **Auditable by design** — every LangGraph node execution is logged (latency, digests, sources,
  model), inspectable inline in the web app or via `aiboarding audit`; optional **LangSmith** tracing.
- **Multi-channel** — Streamlit **web app**, **Slack** bot (`plan` / `progreso` / `done <n>` + Q&A),
  REST API, CLI. All share the same core.
- **Offline deterministic mode** — `fake` LLM + `hashing` embeddings: demo and CI need no API keys.

## Quickstart (local, offline)

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev,ui]"
cp .env.example .env          # offline mode works with zero config

aiboarding ingest --source local --path ./data/sample_docs
aiboarding ui                 # web app → http://localhost:8501
```

For real answers, set OpenAI + your connectors in `.env` (see **Configuration**), then
`aiboarding ingest --source all`.

## Interfaces / useful commands

```bash
# Web app (Streamlit SPA): chat, plan + progress checklist, people, admin/audit
aiboarding ui                                   # http://localhost:8501

# Slack bot (Socket Mode — needs pip install ".[slack]" + tokens)
aiboarding slack                                # @bot ask… | plan | progreso | done 3

# REST API
aiboarding serve                                # http://127.0.0.1:8000/docs

# CLI
aiboarding ask "¿Qué leo primero, docs o agendo reuniones?"
aiboarding plan --name "Ana López" --team data --output plan.md
aiboarding people "security training"
aiboarding ingest --source all                  # confluence + github + gdrive (excludes local)
aiboarding ingest --source local --path ./data/sample_docs
aiboarding audit thr_xxxxxxxxxxxx               # trace of one interaction
aiboarding info                                 # active config + store/people stats

# Push data at runtime (no connector; same URI updates in place)
aiboarding add-doc --title "Parking Policy" --file ./policy.md
aiboarding add-person --id jane.doe --name "Jane Doe" --role SRE --team devops --slack @janed
```

> `--source all` ingests the **real** connectors (confluence, gdrive, github). The local sample
> docs are excluded from `all` to avoid duplicating content; ingest them with `--source local`.

## Data sources (Phase 1)

| Connector | Config |
|---|---|
| Local files (`.md`, `.txt`, `.pdf`) | `--source local --path data/sample_docs/` |
| Confluence Cloud | `CONFLUENCE_BASE_URL`, `CONFLUENCE_EMAIL`, `CONFLUENCE_API_TOKEN` |
| GitHub (READMEs + docs) | `GITHUB_TOKEN`, `GITHUB_REPOS=org/repo1,org/repo2` |
| Google Drive | `GDRIVE_CREDENTIALS_PATH`, `GDRIVE_FOLDER_IDS` + `pip install ".[gdrive]"` |
| Direct push | `aiboarding add-doc` / `POST /documents` |

Unconfigured connectors are skipped gracefully. Setup walkthrough: [`docs/POC_SETUP.md`](docs/POC_SETUP.md).

## Persistence & scaling

| | Local (default) | Hosted / scalable |
|---|---|---|
| Users, plans, progress, chat history | **SQLite** (`data/aiboarding.db`) | **Postgres** |
| Document embeddings + similarity | JSON file (`data/vectorstore/`) | **Postgres + pgvector** |
| App state | file-based (needs a volume when hosted) | **stateless** (scales to N replicas) |

The switch is a single env var: **set `DATABASE_URL`** (e.g. Railway Postgres) and *both* the
relational data and the embeddings move to Postgres — no other changes. Install the driver with
`pip install ".[postgres]"`. The `ProgressStore` / `VectorStore` are behind swappable interfaces.

> Changing embeddings provider (hashing↔openai) changes vector dimensions — re-ingest
> (`rm -rf data/vectorstore` locally, or `DROP TABLE doc_chunks` on Postgres).

## Hosting the POC (share a URL)

Ships with a `Dockerfile` + entrypoint for **Railway** (or any container host). See
[`docs/DEPLOY_RAILWAY.md`](docs/DEPLOY_RAILWAY.md). Highlights:

- **Login wall**: set **`AIBOARDING_UI_PASSWORD`** and the web app requires it — protects your
  OpenAI/connector keys from misuse on a public URL. Unset = open.
- Add **Postgres** for a stateless, scalable deploy (no volume needed).

## Configuration

All keys work with or without the `AIBOARDING_` prefix; secrets live in `.env` (gitignored).

| Variable | Purpose |
|---|---|
| `AIBOARDING_LLM_PROVIDER` / `AIBOARDING_EMBEDDINGS_PROVIDER` | `openai` \| `fake`/`hashing` (offline) |
| `OPENAI_API_KEY` | OpenAI key (LLM + embeddings) |
| `CONFLUENCE_*`, `GITHUB_TOKEN`, `GITHUB_REPOS`, `GDRIVE_*` | connectors |
| `SLACK_BOT_TOKEN`, `SLACK_APP_TOKEN` | Slack bot (Socket Mode) |
| `DATABASE_URL` | Postgres for relational + pgvector (unset ⇒ SQLite + JSON) |
| `AIBOARDING_DB_PATH` | SQLite path (default `./data/aiboarding.db`) |
| `AIBOARDING_UI_PASSWORD` | login-wall password for the web app (unset ⇒ open) |
| `AIBOARDING_SHOW_AUDIT_BUTTON` | show the "Ver auditoría" button under chat answers |
| `AIBOARDING_LANGSMITH_TRACING` + `_API_KEY` + `_PROJECT` | optional LangSmith tracing |

## Local Postgres (test the scalable path)

```bash
docker run -d --name aiboarding-pg -p 5433:5432 \
  -e POSTGRES_PASSWORD=aiboarding -e POSTGRES_USER=aiboarding -e POSTGRES_DB=aiboarding \
  pgvector/pgvector:pg16
pip install -e ".[postgres]"
export DATABASE_URL="postgresql://aiboarding:aiboarding@localhost:5433/aiboarding"

aiboarding ingest --source all && aiboarding ui      # now backed by Postgres + pgvector
docker exec aiboarding-pg psql -U aiboarding -d aiboarding -c "\dt"   # inspect
```

## API

| Method | Route | Description |
|---|---|---|
| GET | `/health` | Store/people stats |
| POST | `/ask` | `{query, user?}` → answer + citations + people |
| POST | `/plan` | `UserProfile` → structured plan + markdown |
| GET/POST | `/people` | Expertise matching / add-update a person |
| POST | `/ingest` · `/documents` | Trigger ingestion / push one document |
| GET | `/audit/{thread_id}` | Full audit trail |

## Architecture

LangGraph `StateGraph` — `classify_intent` routes to `answer_question` (personalized reasoning),
`suggest_people`, `generate_plan`, or `refer_docs`, then `finalize`. Full specs in [`specs/`](specs/).

```
src/aiboarding/
  connectors/    # local, confluence, gdrive, github
  ingestion/     # chunker, pipeline
  knowledge/     # embeddings, vectorstore (JSON), pgvector_store, people
  agent/         # LangGraph nodes, graph, audit, llm
  plans/         # 90-day generator + role templates
  persistence/   # ProgressStore: SQLite / Postgres (users, plans, progress, history)
  api/           # FastAPI
  ui/            # Streamlit SPA
  integrations/  # Slack bot, email
  tracing.py     # LangSmith
```

## Development

```bash
pytest                 # 70 tests, fully offline
ruff check src tests
```

## License

MIT
