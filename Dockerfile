# syntax=docker/dockerfile:1
# AgriVibe Gradio frontend. Build context: this repository. Built by .github/workflows/deploy.yml.
# Same multi-stage pattern as the backend: dependencies first (cached), then the source.
FROM ghcr.io/astral-sh/uv:0.13.7@sha256:96f40d3904aad8d0bd010539001d36c8e2188b981e1334471a90c4a1d93bb490 AS uv

FROM python:3.12-slim-bookworm@sha256:935c3c5b12357a7e10caa9c1e6ca5692344d97cf229832ef584be2cec9fc03df AS build
COPY --from=uv /uv /usr/local/bin/uv
ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy UV_PYTHON_DOWNLOADS=never UV_PROJECT_ENVIRONMENT=/app/.venv
WORKDIR /app
COPY pyproject.toml uv.lock ./
RUN --mount=type=cache,target=/root/.cache/uv uv sync --locked --no-dev

FROM python:3.12-slim-bookworm@sha256:935c3c5b12357a7e10caa9c1e6ca5692344d97cf229832ef584be2cec9fc03df
RUN useradd --uid 10001 --no-create-home --shell /usr/sbin/nologin app
COPY --from=build /app/.venv /app/.venv
WORKDIR /app
COPY app.py settings.py ./
COPY api ./api
COPY contracts ./contracts
COPY handlers ./handlers
COPY theme ./theme
# GRADIO_SERVER_NAME: listen on every interface, not only 127.0.0.1, so the load balancer can reach it.
# AGRIVIBE_API: the backend. On ECS both containers share the task's localhost.
# This classroom branch targets Session 2's in-memory API; override the mode for the full-stack API.
ENV PATH=/app/.venv/bin:$PATH PYTHONUNBUFFERED=1 HOME=/tmp \
    GRADIO_SERVER_NAME=0.0.0.0 GRADIO_SERVER_PORT=7860 GRADIO_ANALYTICS_ENABLED=False \
    AGRIVIBE_API=http://127.0.0.1:8000 AGRIVIBE_BACKEND_MODE=lesson2
USER app
EXPOSE 7860
HEALTHCHECK --interval=10s --timeout=3s --start-period=20s --retries=3 \
  CMD ["python", "-c", "import urllib.request; urllib.request.urlopen('http://127.0.0.1:7860/', timeout=2)"]
CMD ["python", "app.py"]
