# AIboarding — container for the Streamlit POC (Railway / any container host).
FROM python:3.12-slim

WORKDIR /app

# Install the package + UI extra (streamlit). Copy metadata + source first so
# the layer caches when only data/scripts change.
COPY pyproject.toml README.md ./
COPY src ./src
RUN pip install --no-cache-dir ".[ui]"

# Baked-in, non-user data (the people directory + offline sample docs).
COPY data/people.yaml ./data/people.yaml
COPY data/sample_docs ./data/sample_docs
COPY scripts ./scripts

# Real services + point mutable state at the mounted volume (/data).
ENV AIBOARDING_LLM_PROVIDER=openai \
    AIBOARDING_EMBEDDINGS_PROVIDER=openai \
    AIBOARDING_PEOPLE_FILE=/app/data/people.yaml \
    AIBOARDING_DATA_DIR=/data \
    AIBOARDING_VECTORSTORE_DIR=/data/vectorstore \
    AIBOARDING_AUDIT_DIR=/data/audit \
    AIBOARDING_DB_PATH=/data/aiboarding.db

EXPOSE 8501
CMD ["bash", "scripts/railway_start.sh"]
