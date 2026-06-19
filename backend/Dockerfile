FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

RUN groupadd --system app && useradd --system --gid app app

COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

COPY pytest.ini .
COPY alembic.ini .
COPY alembic ./alembic
COPY app ./app

RUN mkdir -p /app/storage/photos /app/app/tests/reports \
    && chown -R app:app /app \
    && chmod -R u+rwX /app/app/tests

USER app

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
