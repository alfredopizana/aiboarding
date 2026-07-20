# Deploy the AIboarding POC on Railway

Hosts the **Streamlit app** so you can share the POC via a URL. Uses the
included `Dockerfile` + `scripts/railway_start.sh`.

## 1. Create the service

1. Push this repo to GitHub (already done if you're reading this in the repo).
2. On <https://railway.app> → **New Project → Deploy from GitHub repo** → pick
   `aiboarding`. Railway detects the `Dockerfile` and builds it.

## 2. Add a Volume (required — the filesystem is otherwise ephemeral)

Service → **Settings → Volumes → New Volume** → mount path **`/data`**.

This persists the SQLite DB (users/plans/progress), the vector store, and the
audit trail across redeploys. Without it, every deploy wipes user data and you'd
re-ingest each time.

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
