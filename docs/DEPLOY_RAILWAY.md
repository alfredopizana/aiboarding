# Deploy AIboarding on Railway

One Railway **project** with up to three services. The knowledge/agent
"backend" is not a separate service — it's the `aiboarding` package embedded in
each front-end process.

| Service | What it is | Public port | Config file |
|---------|-----------|:-----------:|-------------|
| **Postgres** | Railway plugin: relational data **+** pgvector embeddings. Makes the app stateless. | no | *(plugin)* |
| **web** | Streamlit UI — the URL you share for the demo. Owns first-boot ingestion. | **yes** | `railway.json` |
| **slack** *(optional)* | Slack bot (Socket Mode). Shares the same Postgres; does **not** re-ingest. | no | `railway.slack.json` |

The image is shared: `Dockerfile` installs `.[ui,slack,postgres]`, and each
service just runs a different start command (config-as-code, no dashboard
tweaking).

## 1. Create the project + Postgres

1. Push this repo to GitHub.
2. <https://railway.app> → **New Project → Deploy from GitHub repo** → pick
   `aiboarding`. This first service becomes the **web** service.
3. In the project → **New → Database → Add PostgreSQL**. Railway injects
   `DATABASE_URL` into services that reference it.

> **Supabase instead?** The pgvector code is identical — just set
> `DATABASE_URL` to your Supabase connection string on the web (and slack)
> service and skip the Railway Postgres plugin. Nothing else changes.

When `DATABASE_URL` is set, AIboarding stores **both** the relational data
(users/plans/progress/history) **and** the document embeddings (pgvector) in
Postgres. No volume needed; you can scale replicas. The `vector` extension is
created automatically on first boot. Only the audit trail stays file-based —
mount a small `/data` volume on the web service if you want it to survive
redeploys, otherwise it resets (fine for a demo).

## 2. Point the web service at the config + set variables

- **Settings → Config-as-code** → set the config file to `railway.json`
  (Railway usually picks it up automatically).
- **Variables** → add `DATABASE_URL = ${{Postgres.DATABASE_URL}}` plus:

| Variable | Value |
|----------|-------|
| `OPENAI_API_KEY` | `sk-...` |
| `CONFLUENCE_BASE_URL` | `https://<site>.atlassian.net/wiki` |
| `CONFLUENCE_EMAIL` | your email |
| `CONFLUENCE_API_TOKEN` | `ATATT...` |
| `GITHUB_TOKEN` | `github_pat_...` |
| `GITHUB_REPOS` | `Noesis-Foundry/core-api,Noesis-Foundry/web-app,...` |
| `AIBOARDING_UI_PASSWORD` | a password — **gates the public URL, recommended** |
| `AIBOARDING_INGEST_SAMPLE_DOCS` | `true` to also load the bundled offline sample docs (optional, off by default) |
| `AIBOARDING_SHOW_AUDIT_BUTTON` | `true` / `false` (optional) |
| `AIBOARDING_LANGSMITH_TRACING` | `true` + `AIBOARDING_LANGSMITH_API_KEY` (optional) |

> `AIBOARDING_LLM_PROVIDER=openai`, `AIBOARDING_EMBEDDINGS_PROVIDER=openai` and
> the `/data` paths are already baked into the `Dockerfile`.

Then **Settings → Networking → Generate Domain** to get the public URL.

## 3. First deploy

On the **first boot** the web entrypoint ingests Confluence + GitHub (watch the
deploy logs) before Streamlit answers the healthcheck — this can take a few
minutes; `healthcheckTimeout` in `railway.json` is set to 300s. Later boots see
a populated Postgres and skip ingestion, so they start fast.

**Bundled sample docs (opt-in):** set `AIBOARDING_INGEST_SAMPLE_DOCS=true` to
also ingest the offline `data/sample_docs` on first boot — handy if the real
connectors aren't configured and you just want content in the demo. Off by
default (real sources only). Either way the docs land in the active store
(Postgres/pgvector when `DATABASE_URL` is set). Watch the logs for
`>> Knowledge base now holds N docs`.

## 4. (Optional) Add the Slack service

Same repo, same image, Socket Mode (outbound only → no public port).

1. Project → **New → GitHub Repo** → pick `aiboarding` again (a second service).
2. **Settings → Config-as-code** → set the config file to `railway.slack.json`.
3. **Variables** → add `DATABASE_URL = ${{Postgres.DATABASE_URL}}`,
   `OPENAI_API_KEY`, the connector vars, and:
   - `SLACK_BOT_TOKEN` (`xoxb-...`)
   - `SLACK_APP_TOKEN` (`xapp-...`)

The Slack service does **not** ingest (the web service already populated
Postgres). If you ever run Slack *without* the web service, open a Railway shell
and run `aiboarding ingest --source all` once.

## Re-ingesting after content changes

To refresh the knowledge base (e.g. you edited Confluence), open a Railway shell
on the **web** service and run:

```
aiboarding ingest --source all
```

(Pushing the same doc URI updates it in place; no need to wipe first.)

## Notes & caveats

- **Cost**: every question hits OpenAI — a shared URL spends your key. Set
  `AIBOARDING_UI_PASSWORD` so only people you share the password with can use it.
- **Exposure**: ingested Confluence/GitHub content is queryable by anyone who can
  open the app. Fine for the test/demo data; don't point it at sensitive spaces
  without auth.
- If the chat websocket seems stuck behind Railway's proxy, add
  `--server.enableCORS false --server.enableXsrfProtection false` to the
  Streamlit command in `scripts/railway_start.sh`.
