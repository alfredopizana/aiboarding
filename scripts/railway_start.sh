#!/usr/bin/env bash
# Entrypoint for the hosted Streamlit POC.
# 1) Ingest the real sources once (when the knowledge base is empty).
# 2) Also ingest the bundled sample_docs ONLY when AIBOARDING_INGEST_SAMPLE_DOCS
#    is set truthy (1/true/yes/on) — off by default.
# 3) Launch Streamlit bound to Railway's $PORT.
#
# Ingestion writes to whatever store is active — Postgres/pgvector when
# DATABASE_URL is set, else the JSON store under /data.
set -euo pipefail

mkdir -p "${AIBOARDING_VECTORSTORE_DIR:-/data/vectorstore}" "${AIBOARDING_AUDIT_DIR:-/data/audit}"

# Ask the active store how many documents it holds (0 => empty). Any failure
# (e.g. DB not reachable yet) is treated as 0.
count_docs() {
  python -c "from aiboarding.container import build_services; print(build_services().store.count_documents())" 2>/dev/null || echo 0
}

# Opt-in flag for the bundled sample docs (default off), normalized to lowercase.
SAMPLE="$(printf '%s' "${AIBOARDING_INGEST_SAMPLE_DOCS:-}" | tr '[:upper:]' '[:lower:]')"

DOCS=$(count_docs)
if [ "${DOCS:-0}" = "0" ]; then
  echo ">> Knowledge base empty — ingesting real sources (confluence, github)…"
  aiboarding ingest --source all || echo "!! real ingest failed — check connector env vars in Railway"

  case "$SAMPLE" in
    1 | true | yes | on)
      echo ">> AIBOARDING_INGEST_SAMPLE_DOCS set — also ingesting bundled sample_docs…"
      aiboarding ingest --source local --path /app/data/sample_docs \
        || echo "!! sample_docs ingest failed"
      ;;
  esac

  DOCS=$(count_docs)
  echo ">> Knowledge base now holds ${DOCS:-0} docs."
else
  echo ">> Knowledge base has $DOCS docs — skipping ingestion."
fi

echo ">> Starting Streamlit on port ${PORT:-8501}"
exec streamlit run src/aiboarding/ui/streamlit_app.py \
  --server.port "${PORT:-8501}" \
  --server.address 0.0.0.0 \
  --server.headless true \
  --browser.gatherUsageStats false
