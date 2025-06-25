import os
import json
import time
import logging
import boto3
import requests
from datetime import datetime

# --- 配置區塊：透過環境變數從 ECS 任務定義中注入 ---
# 不再從 .env 檔案載入，這些變數將由 ECS 環境提供
AWS_REGION = os.environ.get('AWS_REGION', 'us-west-2')
S3_BUCKET_NAME = os.environ.get('Financial_Report_S3_BUCKET_NAME')
# 更新為綜合損益表的 S3 前綴 (確保這個環境變數在 ECS 任務定義中設置)
S3_RAW_DATA_PREFIX = os.environ.get('Financial_Report_S3_INCOME_STATEMENT_RAW_DATA_PREFIX', 'raw-data/income_statement/')
# SQS 佇列 URL (確保這個環境變數在 ECS 任務定義中設置)
SQS_QUEUE_URL = os.environ.get('SQS_INCOME_STATEMENT_QUEUE_URL') 

class IncomeStatementAPICrawler:
    def __init__(self):
        # 更新 API URL 為綜合損益表
        self.api_url = "https://mops.twse.com.tw/mops/api/t164sb04"
        self.headers = {
            "Accept": "*/*",
            "Accept-Encoding": "gzip, deflate, br, zstd",
            "Accept-Language": "zh-TW,zh;q=0.9",
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Content-Type": "application/json",
            "Host": "mops.twse.com.tw",
            "Origin": "https://mops.twse.com.tw",
            "Pragma": "no-cache",
            "Referer": "https://mops.twse.com.tw/mops/#/web/t164sb04", # 更新 Referer
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-origin",
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36",
            "sec-ch-ua": "\"Chromium\";v=\"136\", \"Google Chrome\";v=\"136\", \"Not.A/Brand\";v=\"99\"",
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": "\"macOS\""
        }
        
        # S3 客戶端：依賴 ECS Task Role 提供的憑證
        self.s3_client = boto3.client('s3', region_name=AWS_REGION)
        # SQS 客戶端：依賴 ECS Task Role 提供的憑證
        self.sqs_client = boto3.client('sqs', region_name=AWS_REGION)
        
        # 將 S3_BUCKET_NAME 和 S3_RAW_DATA_PREFIX 作為實例變數，方便存取
        self.S3_BUCKET_NAME = S3_BUCKET_NAME
        self.S3_RAW_DATA_PREFIX = S3_RAW_DATA_PREFIX

        self._setup_root_logger()
        
    def _setup_root_logger(self):
        root_logger = logging.getLogger()
        root_logger.setLevel(logging.INFO)
        # 移除現有的 root logger handlers，避免重複
        if root_logger.handlers:
            for handler in root_logger.handlers[:]:
                root_logger.removeHandler(handler)
        
        console_handler = logging.StreamHandler()
        # 這裡的格式器是給 root logger 使用
        console_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        console_handler.setFormatter(console_formatter)
        root_logger.addHandler(console_handler)

    def _get_logger(self, stock_code, company_name):
        logger_name = f"{stock_code}_{company_name}_income_statement_api_crawler"
        logger = logging.getLogger(logger_name)
        logger.setLevel(logging.INFO)

        # 檢查 logger 是否已經有 handler。
        # 如果沒有，則為其添加一個 StreamHandler。
        # 這樣可以避免每個公司 logger 都重複輸出到控制台。
        if not logger.handlers:
            # 阻止 logger 將訊息傳播給其父 logger (root logger)
            # 這樣每個公司 logger 的訊息就只會透過它自己的 handler 輸出一次
            # 並且會帶有 [股票代碼 公司名稱] 的前綴
            logger.propagate = False 
            
            console_handler = logging.StreamHandler()
            # 這裡的格式器是給特定公司 logger 使用，帶有股票代碼和公司名稱
            formatter_string = f'%(asctime)s - %(levelname)s - [{stock_code} {company_name}] - %(message)s'
            console_formatter = logging.Formatter(formatter_string)
            console_handler.setFormatter(console_formatter) 
            logger.addHandler(console_handler)
        
        return logger

    def fetch_data_from_api(self, stock_code, year_roc, quarter, logger):
        payload = {
            "companyId": stock_code,
            "dataType": "2", # 2 代表合併報表
            "season": str(quarter),
            "year": str(year_roc),
            "subsidiaryCompanyId": ""
        }
        logger.info(f"發送請求 payload: {payload}")

        try:
            response = requests.post(self.api_url, headers=self.headers, json=payload, timeout=15)
            response.raise_for_status()
            
            json_response = response.json()
            
            if json_response.get('code') == 200 and json_response.get('result'):
                return json_response['result']
            elif json_response.get('message') == "查詢無資料":
                logger.info(f"API 查詢 民國 {year_roc} 第 {quarter} 季：查無資料。")
                return None
            else:
                # 這裡捕捉 '查無相符資料' 或其他非成功狀態碼
                logger.warning(f"API 回應非成功狀態碼或無結果：{json_response.get('code')} - {json_response.get('message')}，原始回應：{response.text}")
                return None
        except requests.exceptions.HTTPError as e:
            logger.error(f"API 請求失敗，HTTP 狀態碼：{e.response.status_code} - {e.response.text}")
            return None
        except requests.exceptions.ConnectionError as e:
            logger.error(f"API 連線錯誤：{e}")
            return None
        except requests.exceptions.Timeout as e:
            logger.error(f"API 請求超時：{e}")
            return None
        except json.JSONDecodeError as e:
            logger.error(f"API 回應非 JSON 格式：{e} - {response.text}")
            return None
        except Exception as e:
            logger.error(f"API 請求發生未預期錯誤：{e}", exc_info=True)
            return None

    def _parse_time_period_from_title(self, title_main, default_year, default_quarter):
        """
        從標題字串中解析出年份、季度和數據類型 (當季/累積/年度累積)。
        範例: "105年第2季" -> 105, 2, "quarterly"
        範例: "105年01月01日至105年06月30日" -> 105, 2, "accumulated"
        範例: "105年度" -> 105, 4, "annual_accumulated"
        """
        year_roc = None
        quarter = None
        data_type = None # "quarterly", "accumulated", "annual_accumulated"
        
        # 判斷是否為「X年度」格式 (通常用於第四季的年度數據)
        if "年度" in title_main:
            try:
                # 提取年份，例如 "105年度" -> "105"
                year_roc_str = title_main.replace('年度', '').strip()
                if year_roc_str.isdigit():
                    year_roc = int(year_roc_str)
                    quarter = 4 # 年度數據對應到第四季
                    data_type = "annual_accumulated"
                    return year_roc, quarter, data_type 
            except ValueError:
                pass

        # 判斷是否為「X年第Y季」格式 (當季數據)
        elif "年第" in title_main and "季" in title_main:
            try:
                parts = title_main.split('年第')
                year_roc = int(parts[0])
                quarter = int(parts[1].replace('季', ''))
                data_type = "quarterly"
                return year_roc, quarter, data_type
            except (ValueError, IndexError):
                pass
        
        # 判斷是否為「X年X月X日至X年X月X日」格式 (累積數據)
        elif "年" in title_main and "月" in title_main and "日" in title_main and "至" in title_main:
            try:
                # 提取結束日期中的年份和月份來判斷季度
                end_date_str = title_main.split('至')[1]
                end_year_str = end_date_str.split('年')[0]
                end_month_str = end_date_str.split('年')[1].split('月')[0]
                
                year_roc = int(end_year_str)
                end_month = int(end_month_str)
                
                quarter = (end_month - 1) // 3 + 1
                data_type = "accumulated"
                return year_roc, quarter, data_type
            except (ValueError, IndexError):
                pass
        
        return None, None, None # 如果不符合任何預期格式，則返回 None

    def crawl_income_statement(self, stock_code, company_name, start_year_roc, start_quarter_roc, end_year_roc, end_quarter_for_end_year):
        logger = self._get_logger(stock_code, company_name)

        for year_to_query in range(start_year_roc, end_year_roc + 1):
            quarters_to_crawl = [1, 2, 3, 4]
            
            # 處理起始年份的季度
            if year_to_query == start_year_roc:
                quarters_to_crawl = [q for q in quarters_to_crawl if q >= start_quarter_roc]
            
            # 處理結束年份的季度
            if year_to_query == end_year_roc:
                quarters_to_crawl = [q for q in quarters_to_crawl if q <= end_quarter_for_end_year]
            
            # 如果某個年份經過篩選後沒有季度可爬，則跳過
            if not quarters_to_crawl:
                logger.info(f"民國 {year_to_query} 年沒有符合條件的季度可爬取，跳過此年份。")
                continue

            for quarter_to_query in quarters_to_crawl:
                logger.info(f"正在透過 API 查詢 民國 {year_to_query} 第 {quarter_to_query} 季的綜合損益表數據...")
                
                # 將重試次數從 2 改為 1 (表示總共嘗試 2 次：原始嘗試 + 1 次重試)
                retries = 1 
                for attempt in range(retries):
                    api_result = self.fetch_data_from_api(stock_code, year_to_query, quarter_to_query, logger)
                    
                    if api_result:
                        report_list = api_result.get('reportList', [])
                        titles = api_result.get('titles', [])
                        
                        parsed_period_data = [] 

                        # 從 titles 中解析出所有有效的時間週期欄位
                        for i in range(1, len(titles)): # 跳過第一個「會計項目」欄位
                            title_info = titles[i]
                            main_title = title_info.get('main', '')
                            sub_titles = title_info.get('sub', []) 

                            # 確保子標題是金額和百分比，以確認這是有效的數據欄位
                            if not (len(sub_titles) == 2 and 
                                    sub_titles[0].get('main') == '金額' and 
                                    sub_titles[1].get('main') == '%'):
                                logger.warning(f"標題 '{main_title}' 的子標題格式不符預期，跳過此欄位解析。")
                                continue

                            # 嘗試解析標題
                            parsed_year, parsed_quarter, data_type = self._parse_time_period_from_title(main_title, year_to_query, quarter_to_query)
                            
                            if parsed_year is not None and parsed_quarter is not None and data_type is not None:
                                amount_idx = (i - 1) * 2 + 1 
                                percent_idx = (i - 1) * 2 + 2
                                parsed_period_data.append({
                                    "year_roc": parsed_year,
                                    "quarter": parsed_quarter,
                                    "data_type": data_type,
                                    "amount_idx": amount_idx,
                                    "percent_idx": percent_idx
                                })
                            else:
                                logger.warning(f"無法從標題 '{main_title}' 解析出有效的年份/季度/數據類型，跳過此欄位。")
                        
                        if not parsed_period_data:
                            logger.warning(f"在 API 回應的表頭中未找到 民國 {year_to_query} 第 {quarter_to_query} 季的有效數據欄位，可能無數據。")
                            break # 跳出重試迴圈

                        # --- 新增的 EPS 處理邏輯開始 ---
                        eps_data_by_period = { (p['year_roc'], p['quarter'], p['data_type']): { '基本每股盈餘': [None, None], '稀釋每股盈餘': [None, None] } 
                                                for p in parsed_period_data }
                        
                        for row_idx, row in enumerate(report_list):
                            if len(row) > 0:
                                raw_item_name = row[0]
                                cleaned_item_name = raw_item_name.lstrip(' 　').strip()

                                # 優先處理直接帶有數值的 EPS 項目，無論縮排與否
                                # 這裡我們尋找「基本每股盈餘」和「稀釋每股盈餘」的最終數值
                                if cleaned_item_name in ["基本每股盈餘", "稀釋每股盈餘"]:
                                    # 遍歷所有時間週期，找到對應的數值
                                    for period_info in parsed_period_data:
                                        amount_idx = period_info['amount_idx']
                                        percent_idx = period_info['percent_idx']
                                        period_key = (period_info['year_roc'], period_info['quarter'], period_info['data_type'])

                                        if len(row) > percent_idx:
                                            value = None
                                            percent = None
                                            
                                            value_str = row[amount_idx].strip()
                                            if value_str:
                                                try:
                                                    value = float(value_str.replace(',', ''))
                                                except ValueError:
                                                    pass

                                            percent_str = row[percent_idx].strip()
                                            if percent_str:
                                                try:
                                                    percent = float(percent_str)
                                                except ValueError:
                                                    pass
                                            
                                            # 如果當前行的這個項目的數值有效，則更新它
                                            # 這樣可以確保不論是主項目還是子項目帶有數值，只要其清理後的名稱是"基本每股盈餘"或"稀釋每股盈餘"
                                            # 就會被捕捉並覆蓋之前可能為 None 的值
                                            if value is not None or percent is not None:
                                                eps_data_by_period[period_key][cleaned_item_name] = [value, percent]
                                else:
                                    # 處理其他非 EPS 相關的財務項目
                                    # 排除 "繼續營業單位淨利（淨損）" 這種 EPS 下的冗餘子項
                                    if cleaned_item_name.startswith("繼續營業單位淨利（淨損）"):
                                        continue

                                    # 提取並儲存其他項目
                                    for period_info in parsed_period_data:
                                        amount_idx = period_info['amount_idx']
                                        percent_idx = period_info['percent_idx']
                                        period_key = (period_info['year_roc'], period_info['quarter'], period_info['data_type'])
                                        
                                        # 初始化該期間的數據字典
                                        if period_key not in eps_data_by_period:
                                            eps_data_by_period[period_key] = {}
                                            
                                        if cleaned_item_name not in eps_data_by_period[period_key]: # 避免重複添加項目
                                            if len(row) > percent_idx:
                                                value = None
                                                percent = None
                                                
                                                value_str = row[amount_idx].strip()
                                                if value_str:
                                                    try:
                                                        value = float(value_str.replace(',', ''))
                                                    except ValueError:
                                                        pass

                                                percent_str = row[percent_idx].strip()
                                                if percent_str:
                                                    try:
                                                        percent = float(percent_str)
                                                    except ValueError:
                                                        pass
                                                
                                                if value is not None or percent is not None:
                                                    eps_data_by_period[period_key][cleaned_item_name] = [value, percent]
                                                else:
                                                    eps_data_by_period[period_key][cleaned_item_name] = [None, None] # 即使是空值也記錄
                                            else:
                                                eps_data_by_period[period_key][cleaned_item_name] = [None, None] # 欄位不足也記錄 None

                        # 將處理好的數據保存到 S3
                        for period_info in parsed_period_data:
                            current_year = period_info['year_roc']
                            current_quarter = period_info['quarter']
                            current_data_type = period_info['data_type']
                            period_key = (current_year, current_quarter, current_data_type)

                            data_to_save = eps_data_by_period.get(period_key, {}) # 獲取該期間的完整數據

                            if data_to_save:
                                self.save_data_to_s3(stock_code, company_name, current_year, current_quarter, current_data_type, data_to_save, logger)
                                logger.info(f"成功保存 民國 {current_year} 第 {current_quarter} 季 ({current_data_type}) 數據至 S3。")
                            else:
                                logger.info(f"API 回應中未找到 民國 {current_year} 第 {current_quarter} 季 ({current_data_type}) 的有效數據，不保存。")
                        # --- 新增的 EPS 處理邏輯結束 ---
                        
                        time.sleep(1) # 每次請求後暫停 1 秒
                        break # 成功取得數據，跳出重試迴圈
                    else:
                        logger.warning(f"取得 民國 {year_to_query} 第 {quarter_to_query} 季數據失敗，進行第 {attempt + 1} 次重試...")
                        time.sleep(3) # 重試前暫停 3 秒
                else:
                    logger.error(f"**多次嘗試後仍無法取得 民國 {year_to_query} 第 {quarter_to_query} 季數據，跳過此季度。**")

    def save_data_to_s3(self, stock_code, company_name, year_roc, quarter, data_type, data, logger):
        # 根據 data_type 建立不同的 S3 Object Key
        # 例如: 1101_105Q2_income_statement_quarterly.json
        # 例如: 1101_105Q2_income_statement_accumulated.json

        # 這裡根據 data_type 來決定檔案名，確保明確性
        if data_type == "quarterly":
            s3_object_key = f"{self.S3_RAW_DATA_PREFIX}{stock_code}_{year_roc}Q{quarter}_income_statement_quarterly.json"
        elif data_type == "accumulated" or data_type == "annual_accumulated": 
            s3_object_key = f"{self.S3_RAW_DATA_PREFIX}{stock_code}_{year_roc}Q{quarter}_income_statement_accumulated.json"
        else:
            logger.error(f"未知的數據類型: {data_type}，無法生成 S3 物件鍵。")
            return
            
        json_data = {
            "stock_code": stock_code,
            "company_name": company_name,
            "year_roc": year_roc,
            "quarter": quarter,
            "data_type": data_type, # 標示數據類型 (這裡仍然會是 original data_type, 但檔名會統一)
            "data": data,
            "crawled_at": datetime.now().isoformat()
        }
        
        try:
            json_payload = json.dumps(json_data, ensure_ascii=False, indent=2)
            
            self.s3_client.put_object(
                Bucket=self.S3_BUCKET_NAME,
                Key=s3_object_key,
                Body=json_payload.encode('utf-8'),
                ContentType='application/json'
            )
            logger.info(f"數據成功上傳至 S3: {s3_object_key}")
        except Exception as e:
            logger.error(f"上傳數據至 S3 失敗: {s3_object_key} - {e}", exc_info=True)

# --- 主程式入口點：此區塊為 ECS Task 從 SQS 接收訊息並處理 ---
if __name__ == "__main__":
    crawler = IncomeStatementAPICrawler() # 實例化新的爬蟲類別
    
    # SQS 接收訊息的參數
    max_messages = 1
    # VisibilityTimeout 應根據實際任務處理時間設定，確保在處理期間訊息不會被其他消費者看到
    # 假設爬取一家公司所有季度數據最多需要 15 分鐘 (900秒)，請根據實際情況調整
    visibility_timeout_seconds = 900 
    wait_time_seconds = 20 # 長輪詢，減少空請求

    no_message_count = 0
    # 設定連續沒有訊息的次數上限。達到此上限後，任務將退出以節省成本。
    # 這裡假設如果連續 3 次 (3 * 20秒 = 1分鐘) 沒有訊息，就認為任務已完成。
    max_no_message_attempts = 3

    root_logger = logging.getLogger() # 使用根日誌記錄器來記錄 SQS 相關訊息

    while True:
        try:
            # 從 SQS 佇列拉取訊息
            root_logger.info(f"正在從 SQS 佇列 {SQS_QUEUE_URL} 接收訊息...")
            response = crawler.sqs_client.receive_message(
                QueueUrl=SQS_QUEUE_URL,
                MaxNumberOfMessages=max_messages,
                VisibilityTimeout=visibility_timeout_seconds,
                WaitTimeSeconds=wait_time_seconds
            )
            
            messages = response.get('Messages', [])
            
            if not messages:
                no_message_count += 1
                root_logger.info(f"沒有可用的 SQS 訊息，等待 {wait_time_seconds} 秒... (連續無訊息次數: {no_message_count}/{max_no_message_attempts})")
                if no_message_count >= max_no_message_attempts:
                    root_logger.info(f"連續 {max_no_message_attempts} 次沒有收到 SQS 訊息，停止任務以節省成本。") 
                    break # 跳出 while True 迴圈，程式結束                
                # time.sleep(wait_time_seconds) # 此行不需要，因為 WaitTimeSeconds 已在 receive_message 中生效
                continue

            no_message_count = 0 # 重置計數器

            for message in messages:
                receipt_handle = message['ReceiptHandle'] # 訊息的唯一識別符，用於刪除訊息
                
                try:
                    # 解析訊息內容，預期是 JSON 格式，包含 stock_code, company_name, start_year_roc, start_quarter_roc, end_year_roc, end_quarter_for_end_year
                    message_body = json.loads(message['Body'])
                    stock_code = message_body.get('stock_code')
                    company_name = message_body.get('company_name')
                    start_year_roc = message_body.get('start_year_roc')
                    start_quarter_roc = message_body.get('start_quarter_roc')
                    end_year_roc = message_body.get('end_year_roc')
                    end_quarter_for_end_year = message_body.get('end_quarter_for_end_year')

                    # 檢查所有必要的參數是否存在 (確保 SQS 訊息包含這些參數)
                    if all([stock_code, company_name, start_year_roc, start_quarter_roc, end_year_roc, end_quarter_for_end_year]):
                        root_logger.info(f"\n--- 從 SQS 接收任務：開始爬取 {stock_code} {company_name} (民國 {start_year_roc}Q{start_quarter_roc} - {end_year_roc}Q{end_quarter_for_end_year}) ---")
                        
                        # 執行爬蟲邏輯
                        # 傳遞從 SQS 訊息中獲取的年份和季度範圍
                        crawler.crawl_income_statement(
                            stock_code, company_name, 
                            start_year_roc, start_quarter_roc, 
                            end_year_roc, end_quarter_for_end_year
                        ) 
                        
                        # 爬蟲成功完成後，刪除 SQS 訊息
                        crawler.sqs_client.delete_message(
                            QueueUrl=SQS_QUEUE_URL,
                            ReceiptHandle=receipt_handle # 修正了參數名稱
                        )
                        root_logger.info(f"--- 完成 {stock_code} {company_name} 爬取，並已從 SQS 佇列中刪除訊息 ---")
                    else:
                        root_logger.warning(
                            f"SQS 訊息格式不正確，缺少必要參數 ({stock_code=}, {company_name=}, {start_year_roc=}, {start_quarter_roc=}, {end_year_roc=}, {end_quarter_for_end_year=}): "
                            f"{message['Body']}. 將刪除此訊息以避免重複處理。"
                        )
                        # 對於格式不正確的訊息，直接刪除，避免無限循環
                        crawler.sqs_client.delete_message(
                            QueueUrl=SQS_QUEUE_URL,
                            ReceiptHandle=receipt_handle
                        )

                except json.JSONDecodeError:
                    root_logger.error(f"SQS 訊息體不是有效的 JSON 格式: {message['Body']}. 將刪除此訊息以避免重複錯誤。", exc_info=True)
                    # 刪除無法解析的訊息，避免重複錯誤
                    crawler.sqs_client.delete_message(
                        QueueUrl=SQS_QUEUE_URL,
                        ReceiptHandle=receipt_handle
                    )
                except Exception as e:
                    root_logger.error(f"處理 SQS 訊息或執行爬蟲時發生錯誤: {e}. 訊息將在 VisibilityTimeout 後重新可見。", exc_info=True)
                    # 如果這裡發生錯誤，訊息將在 VisibilityTimeout 後重新可見，並被重新處理
                    # 如果是持續性錯誤，訊息將會進入死信佇列 (由 SQS 的 Redrive Policy 配置處理)
                    # 不在此處刪除訊息，讓 SQS 處理重試邏輯
        
        except Exception as e:
            root_logger.critical(f"與 SQS 服務互動時發生嚴重錯誤: {e}", exc_info=True)
            root_logger.info("程式將在短暫等待後重試 SQS 連接...")
            time.sleep(10) # 發生 SQS 相關錯誤時等待較長時間再重試
