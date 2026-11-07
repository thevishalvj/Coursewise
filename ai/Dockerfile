# Coursewise AI service. Build from the repo root:
#   docker build -f ai/Dockerfile -t coursewise-ai .
# The embedding model and the ChromaDB index are built into the image,
# so the container needs only Gemini (and optionally Redis) at runtime.

FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    HF_HOME=/opt/hf \
    COURSEWISE_MARKDOWN_DIR=/app/data/markdown \
    COURSEWISE_CHROMA_DIR=/app/data/chroma

WORKDIR /app/ai

# CPU-only PyTorch is about 10x smaller than the default CUDA build.
ARG TORCH_INDEX_URL=https://download.pytorch.org/whl/cpu

# Optional build secret "ca": an extra CA bundle for builds behind a TLS-inspecting proxy.
RUN --mount=type=secret,id=ca,required=false \
    if [ -f /run/secrets/ca ]; then export PIP_CERT=/run/secrets/ca; fi; \
    pip install torch --index-url "$TORCH_INDEX_URL"

COPY ai/requirements.txt .
RUN --mount=type=secret,id=ca,required=false \
    if [ -f /run/secrets/ca ]; then export PIP_CERT=/run/secrets/ca; fi; \
    pip install -r requirements.txt

COPY ai/coursewise ./coursewise
COPY data/markdown /app/data/markdown

# Download the embedding model and build the index at build time.
# REDIS_URL is empty here so ingest does not try to clear a cache.
RUN --mount=type=secret,id=ca,required=false \
    if [ -f /run/secrets/ca ]; then export REQUESTS_CA_BUNDLE=/run/secrets/ca SSL_CERT_FILE=/run/secrets/ca; fi; \
    REDIS_URL= python -m coursewise.ingest

RUN useradd --create-home app && chown -R app /app/data /opt/hf
USER app

ENV HF_HUB_OFFLINE=1
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --start-period=60s \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')"
CMD ["uvicorn", "coursewise.api:app", "--host", "0.0.0.0", "--port", "8000"]
