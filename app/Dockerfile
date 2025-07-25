
FROM python:3.11-slim AS builder


WORKDIR /tmp/build


RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*


COPY app/requirements.txt .


RUN pip wheel --no-cache-dir --no-deps --wheel-dir /app/wheels -r requirements.txt


FROM python:3.11-slim


WORKDIR /app


ENV PYTHONPATH=/app/backend \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1


COPY --from=builder /app/wheels /wheels

COPY --from=builder /tmp/build/requirements.txt .


RUN pip install --no-cache /wheels/*


COPY app/ .


EXPOSE 8000


CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]