# Deploy the AIboarding POC on Railway

Hosts the **Streamlit app** so you can share the POC via a URL. Uses the
included `Dockerfile` + `scripts/railway_start.sh`.

## 1. Create the service

1. Push this repo to GitHub (already done if you're reading this in the repo).
2. On <https://railway.app> → **New Project → Deploy from GitHub repo** → pick
   `aiboarding`. Railway detects the `Dockerfile` and builds it.

## 2. Choose where state lives

**Option A — SQLite + a Volume (simplest, single instance).**
Service → **Settings → Volumes → New Volume** → mount path **`/data`**. Persists
the SQLite DB, the JSON vector store, and the audit trail across redeploys.
Works great for one instance; it does not scale to multiple replicas.

**Option B — Postgres + pgvector (recommended, stateless & scalable).**
1. In the project → **New → Database → Add PostgreSQL**. Railway injects
   `DATABASE_URL` into your service automatically (reference it under Variables
   if needed: `${{Postgres.DATABASE_URL}}`).
2. That's it: when `DATABASE_URL` is set, AIboarding puts **both** the relational
   data (users/plans/progress/history) **and** the document embeddings
   (pgvector) in Postgres. The app becomes stateless — no Volume needed, and you
   can scale to multiple replicas.
   - The `vector` extension is created automatically on first boot (Railway's
     Postgres role allows `CREATE EXTENSION`).
   - Only the audit trail stays file-based; mount a small `/data` volume if you
     want it to survive redeploys, otherwise it's fine to let it reset.

## 3. Set environment variables

Service → **Variables** → add (values from your local `.env`):

| Variable | Value |
|----------|-------|
| `OPENAI_API_KEY` | `sk-...` |
| `CONFLUENCE_BASE_URL` | `https://<site>.atlassian.net/wiki` |
| `CONFLUENCE_EMAIL` | your email |
| `CONFLUENCE_API_TOKEN` | `ATATT...` |
| `GITHUB_TOKEN` | `github_pat_...` |
| `GITHUB_REPOS` | `Noesis-Foundry/core-api,Noesis-Foundry/web-app,...` |
| `DATABASE_URL` | *(Option B)* injected automatically when you add Railway Postgres — reference `${{Postgres.DATABASE_URL}}` if it's a separate service |
| `AIBOARDING_UI_PASSWORD` | a password (protects the public URL — **recommended**) |
| `AIBOARDING_SHOW_AUDIT_BUTTON` | `true` / `false` (optional) |
| `AIBOARDING_LANGSMITH_TRACING` | `true` + `AIBOARDING_LANGSMITH_API_KEY` (optional) |

> `AIBOARDING_LLM_PROVIDER=openai`, `AIBOARDING_EMBEDDINGS_PROVIDER=openai` and the
> `/data` paths are already set in the `Dockerfile` — no need to repeat them.

## 4. Deploy

Railway builds and starts it. On the **first boot** the entrypoint ingests
Confluence + GitHub into the volume (watch the deploy logs). Later boots skip
ingestion because the vector store is already there.

Railway assigns a public URL under **Settings → Networking → Generate Domain**.
Share that URL.

## Re-ingesting after content changes

To refresh the knowledge base (e.g. you edited Confluence), either:
- Delete `store.json` from the volume and redeploy, or
- Open a Railway shell on the service and run `aiboarding ingest --source all`.

## Notes & caveats

- **Cost**: every question hits the OpenAI API — a shared URL spends your key.
  Set `AIBOARDING_UI_PASSWORD` so only people you share the password with can use it.
- **Exposure**: the ingested Confluence/GitHub content is queryable by anyone who
  can open the app. Fine for the test/demo data; don't point it at sensitive real
  spaces without auth.
- **Slack bot** (optional): the bot uses Socket Mode (outbound), so it can run as a
  **second Railway service** from the same repo with start command
  `aiboarding slack` and the `SLACK_BOT_TOKEN` / `SLACK_APP_TOKEN` variables. It
  needs no public port.
- If the app loads but the chat websocket seems stuck behind Railway's proxy, add
  `--server.enableCORS false --server.enableXsrfProtection false` to the Streamlit
  command in `scripts/railway_start.sh`.
