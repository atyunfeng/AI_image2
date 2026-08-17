FROM python:3.13-slim-bookworm
WORKDIR /app
RUN pip install --no-cache-dir uv==0.8.14
COPY backend/pyproject.toml backend/uv.lock ./
RUN uv sync --frozen --no-dev
COPY backend/alembic.ini ./alembic.ini
COPY backend/alembic ./alembic
COPY backend/src ./src
ENV PATH="/app/.venv/bin:$PATH" PYTHONPATH="/app/src"
CMD ["uvicorn", "aiimage.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
