#!/usr/bin/env bash
# Entrypoint for the hosted Streamlit POC.
# 1) On the first boot (empty volume) ingest the real sources.
# 2) Launch Streamlit bound to Railway's $PORT.
set -euo pipefail

VS_DIR="${AIBOARDING_VECTORSTORE_DIR:-/data/vectorstore}"
AUDIT_DIR="${AIBOARDING_AUDIT_DIR:-/data/audit}"
mkdir -p "$VS_DIR" "$AUDIT_DIR"

if [ ! -f "$VS_DIR/store.json" ]; then
  echo ">> First boot: no vectorstore found — ingesting real sources (confluence, github)…"
  aiboarding ingest --source all || echo "!! ingest failed — check connector env vars in Railway"
else
  echo ">> Vectorstore present — skipping ingestion."
fi

echo ">> Starting Streamlit on port ${PORT:-8501}"
exec streamlit run src/aiboarding/ui/streamlit_app.py \
  --server.port "${PORT:-8501}" \
  --server.address 0.0.0.0 \
  --server.headless true \
  --browser.gatherUsageStats false
