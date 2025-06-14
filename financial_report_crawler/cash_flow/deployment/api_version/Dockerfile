# Dockerfile
# 使用官方 Python 3.11 映像，輕量級且包含 Debian (buster)
# 明確指定平台為 linux/amd64，確保在 x86 架構上執行
FROM --platform=linux/amd64 python:3.11-slim-buster

# 設定工作目錄
WORKDIR /app

# 將 requirements.txt 複製到容器中，並安裝依賴
# 使用 --no-cache-dir 減少映像大小
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 將應用程式碼複製到容器中
COPY cash_flow_api_crawler_ecs.py .

# 定義容器啟動時執行的命令
CMD ["python", "cash_flow_api_crawler_ecs.py"]