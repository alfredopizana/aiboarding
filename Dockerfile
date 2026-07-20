# AIboarding — one image, two start commands (Streamlit UI + Slack bot).
# Runs on Railway or any container host.
FROM python:3.12-slim

WORKDIR /app

# Install the package + UI (streamlit) + Slack + Postgres/pgvector extras.
# Copy metadata + source first so the layer caches when only data/scripts change.
COPY pyproject.toml README.md ./
COPY src ./src
RUN pip install --no-cache-dir ".[ui,slack,postgres]"

# Baked-in, non-user data: the people directory + the offline sample_docs.
# On Railway the knowledge base is built from the REAL connectors (Confluence +
# GitHub) into Postgres/pgvector. The sample_docs ship as an *opt-in* the
# entrypoint ingests only when AIBOARDING_INGEST_SAMPLE_DOCS is set truthy
# (see railway_start.sh).
COPY data/people.yaml ./data/people.yaml
COPY data/sample_docs ./data/sample_docs
COPY scripts ./scripts

# Real providers.
ENV AIBOARDING_LLM_PROVIDER=openai
ENV AIBOARDING_EMBEDDINGS_PROVIDER=openai
ENV AIBOARDING_PEOPLE_FILE=/app/data/people.yaml

# File-based state paths. With DATABASE_URL set (Postgres/pgvector) the app is
# stateless and /data is only used for the optional audit trail.
ENV AIBOARDING_DATA_DIR=/data
ENV AIBOARDING_VECTORSTORE_DIR=/data/vectorstore
ENV AIBOARDING_AUDIT_DIR=/data/audit
ENV AIBOARDING_DB_PATH=/data/aiboarding.db

ENV PYTHONUNBUFFERED=1

EXPOSE 8501
# Default = UI service. The Slack service overrides this via railway.slack.json.
CMD ["bash", "scripts/railway_start.sh"]
