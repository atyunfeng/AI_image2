FROM ghcr.io/astral-sh/uv:0.8.14-python3.13-bookworm-slim
WORKDIR /app
COPY backend/pyproject.toml backend/uv.lock ./
RUN uv sync --frozen --no-dev
COPY backend/alembic.ini ./alembic.ini
COPY backend/alembic ./alembic
COPY backend/src ./src
ENV PATH="/app/.venv/bin:$PATH" PYTHONPATH="/app/src"
CMD ["uvicorn", "aiimage.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
