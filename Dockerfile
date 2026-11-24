# One image for the whole app (docs/deploy.md): the website is built in the first stage and the API
# serves it. Build from the repository root: docker build -t trove .

FROM node:22-slim AS web
WORKDIR /build/web
COPY web/package.json web/package-lock.json ./
RUN npm ci
COPY web/ ./
RUN npm run build

FROM python:3.13-slim
ENV PYTHONUNBUFFERED=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    ENVIRONMENT=production
RUN pip install --no-cache-dir uv
WORKDIR /app/api
COPY api/pyproject.toml api/uv.lock ./
RUN uv sync --frozen --no-dev
COPY api/ ./
COPY --from=web /build/web/dist /app/web/dist
# The host sets PORT. Secrets and settings come from its environment, never from the image.
CMD ["sh", "-c", "exec uv run --no-sync uvicorn trove.serve:site --host 0.0.0.0 --port ${PORT:-8000}"]
