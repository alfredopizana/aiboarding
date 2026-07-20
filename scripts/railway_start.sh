#!/usr/bin/env bash
# Entrypoint for the hosted Streamlit POC.
# 1) Ingest the real sources once (when the knowledge base is empty).
# 2) Launch Streamlit bound to Railway's $PORT.
set -euo pipefail

mkdir -p "${AIBOARDING_VECTORSTORE_DIR:-/data/vectorstore}" "${AIBOARDING_AUDIT_DIR:-/data/audit}"

# Works for both the JSON store and Postgres/pgvector: ask the store how many
# documents it holds (0 => needs ingestion). Empty/failure is treated as 0.
DOCS=$(python -c "from aiboarding.container import build_services; print(build_services().store.count_documents())" 2>/dev/null || echo 0)
if [ "${DOCS:-0}" = "0" ]; then
  echo ">> Knowledge base empty — ingesting real sources (confluence, github)…"
  aiboarding ingest --source all || echo "!! ingest failed — check connector env vars in Railway"
else
  echo ">> Knowledge base has $DOCS docs — skipping ingestion."
fi

echo ">> Starting Streamlit on port ${PORT:-8501}"
exec streamlit run src/aiboarding/ui/streamlit_app.py \
  --server.port "${PORT:-8501}" \
  --server.address 0.0.0.0 \
  --server.headless true \
  --browser.gatherUsageStats false
