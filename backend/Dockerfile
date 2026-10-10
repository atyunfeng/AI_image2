FROM python:3.14-slim-bookworm
WORKDIR /app
RUN apt-get update \
    && apt-get install -y --no-install-recommends fonts-noto-cjk \
    && rm -rf /var/lib/apt/lists/*
RUN pip install --no-cache-dir uv==0.8.14
RUN groupadd --system aiimage && useradd --system --gid aiimage --home-dir /app aiimage
COPY backend/pyproject.toml backend/uv.lock ./
COPY backend/src ./src
RUN uv sync --frozen --no-dev
COPY backend/alembic.ini ./alembic.ini
COPY backend/alembic ./alembic
ENV PATH="/app/.venv/bin:$PATH" PYTHONPATH="/app/src"
RUN chown -R aiimage:aiimage /app
USER aiimage
CMD ["uvicorn", "aiimage.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
