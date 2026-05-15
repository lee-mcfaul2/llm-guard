# syntax=docker/dockerfile:1.7

# Builder stage: install deps, pre-download ML models so the HuggingFace cache
# is baked into the runtime image.
FROM python:3.12-slim AS builder

ENV PIP_NO_CACHE_DIR=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    UV_LINK_MODE=copy

RUN apt-get update && apt-get install -y --no-install-recommends \
      build-essential \
      curl \
    && rm -rf /var/lib/apt/lists/*

RUN pip install uv

WORKDIR /app
COPY pyproject.toml ./
RUN uv venv /opt/venv && \
    . /opt/venv/bin/activate && \
    uv pip compile pyproject.toml --quiet -o /tmp/requirements.txt && \
    uv pip install --no-cache --requirement /tmp/requirements.txt

ENV PATH="/opt/venv/bin:$PATH" \
    HF_HOME=/opt/huggingface

# Pre-load every ML scanner so the model files land in /opt/huggingface.
# Outbound PromptInjection is aliased to input_scanners.PromptInjection in our
# wrapper (per Task 11 deviation), so we only need to load the input variant.
# Best-effort: if a scanner's API/model differs in the pinned llm-guard
# version, fall back to lazy runtime download rather than failing the image.
RUN (python -c "from llm_guard.input_scanners import PromptInjection, Toxicity, BanTopics; \
PromptInjection(); Toxicity(); BanTopics(topics=['violence'])" && \
    python -c "from llm_guard.output_scanners import MaliciousURLs, Sensitive; \
MaliciousURLs(); Sensitive()") \
    || echo "WARN: ML scanner preload failed; models will download at runtime"

# Runtime stage
FROM python:3.12-slim AS runtime

RUN apt-get update && apt-get install -y --no-install-recommends \
      libgomp1 \
    && rm -rf /var/lib/apt/lists/* && \
    addgroup --system app && adduser --system --ingroup app app

ENV PYTHONUNBUFFERED=1 \
    PATH="/opt/venv/bin:$PATH" \
    HF_HOME=/opt/huggingface

COPY --from=builder /opt/venv /opt/venv
COPY --from=builder /opt/huggingface /opt/huggingface
COPY --chown=app:app src/ /app/src/

USER app
WORKDIR /app

EXPOSE 8080

HEALTHCHECK --interval=10s --timeout=3s --start-period=30s \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8080/healthz', timeout=2)"

ENTRYPOINT ["python", "-m", "llm_guard_svc"]
