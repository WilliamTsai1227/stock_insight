import os
import json
import time
import boto3
import urllib.request
from datetime import datetime, timedelta, timezone
from pymongo import MongoClient
from pymongo.server_api import ServerApi

# Load environment variables if running locally
if os.getenv("AWS_EXECUTION_ENV") is None:
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        pass

# Configuration from environment variables
DB_USER = os.getenv('mongodb_user')
DB_PASSWORD = os.getenv('mongodb_password')
DISCORD_WEBHOOK_URL = os.getenv('DISCORD_WEBHOOK_URL')
SENDER_EMAIL = os.getenv('SES_SENDER_EMAIL')
RECEIVER_EMAIL = os.getenv('SES_RECEIVER_EMAIL')
AWS_REGION = os.getenv('AWS_REGION', 'us-west-2')

# MongoDB Connection URI
MONGO_URI = f"mongodb+srv://{DB_USER}:{DB_PASSWORD}@stock-main.kbyokcd.mongodb.net/?retryWrites=true&w=majority&appName=stock-main"

def get_mongodb_client():
    return MongoClient(MONGO_URI, server_api=ServerApi('1'))

def format_timestamp(ts):
    """Convert Unix timestamp to readable string in Taiwan time (UTC+8)"""
    # Create a timezone object for UTC+8
    tz_taiwan = timezone(timedelta(hours=8))
    # Convert timestamp to datetime object with Taiwan timezone
    dt = datetime.fromtimestamp(ts, tz=tz_taiwan)
    return dt.strftime('%Y-%m-%d %H:%M:%S')

def send_discord_notification(content):
    if not DISCORD_WEBHOOK_URL:
        print("DISCORD_WEBHOOK_URL not set, skipping Discord notification.")
        return
    
    data = {"content": content}
    req = urllib.request.Request(
        DISCORD_WEBHOOK_URL,
        data=json.dumps(data).encode('utf-8'),
        headers={'Content-Type': 'application/json'}
    )
    try:
        with urllib.request.urlopen(req) as response:
            print(f"Discord notification sent. Status: {response.status}")
    except Exception as e:
        print(f"Failed to send Discord notification: {e}")

def send_email_notification(subject, body):
    if not SENDER_EMAIL or not RECEIVER_EMAIL:
        print("SENDER_EMAIL or RECEIVER_EMAIL not set, skipping email notification.")
        return
    
    ses = boto3.client('ses', region_name=AWS_REGION)
    try:
        response = ses.send_email(
            Source=SENDER_EMAIL,
            Destination={'ToAddresses': [RECEIVER_EMAIL]},
            Message={
                'Subject': {'Data': subject},
                'Body': {'Text': {'Data': body}}
            }
        )
        print(f"Email sent. Message ID: {response['MessageId']}")
    except Exception as e:
        print(f"Failed to send email: {e}")

def lambda_handler(event, context):
    try:
        client = get_mongodb_client()
        db = client['stock_insight']
        collection = db['AI_news_analysis']

        # 1. Fetch the latest 200 documents
        # Sorted by publishAt descending
        cursor = collection.find().sort("publishAt", -1).limit(200)
        docs = list(cursor)

        if not docs:
            print("No data found in AI_news_analysis.")
            return {"statusCode": 200, "body": "No data found"}

        # 2. Process Data
        unique_stocks = [] # List of [country, code, name]
        seen_stocks = set() # Set of tuples (country, code, name)
        
        unique_industries = [] # List of unique strings
        seen_industries = set()
        
        unique_source_news = [] # List of unique titles
        seen_news = set()
        
        timestamps = []

        for doc in docs:
            # Timestamps
            if "publishAt" in doc:
                timestamps.append(doc["publishAt"])
            
            # Stocks
            stock_list = doc.get("stock_list", [])
            for stock in stock_list:
                if isinstance(stock, list) and len(stock) >= 3:
                    stock_tuple = (stock[0], stock[1], stock[2])
                    if stock_tuple not in seen_stocks:
                        seen_stocks.add(stock_tuple)
                        unique_stocks.append(stock)
            
            # Industries
            industry_list = doc.get("industry_list", [])
            for industry in industry_list:
                if industry.strip() and industry.strip() not in seen_industries:
                    seen_industries.add(industry.strip())
                    unique_industries.append(industry.strip())
            
            # News Sources
            source_news = doc.get("source_news", [])
            for news in source_news:
                title = news.get("title", "").strip()
                if title and title not in seen_news:
                    seen_news.add(title)
                    unique_source_news.append(title)

        # Time range
        if timestamps:
            start_time = format_timestamp(min(timestamps))
            end_time = format_timestamp(max(timestamps))
        else:
            start_time = "Unknown"
            end_time = "Unknown"

        # 3. Generate Report Content
        report_title = f"{start_time} ~ {end_time} 的推薦股票及產業"
        
        report_body = f"標題：{report_title}\n"
        report_body += f"以下為 AI 在 {start_time} ~ {end_time} 閱讀新聞後的推薦股票及產業\n\n"
        
        report_body += "推薦股票：\n"
        if unique_stocks:
            for s in unique_stocks:
                report_body += f'國家"{s[0]}", 股票代碼"{s[1]}", 股票名稱："{s[2]}"\n'
        else:
            report_body += "無\n"
        
        report_body += "\n推薦產業："
        if unique_industries:
            report_body += ", ".join([f'"{i}"' for i in unique_industries])
        else:
            report_body += "無"
        report_body += "\n\n"
        
        report_body += "新聞來源：\n"
        if unique_source_news:
            report_body += ", ".join([f'"{t}"' for t in unique_source_news])
        else:
            report_body += "無"

        print("--- Report Generated ---")
        print(report_body)
        print("------------------------")

        # 4. Send Notifications
        send_email_notification(report_title, report_body)
        send_discord_notification(report_body)

        return {
            "statusCode": 200,
            "body": json.dumps({"message": "Report sent successfully", "title": report_title})
        }

    except Exception as e:
        error_msg = f"Error in Get_AI_recommended_stocks: {str(e)}"
        print(error_msg)
        return {
            "statusCode": 500,
            "body": json.dumps({"error": error_msg})
        }

if __name__ == "__main__":
    lambda_handler({}, {})
