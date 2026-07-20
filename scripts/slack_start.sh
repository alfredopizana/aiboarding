#!/usr/bin/env bash
# Entrypoint for the hosted Slack bot (Socket Mode — no public port).
#
# The bot shares the same Postgres as the UI service, so it does NOT ingest —
# the UI ("web") service owns ingestion. If you deploy Slack *without* the UI,
# populate the knowledge base once from a Railway shell:
#   aiboarding ingest --source all
set -euo pipefail

echo ">> Starting AIboarding Slack bot (Socket Mode)…"
exec aiboarding slack
