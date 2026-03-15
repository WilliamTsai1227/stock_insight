import os
import json
import time
import urllib.request
from datetime import datetime, timedelta, timezone
from pymongo import MongoClient
from pymongo.server_api import ServerApi
from dotenv import load_dotenv

# 1. 載入當前目錄下的 .env 檔案
env_path = os.path.join(os.path.dirname(__file__), '.env')
load_dotenv(env_path)

# 設定環境變數
DB_USER = os.getenv('mongodb_user')
DB_PASSWORD = os.getenv('mongodb_password')
DISCORD_WEBHOOK_URL = os.getenv('DISCORD_WEBHOOK_URL')

# MongoDB 連線字串
MONGO_URI = f"mongodb+srv://{DB_USER}:{DB_PASSWORD}@stock-main.kbyokcd.mongodb.net/?retryWrites=true&w=majority&appName=stock-main"

def get_mongodb_client():
    return MongoClient(MONGO_URI, server_api=ServerApi('1'))

def format_timestamp(ts):
    """將 Unix 時間戳轉為台灣時間 (UTC+8)"""
    tz_taiwan = timezone(timedelta(hours=8))
    dt = datetime.fromtimestamp(ts, tz=tz_taiwan)
    return dt.strftime('%Y-%m-%d %H:%M:%S')

def send_discord_notification(content):
    """發送訊息到 Discord Webhook，並支援自動分段發送 (處理 2000 字限制)"""
    if not DISCORD_WEBHOOK_URL:
        print("錯誤：找不到 DISCORD_WEBHOOK_URL，請檢查 .env 檔案。")
        return

    # Discord 單則訊息上限 2000 字，安全起見設為 1900
    MAX_LENGTH = 1900
    
    # 將內容按行分割，並分段組合
    lines = content.split('\n')
    chunks = []
    current_chunk = ""

    for line in lines:
        # 如果單行就超過上限（極少見），強制切斷
        if len(line) > MAX_LENGTH:
            line = line[:MAX_LENGTH]
            
        if len(current_chunk) + len(line) + 1 > MAX_LENGTH:
            chunks.append(current_chunk)
            current_chunk = line + '\n'
        else:
            current_chunk += line + '\n'
    
    if current_chunk:
        chunks.append(current_chunk)

    # 依序發送每一段
    for i, chunk in enumerate(chunks):
        if len(chunks) > 1:
            header = f"(第 {i+1}/{len(chunks)} 部分)\n"
            chunk = header + chunk

        data = {"content": chunk}
        req = urllib.request.Request(
            DISCORD_WEBHOOK_URL,
            data=json.dumps(data).encode('utf-8'),
            headers={
                'Content-Type': 'application/json',
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36'
            }
        )
        try:
            with urllib.request.urlopen(req) as response:
                print(f"[{datetime.now()}] Discord 通知分段 {i+1} 發送成功！")
            # 稍微延遲避免觸發 Discord 的 Rate Limit (頻率限制)
            time.sleep(0.5)
        except Exception as e:
            print(f"發送 Discord 失敗: {e}")

def run_job():
    """執行爬取與彙整任務"""
    print(f"[{datetime.now()}] 開始執行彙整任務...")
    try:
        client = get_mongodb_client()
        db = client['stock_insight']
        collection = db['AI_news_analysis']

        # 1. 抓取最新的 100 條資料
        cursor = collection.find().sort("publishAt", -1).limit(100)
        docs = list(cursor)

        if not docs:
            print("資料庫中沒有 AI_news_analysis 資料。")
            return

        # 2. 資料處理 (去重邏輯)
        unique_stocks = []
        seen_stocks = set()
        unique_industries = []
        seen_industries = set()
        unique_source_news = []
        seen_news = set()
        timestamps = []

        for doc in docs:
            if "publishAt" in doc:
                timestamps.append(doc["publishAt"])
            
            # 股票去重: [國家, 代碼, 名稱] 完全一致才去重
            for stock in doc.get("stock_list", []):
                if isinstance(stock, list) and len(stock) >= 3:
                    stock_tuple = (stock[0], stock[1], stock[2])
                    if stock_tuple not in seen_stocks:
                        seen_stocks.add(stock_tuple)
                        unique_stocks.append(stock)
            
            # 產業去重
            for industry in doc.get("industry_list", []):
                ind = industry.strip()
                if ind and ind not in seen_industries:
                    seen_industries.add(ind)
                    unique_industries.append(ind)
            
            # 新聞來源標題去重
            for news in doc.get("source_news", []):
                title = news.get("title", "").strip()
                if title and title not in seen_news:
                    seen_news.add(title)
                    unique_source_news.append(title)

        # 3. 產出報告內容
        start_time = format_timestamp(min(timestamps)) if timestamps else "未知"
        end_time = format_timestamp(max(timestamps)) if timestamps else "未知"

        report_content = f"### 📊 AI 推薦股票及產業報告\n"
        report_content += f"**時間區間**：`{start_time}` ~ `{end_time}`\n\n"
        
        report_content += "**🌟 推薦股票**：\n"
        if unique_stocks:
            for s in unique_stocks:
                report_content += f"• 國家: `{s[0]}`, 代碼: `{s[1]}`, 名稱: **{s[2]}**\n"
        else:
            report_content += "• 目前無推薦股票\n"
        
        report_content += f"\n**🏭 推薦產業**：\n"
        if unique_industries:
            for i in unique_industries:
                report_content += f"• `{i}`\n"
        else:
            report_content += "• 目前無推薦產業\n"
        
        report_content += f"\n**📰 新聞來源摘要** ({len(unique_source_news)} 則)：\n"
        if unique_source_news:
            for t in unique_source_news:
                report_content += f"• 「{t}」\n"
        else:
            report_content += "• 目前無來源新聞\n"

        # 4. 發送
        send_discord_notification(report_content)

    except Exception as e:
        print(f"執行出錯: {e}")

def get_seconds_until_next_run():
    """計算距離下一次執行時間的秒數 (依照台灣時間動態調整)"""
    tz_taiwan = timezone(timedelta(hours=8))
    now = datetime.now(tz_taiwan)
    
    # 定義排程時間點 (24小時制，時:分)
    # 早上 07:00 開始，每 1.5 小時：07:00, 08:30, 10:00, 11:30, 13:00
    # 下午 13:00 開始，每 3 小時：16:00, 19:00, 22:00, 01:00, 04:00
    schedule = [
        (1, 0), (4, 0), (7, 0), (8, 30), (10, 0), (11, 30), (13, 0), (16, 0), (19, 0), (22, 0)
    ]
    
    # 轉換成今日的所有排程 datetime 物件
    future_times = []
    for hour, minute in schedule:
        t = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
        # 如果排程時間已經過了，就設為明天同一個時間
        if t <= now:
            t += timedelta(days=1)
        future_times.append(t)
    
    # 找出最近的一個未來時間
    next_run = min(future_times)
    diff = (next_run - now).total_seconds()
    
    return int(diff), next_run

if __name__ == "__main__":
    print("=== Discord 本地動態時段通知腳本已啟動 ===")
    
    # 啟動時先執行一次，或是可以選擇等待到 07:00 再執行
    # 這裡選擇啟動時先跑一次，之後進入排程
    run_job()
    
    while True:
        wait_seconds, next_run_time = get_seconds_until_next_run()
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 任務完成。")
        print(f"下次執行台灣時間：{next_run_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"需要等待：{wait_seconds / 3600:.2f} 小時 ({wait_seconds} 秒)...")
        
        time.sleep(wait_seconds)
        run_job()
