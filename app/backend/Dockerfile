# 構建階段
FROM python:3.11-slim as builder

WORKDIR /app

# 安裝構建依賴
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# 複製並安裝依賴
COPY requirements.txt .
RUN pip wheel --no-cache-dir --no-deps --wheel-dir /app/wheels -r requirements.txt

# 運行階段
FROM python:3.11-slim

WORKDIR /app/backend

# 設置環境變數
ENV PYTHONPATH=/app/backend \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# 從構建階段複製輪子並安裝
COPY --from=builder /app/wheels /wheels
COPY --from=builder /app/requirements.txt .
RUN pip install --no-cache /wheels/*

# 複製應用程式代碼
COPY . .

# 暴露端口
EXPOSE 8000

# 運行應用
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"] 