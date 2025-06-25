import json
import boto3
import os
from dotenv import load_dotenv

# 載入 .env 檔案中的環境變數
# 確保 .env 檔案與此腳本位於相同目錄，並包含 SQS_INCOME_STATEMENT_QUEUE_URL
load_dotenv()

# 從環境變數中讀取 AWS 區域
AWS_REGION = os.environ.get('AWS_REGION', 'us-west-2')
SQS_INCOME_STATEMENT_QUEUE_URL="https://sqs.us-west-2.amazonaws.com/058264224030/stock-insight-income-statement.fifo"
# 從環境變數中讀取自訂的 Access Key ID 和 Secret Access Key
# 這些憑證用於本地運行時向 SQS 發送訊息。
# 在 ECS 中，應使用 IAM Task Role，不需此處傳遞憑證。
sqs_access_key_id = os.getenv("aws_sqs_access_key_id")
sqs_secret_access_key = os.getenv("aws_sqs_secret_access_key")

# 定義所有要發送的佇列 URL
# 確保 SQS_INCOME_STATEMENT_QUEUE_URL 在您的 .env 檔案中正確設定
SQS_QUEUES_TO_PUSH = {
    # 'cash_flow': os.environ.get('SQS_CASH_FLOW_QUEUE_URL'),
    # 'balance_sheet': os.environ.get('SQS_BALANCE_SHEET_QUEUE_URL'),
    # 'income_statement': os.environ.get('SQS_INCOME_STATEMENT_QUEUE_URL')
    'income_statement': SQS_INCOME_STATEMENT_QUEUE_URL
}

def push_companies_to_sqs(companies_file_path):
    """
    從 JSON 檔案讀取公司列表，並將每個公司作為任務訊息推送到指定的 SQS 佇列。
    """
    # 初始化 SQS 客戶端。
    # 請注意：在生產環境中（例如 ECS），推薦使用 IAM Role，避免在程式碼中直接使用 Access Key。
    sqs_client = boto3.client(
        'sqs',
        region_name=AWS_REGION,
        aws_access_key_id=sqs_access_key_id,
        aws_secret_access_key=sqs_secret_access_key
    )

    companies = {}
    try:
        with open(companies_file_path, 'r', encoding='utf-8') as f:
            companies = json.load(f)
        print(f"成功從 '{companies_file_path}' 載入 {len(companies)} 筆公司資料。")
    except FileNotFoundError:
        print(f"錯誤: 找不到公司列表檔案 '{companies_file_path}'。請確認檔案是否存在。")
        return
    except json.JSONDecodeError:
        print(f"錯誤: 公司列表檔案 '{companies_file_path}' 格式不正確，無法解析 JSON。")
        return

    # 定義爬取範圍，這些資訊將包含在 SQS 訊息中
    # 這裡的範圍需要根據您希望爬蟲處理哪些年份和季度來設定
    # 您需要根據實際需求調整這些值，例如從某年第一季到某年第四季
    start_year_roc = 105      # 起始民國年份
    start_quarter_roc = 1     # 起始季度 (1, 2, 3, 4)
    end_year_roc = 114        # 結束民國年份
    end_quarter_for_end_year = 1 # 結束年份要爬取的最終季度 (例如：4 代表爬到該年第四季)

    for stock_code, company_name in companies.items():
        message_body = {
            "stock_code": stock_code,
            "company_name": company_name,
            "start_year_roc": start_year_roc,
            "start_quarter_roc": start_quarter_roc,
            "end_year_roc": end_year_roc,
            "end_quarter_for_end_year": end_quarter_for_end_year
        }
        json_message = json.dumps(message_body, ensure_ascii=False)

        for queue_type, queue_url in SQS_QUEUES_TO_PUSH.items():
            # ** DEBUG 訊息：用於確認讀取到的 URL **
            print(f"嘗試為佇列 '{queue_type}' 讀取到的 URL: '{queue_url}'")
            
            if not queue_url:
                print(f"錯誤: 佇列類型 '{queue_type}' 的 URL 未在環境變數中設定。跳過此佇列。")
                continue
            
            try:
                # 對於 FIFO 佇列，必須提供 MessageGroupId。
                # 這裡使用 stock_code 作為 MessageGroupId，確保同一隻股票的任務被按順序處理。
                # 如果啟用了內容去重複，MessageDeduplicationId 是可選的，否則也需要提供一個唯一的 ID。
                sqs_client.send_message(
                    QueueUrl=queue_url,
                    MessageBody=json_message,
                    MessageGroupId=stock_code # 對於 FIFO 佇列是必需的
                    # MessageDeduplicationId='unique_id_for_this_message' # 如果未啟用內容去重複，則需要此項
                )
                print(f"已發送任務 {stock_code} {company_name} 到 {queue_type} 佇列")
            except Exception as e:
                print(f"發送任務 {stock_code} {company_name} 到 {queue_type} 佇列失敗：{e}")

if __name__ == "__main__":
    # 請根據您實際存放公司列表的檔案名稱來修改
    companies_list_file = 'companies_list_source.json' 
    push_companies_to_sqs(companies_list_file)
