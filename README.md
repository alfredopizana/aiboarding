# AIboarding 🚀

AI-powered onboarding assistant. Generates **90-Day Success Plans**, answers new-hire
questions with cited sources, tells you **who to connect with**, and refers you to the
right documentation — built on **LangGraph** with a full **audit trail** for every interaction.

## Features

- **90-Day Success Plan generator** — 30/60/90 phases per role (engineer, product, default),
  with items linked to *real* teammates and *real* ingested docs.
- **Q&A with citations (RAG)** — answers grounded in your company knowledge; every answer
  cites its sources or honestly says it doesn't know.
- **People connector** — "who knows about kubernetes?" → expertise-matched contacts with reasons.
- **Doc referral** — "where are the runbook docs?" → direct links to Confluence/Drive/GitHub/files.
- **Auditable by design** — every LangGraph node execution is logged (JSONL per thread):
  latency, input/output digests (no raw PII), sources used, model.
- **Offline deterministic mode** — `fake` LLM + `hashing` embeddings: demo and CI need no API keys.

## Data sources (Phase 1)

| Connector | Config |
|---|---|
| Local files (`.md`, `.txt`, `.pdf`) | `--path` or `data/sample_docs/` |
| Confluence Cloud | `CONFLUENCE_BASE_URL`, `CONFLUENCE_EMAIL`, `CONFLUENCE_API_TOKEN` |
| GitHub (READMEs + docs) | `GITHUB_TOKEN`, `GITHUB_REPOS=org/repo1,org/repo2` |
| Google Drive | `GDRIVE_CREDENTIALS_PATH`, `GDRIVE_FOLDER_IDS` + `pip install ".[gdrive]"` |

Unconfigured connectors are skipped gracefully.

## Phase 2 (included, activated by config)

- **Slack bot** (Socket Mode): `pip install ".[slack]"` + `SLACK_BOT_TOKEN`/`SLACK_APP_TOKEN`,
  then `python -m aiboarding.integrations.slack_bot`. See `integrations/slack_bot.py`.
- **Email** (SMTP, stdlib): send plans/digests via `EmailSender` — `SMTP_*` env vars.

## Quickstart

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env   # optional; offline mode works with zero config

# 1. Ingest sample knowledge + your sources
aiboarding ingest --source local --path ./data/sample_docs
aiboarding ingest --source all     # also confluence/github/gdrive if configured

# 2. Ask anything
aiboarding ask "How do I set up my development environment?"
aiboarding ask "¿Quién sabe de kubernetes?"

# 3. Generate a 90-day plan
aiboarding plan --name "Ana López" --role engineer --team platform --output plan.md

# 4. Who to talk to
aiboarding people "security training"

# 5. Inspect the audit trail of any interaction
aiboarding audit thr_xxxxxxxxxxxx

# 6. REST API
aiboarding serve   # → http://127.0.0.1:8000/docs
```

### Real LLM mode

```bash
export AIBOARDING_LLM_PROVIDER=openai
export AIBOARDING_EMBEDDINGS_PROVIDER=openai
export OPENAI_API_KEY=sk-...
```

## API

| Method | Route | Description |
|---|---|---|
| GET | `/health` | Store/people stats |
| POST | `/ask` | `{query, user?}` → answer + citations + people |
| POST | `/plan` | `UserProfile` → structured plan + markdown |
| GET | `/people?topic=` | Expertise matching |
| POST | `/ingest` | Trigger ingestion |
| GET | `/audit/{thread_id}` | Full audit trail |

## Architecture

LangGraph `StateGraph`:

```
START → classify_intent ─┬→ answer_question ─┐
                         ├→ suggest_people ──┤
                         ├→ generate_plan ───┼→ finalize → END
                         └→ refer_docs ──────┘
```

Full specs in [`specs/`](specs/): vision, architecture, ingestion, agent+audit,
90-day plan, API/CLI/integrations.

## Development

```bash
pytest            # 36 tests, fully offline
ruff check src tests
```

Project layout:

```
src/aiboarding/
  connectors/    # local, confluence, gdrive, github
  ingestion/     # chunker, pipeline
  knowledge/     # embeddings, vectorstore, people
  agent/         # LangGraph nodes, graph, audit, llm
  plans/         # 90-day generator + role templates
  api/           # FastAPI
  integrations/  # Phase 2: slack, email
specs/           # SPEC-001..006
data/            # people.yaml, sample_docs/
tests/
```

## License

MIT
