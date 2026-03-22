FROM python:3.13-slim AS builder

RUN apt-get update && apt-get install -y \
    curl build-essential libpq-dev && rm -rf /var/lib/apt/lists/*
    
ENV POETRY_VERSION=2.3.2 \
    POETRY_VIRTUALENVS_IN_PROJECT=true \
    POETRY_NO_INTERACTION=1
    
RUN pip install "poetry==$POETRY_VERSION"
    
WORKDIR /app
COPY pyproject.toml poetry.lock ./
RUN poetry install --no-root --no-ansi
    
FROM python:3.13-slim AS runtime
    
RUN apt-get update && apt-get install -y libpq-dev && rm -rf /var/lib/apt/lists/*
RUN useradd -m appuser
    
WORKDIR /app

RUN mkdir -p /app/logs && chown -R appuser:appuser /app
    
COPY --from=builder --chown=appuser:appuser /app/.venv /app/.venv
COPY --chown=appuser:appuser app /app/app
COPY --chown=appuser:appuser tests /app/tests
COPY --chown=appuser:appuser alembic /app/alembic
COPY --chown=appuser:appuser alembic.ini /app/
COPY --chown=appuser:appuser pyproject.toml /app/
    
ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1
    
USER appuser
    
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]