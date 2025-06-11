# 使用一個包含 Python 和 Chrome 瀏覽器的基礎映像檔
FROM --platform=linux/amd64 selenium/standalone-chrome:4.20.0 

# 以下保持不變
WORKDIR /app
COPY requirements.txt .
USER root
RUN apt-get update && apt-get install -y python3-pip \
    && pip3 install --no-cache-dir -r requirements.txt \
    && rm -rf /var/lib/apt/lists/*
COPY cash_flow_crawler_quarter_to_S3.py .
ENTRYPOINT ["python3", "cash_flow_crawler_quarter_to_S3.py"]