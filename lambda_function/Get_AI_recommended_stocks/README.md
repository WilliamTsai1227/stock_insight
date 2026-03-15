# AI 推薦股票與產業通知系統 (AI Stock & Industry Notifier)

此專案包含兩個主要腳本，用於從 MongoDB 提取 AI 分析結果，並透過 Email (AWS SES) 或 Discord Webhook 發送摘要報告。

## 檔案說明

1.  **`Get_AI_recommended_stocks.py`**:
    *   **用途**: AWS Lambda 專用腳本。
    *   **功能**: 抓取最近 200 條 AI 分析，透過 AWS SES 發送 Email 並串接 Discord Webhook。
    *   **適用場景**: 部署在 AWS 上，使用 EventBridge 定時觸發。

2.  **`local_discord_notifier.py`**:
    *   **用途**: 長時間不關機的本地電腦專用腳本。
    *   **功能**: 
        *   抓取最近 **100 條** AI 分析紀錄。
        *   **自動分段發送**: 內容若超過 Discord 的 2000 字限制會自動拆分，確保報表完整。
        *   **美化排版**: 採用清單式換行排版，方便手機閱讀。
        *   **動態排程時段 (台灣時間)**: 
            *   **密集偵測時段 (07:00 ~ 13:00)**: 每 **1.5 小時** 執行一次。
                *   執行時間點: `07:00`, `08:30`, `10:00`, `11:30`, `13:00`
            *   **一般偵測時段 (13:00 ~ 隔日 07:00)**: 每 **3 小時** 執行一次。
                *   執行時間點: `16:00`, `19:00`, `22:00`, `01:00`, `04:00`
    *   **適用場景**: 在個人電腦 (如 Mac mini) 24 小時執行。

## 安裝與設定

### 1. 環境變數 (.env)
在 `lambda_function/Get_AI_recommended_stocks/` 目錄下建立 `.env` 檔案，內容如下：

```env
mongodb_user=你的資料庫帳號
mongodb_password=你的資料庫密碼
DISCORD_WEBHOOK_URL=你的Discord頻道Webhook網址

# AWS SES 設定 (僅 Get_AI_recommended_stocks.py 需要)
SES_SENDER_EMAIL=驗證過的發信箱
SES_RECEIVER_EMAIL=收信箱
AWS_REGION=us-west-2
```

### 2. 安裝套件
確保你的 Python 環境已安裝必要套件：
```bash
pip install pymongo python-dotenv boto3
```

## 執行本地腳本 (Local Mode)
打開 Terminal，執行以下指令：
```bash
python3 local_discord_notifier.py
```
啟動後會立刻發送一次，隨後進入自動排程。

## 注意事項
*   **Discord 頻率限制**: 本地腳本已內建 0.5 秒延遲，避免連續發送過快被封鎖。
*   **MongoDB 連線**: 確保執行環境的 IP 已經在 MongoDB Atlas 的 Network Access 白名單中。
*   **電腦休眠**: 若電腦進入休眠模式，本地腳本會停止運行，建議將電腦設為「永不休眠」。
