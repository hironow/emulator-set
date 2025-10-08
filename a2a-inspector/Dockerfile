# syntax=docker/dockerfile:1.6

ARG A2A_INSPECTOR_REPO=https://github.com/a2aproject/a2a-inspector.git
ARG A2A_INSPECTOR_REF=main

# Stage 0: fetch source once and reuse from later stages
FROM alpine/git AS source
ARG A2A_INSPECTOR_REPO
ARG A2A_INSPECTOR_REF
WORKDIR /src
RUN git clone --depth 1 --branch "${A2A_INSPECTOR_REF}" "${A2A_INSPECTOR_REPO}" repo

# Stage 1: build frontend assets
FROM node:18-alpine AS frontend-builder
WORKDIR /app

COPY --from=source /src/repo/frontend/package*.json ./
COPY --from=source /src/repo/frontend/tsconfig.json ./
COPY --from=source /src/repo/frontend/src ./src
RUN npm ci
COPY --from=source /src/repo/frontend/ ./
RUN npm rebuild esbuild
RUN npm run build

# Stage 2: assemble runtime image
FROM python:3.12-slim
WORKDIR /app

ENV UV_PYTHON_PREFER_SYSTEM=1
RUN pip install --no-cache-dir uv

COPY --from=source /src/repo/pyproject.toml ./
COPY --from=source /src/repo/uv.lock ./
RUN uv sync --no-cache
RUN uv pip install validators

COPY --from=source /src/repo/backend ./backend/

RUN mkdir -p /app/frontend
COPY --from=frontend-builder /app/public /app/frontend/public

WORKDIR /app/backend
EXPOSE 8080

CMD ["uv", "run", "--", "uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8080"]
