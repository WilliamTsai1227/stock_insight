# 範例：將任務推送到所有相關佇列
import json
import boto3
import os
from dotenv import load_dotenv

# 載入 .env 檔案中的環境變數
load_dotenv()

# 從環境變數中讀取 AWS 區域
AWS_REGION = os.environ.get('AWS_REGION', 'us-west-2')

# 從環境變數中讀取自訂的 Access Key ID 和 Secret Access Key
sqs_access_key_id = os.getenv("aws_sqs_access_key_id")
sqs_secret_access_key = os.getenv("aws_sqs_secret_access_key")

# 定義所有要發送的佇列 URL (現在會從 .env 或系統環境變數中讀取)
SQS_QUEUES_TO_PUSH = {
    'cash_flow': os.environ.get('SQS_CASH_FLOW_QUEUE_URL')
    # 'balance_sheet': os.environ.get('SQS_BALANCE_SHEET_QUEUE_URL'),
    # 'income_statement': os.environ.get('SQS_INCOME_STATEMENT_QUEUE_URL')
}

def push_companies_to_sqs(companies_file_path):
    # 這裡明確地傳遞您的自訂 Access Key ID 和 Secret Access Key
    sqs_client = boto3.client(
        'sqs',
        region_name=AWS_REGION,
        aws_access_key_id=sqs_access_key_id,
        aws_secret_access_key=sqs_secret_access_key
    )

    companies = {}
    with open(companies_file_path, 'r', encoding='utf-8') as f:
        companies = json.load(f)

    for stock_code, company_name in companies.items():
        message_body = {
            "stock_code": stock_code,
            "company_name": company_name
        }
        json_message = json.dumps(message_body, ensure_ascii=False)

        for queue_type, queue_url in SQS_QUEUES_TO_PUSH.items():
            if not queue_url:
                print(f"錯誤: 佇列類型 {queue_type} 的 URL 未在環境變數中設定。跳過此佇列。")
                continue
            try:
                sqs_client.send_message(
                    QueueUrl=queue_url,
                    MessageBody=json_message
                )
                print(f"已發送任務 {stock_code} {company_name} 到 {queue_type} 佇列")
            except Exception as e:
                print(f"發送任務 {stock_code} {company_name} 到 {queue_type} 佇列失敗：{e}")

if __name__ == "__main__":
    companies_list_file = 'enriched_missing_stocks.json'
    push_companies_to_sqs(companies_list_file)