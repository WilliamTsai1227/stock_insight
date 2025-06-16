import boto3
import json
import io
import re
from datetime import datetime
from lambda_layer.db_data_utils.insert_data import insert_data_mongodb
import time
from lambda_layer.log_utils.logger import log_error,log_success
import os

if os.getenv("AWS_EXECUTION_ENV") is None:
    from dotenv import load_dotenv
    load_dotenv()
    s3_access_key_id = os.getenv("aws_s3_access_key_id")
    s3_secret_access_key = os.getenv("aws_s3_secret_access_key")

#This lambda function is used to get headline news data from s3, then use AI to analyze the news , and finally return the results and intsert them into database.



def get_s3_client():
    return boto3.client(
        "s3",
        region_name="us-west-2"
    )

def get_bedrock_client():
    return boto3.client(
        'bedrock-runtime',
        region_name="us-west-2"
    )

def get_today_max_version(bucket_name, prefix_date=None):
    """取得今天該 prefix 下最大的版本號"""
    s3 = get_s3_client()
    
    if prefix_date is None:
        prefix_date = datetime.now().strftime("headline_daily/headline_news_%Y%m%d")  # e.g., headline_daily/headline_news_20250501

    response = s3.list_objects_v2(Bucket=bucket_name, Prefix=prefix_date)
    max_version = 0

    if 'Contents' in response:
        for obj in response['Contents']:
            key = obj['Key']
            match = re.search(rf"{prefix_date}_v(\d+)\.json", key)
            if match:
                version = int(match.group(1))
                if version > max_version:
                    max_version = version
    return max_version  # 0 表示目前沒有任何檔案






def get_latest_read_key(bucket_name):
    """取得今天最新版本的檔案 key"""
    prefix_date = datetime.now().strftime("headline_daily/headline_news_%Y%m%d")
    max_version = get_today_max_version(bucket_name, prefix_date)
    if max_version == 0:
        log_collection = "AI_headline_news_error"
        log_type = "s3 source_file_error"
        error_message = "There are no headlines json files available for analysis in S3 today."
        source = "lambda_function/AI_headline_news_analysis.py / get_latest_read_key()"
        log_error(
            log_collection = log_collection,
            log_type=log_type,
            error_message=error_message,
            source=source
            )
        raise FileNotFoundError(f"No file found for {prefix_date}")
    return f"{prefix_date}_v{max_version}.json"




def get_s3_file_like_object(bucket_name, key):
    """從 S3 取得像本地檔案的 file-like 物件"""
    s3 = get_s3_client()
    response = s3.get_object(Bucket=bucket_name, Key=key)
    content = response['Body'].read().decode('utf-8')
    return io.StringIO(content)  # 回傳像 open(...) 回傳的檔案物件



def load_local_news_from_s3(bucket_name, key):
    """從 S3 載入 JSON 檔案並組合成文字"""
    news_entries = []
    f = get_s3_file_like_object(bucket_name, key)  # 跟 open(...) 類似
    for line in f:
        try:
            news_json = json.loads(line.strip())
        except json.JSONDecodeError as e:
            log_collection = "AI_headline_news_error"
            log_type = "bedrock_client.invoke_model error"
            error_message = f"load_local_news_from_s3()  json.loads(line.strip()) error {e}"
            source = "lambda_function/AI_headline_news_analysisy.py/load_local_news_from_s3()"
            log_error(log_collection=log_collection,log_type=log_type,error_message=error_message,source=source)
            continue
        try:
            title = news_json.get("title", "")
            content = news_json.get("content", "")
            id = news_json.get("_id", "")
            news_entries.append(f"標題：{title}\nID:{id}\n內文：{content}")
        except Exception as e:
            log_collection = "AI_headline_news_error"
            log_type = "bedrock_client.invoke_model error"
            error_message = f"load_local_news_from_s3()  news_entries.append() error {e}"
            source = "lambda_function/AI_headline_news_analysisy.py/load_local_news_from_s3()"
            log_error(log_collection=log_collection,log_type=log_type,error_message=error_message,source=source)
            continue
    return "\n".join(news_entries) #會回傳一個多段中間只有換行的字串，每一段都會是f"標題：{title}\nID:{id}\n內文：{content}"




def analyze_news(news_text: str) -> str:
    source = "AI_headline_news_analysis.py / analyze_news()"
    
    system_prompt = """
    你是一位專業新聞分析師，請閱讀以下新聞並完成七項任務
    請**僅以 JSON 物件格式回傳下方欄位內容**，不得輸出自然語言說明、換行或其他額外內容，JSON 必須為單一物件：
    範例：
    {
    "summary": "請填入第 1 項：當日新聞的精簡摘要。",
    "important_news": "請填入第 2 項：真正重要的重點新聞（根據潛在意義與影響）。",
    "sentiment": "請填入第 3 項：整體情緒分析（正面／負面／中性）及理由。",
    "potential_stocks_and_industries": "請填入第 4 項的完整文字描述（包含推薦個股與產業的原因說明）。",
    "stock_list": [
        ["tw", "2330", "台積電"],
        ["us", "AAPL", "APPLE"]
    ],
    "industry_list": [
        "半導體",
        "光電"
    ],
    "source_news":[
        {"title":"美港口對陸船收費 長榮彈性調配不受影響","_id":"680b6917c3c5d94c43190b98"},
        {"title":"關稅衝擊〉全面防堵「洗產地」！5/7起 MIT貨品出口至美國 須附原產地聲明書","_id":"680b6917c3c5d94c43190b99"},
        {"title":"對美中貿易協議樂觀期待 美債殖利率持穩","_id":"680b6917c3c5d94c43190b9a"},
    ]
    }

    ---

    欄位說明：
    1. summary : 提供當日新聞的**精簡摘要** Datatype:String。
    2. important_news : 挑出真正**重要的重點新聞**，請根據新聞潛在意義與可能影響，不僅是出現次數。(如果要以條列方式撰寫，請以數字條列並在每個條列式結尾使用 **字串形式的 `\\n`**（即兩個反斜線加 n 字母），而不是實際的換行符號。避免變成一整段文字）。Datatype:String。
    3. sentiment : 給出今日新聞的**情緒分析**（正面／負面／中性），並說明你的判斷依據。Datatype:String。
    4. potential_stocks_and_industries : 根據新聞內容，推論出**值得高度關注的潛力個股與產業**，並解釋推薦原因（例如：政策利多、產業趨勢、事件驅動等）。(如果要以條列方式撰寫，請以數字條列並在每個條列式結尾使用 **字串形式的 `\\n`**（即兩個反斜線加 n 字母），而不是實際的換行符號。避免變成一整段文字）。Datatype:String。
    5. stock_list : 將第 4 點提到的個股，**以 list 格式放入 stock_list 欄位**，格式如下：
    - 台股用 ["tw", "股票代碼", "公司名稱"]
    - 美股用 ["us", "股票代碼", "公司名稱"]
    - 港股用 ["hk", "股票代碼", "公司名稱"]
    - 日股用 ["jp", "股票代碼", "公司名稱"]
    - 中國股票用 ["cn", "股票代碼", "公司名稱"]
    6. industry_list : 將第 4 點提到的產業，**以 list 格式放入 industry_list 欄位**，範例如下：
    - ["半導體", "AI", "鋼鐵"]
    - 注意：**不得加上「產業」兩字**
    7. source_news : 請將本次分析所根據的每一篇新聞，回傳其「標題」與「ID」，格式如下：
    - [
        {"title": "新聞標題A", "_id": "680b6917c3c5d94c43190b98"},
        {"title": "新聞標題B", "_id": "680b6917c3c5d94c43190b99"}
    ]

    特別注意：
    - 請優先挑出新聞中「雖然只出現一次但具有潛在重大意涵」的議題。
    - 在第 4 項中，若可提及具體公司名稱（如台積電、鴻海等）與產業（如半導體、AI、生技、綠能），並說明其與新聞的關聯，效果更佳。
    - 所有欄位都必須填入對應的內容，並以 JSON 結構格式回傳（不要有自然語言或段落），請務必嚴格依照上述格式與內容回傳單一 JSON。
    """

    # 假設每次最多處理 5 篇新聞
    max_articles_per_batch = 5
    
    news_list = re.split(r'(?=標題：)', news_text) #使用正則將每篇新聞以"標題："做區分寫入list，確保一個item就是一則新聞
    news_list = [n.strip() for n in news_list if n.strip()] # 移除空字串或只包含空白的元素

    batches = []
    for i in range(0, len(news_list), max_articles_per_batch):
        batch = news_list[i:i + max_articles_per_batch]
        batches.append(batch)
    
    total_summary = []  # 用來儲存每一批的摘要

    # 初始化 Bedrock Runtime 客戶端
    bedrock_client = get_bedrock_client()

    # Claude 3 Haiku 模型 ID
    MODEL_ID = 'anthropic.claude-3-haiku-20240307-v1:0'
    count = 0
    for item in batches:
        # 合併每一批的新聞文本
        batch_text = "\n\n".join(item)
        full_prompt = f"{system_prompt.strip()}\n\n以下是今天的新聞：\n{batch_text.strip()}"
        # 建立符合 Claude Messages API 的 body 結構
        body = {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 5000,
            "temperature": 0.7,
            "top_p": 0.95,
            "top_k": 250,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": full_prompt
                        }
                    ]
                }
            ]
        }

        try:
            # 呼叫模型
            response = bedrock_client.invoke_model(
                modelId=MODEL_ID,
                body=json.dumps(body),
                contentType='application/json',
                accept='application/json'
            )
            response_body = response['body'].read().decode('utf-8')
            result = json.loads(response_body)
        except Exception as e:
            log_collection = "AI_headline_news_error"
            log_type = "bedrock_client.invoke_model error"
            error_message = f"{e}"
            source = "lambda_function/AI_headline_news_analysisy.py/analyze_news()"
            log_error(log_collection=log_collection,log_type=log_type,error_message=error_message,source=source)
            continue
        
        # 取得 Claude 回應的內容
        if isinstance(result.get("content"), list) and len(result["content"]) > 0 and "text" in result["content"][0]:
            # 嘗試把文字內容當作 JSON 解開
            try:
                count += 1
                text_content= result["content"][0]["text"]
                parsed_result = json.loads(text_content)
                summary = parsed_result.get("summary", False)
                important_news = parsed_result.get("important_news", False)
                sentiment = parsed_result.get("sentiment", False)
                potential_stocks_and_industries = parsed_result.get("potential_stocks_and_industries", False)
                stock_list = parsed_result.get("stock_list", False)
                industry_list = parsed_result.get("industry_list", False)
                source_news = parsed_result.get("source_news", False)
                publishAt = int(time.time())
                # 儲存每次批次結果到資料庫
                ai_summary = {
                    "analysis_batch":count,
                    "is_summary":False,
                    "category": "headline",
                    "publishAt":publishAt,
                    "summary":summary,
                    "important_news":important_news,
                    "sentiment":sentiment,
                    "potential_stocks_and_industries":potential_stocks_and_industries,
                    "stock_list":stock_list,
                    "industry_list":industry_list,
                    "source_news":source_news
                    }
                # Store each AI analysis summary in the database
                
                insert_data_mongodb(
                    ai_summary, 
                    insert_db="stock_insight", 
                    insert_collection="AI_news_analysis", 
                    log_success_collection="AI_headline_news_success",
                    log_error_collection="AI_headline_news_error",
                    source=source
                    )
            except json.JSONDecodeError as e:
                log_error("AI_headline_news_error", "JSON decode error", str(e), source="lambda_function/AI_headline_news_analysisy.py/analyze_news()")
                continue
        else:
            log_error("AI_headline_news_error", "JSON decode error", "Claude 沒有回傳內容", source="lambda_function/AI_headline_news_analysisy.py/analyze_news()")
        try:
            if "_id" in ai_summary:
                del ai_summary["_id"] #fix the auto add "_id" after insert_data_mongodb()                 
            # Add a summary of each batch to the summary
            total_summary.append(ai_summary)
            time.sleep(2)
        except Exception as e:
            log_collection = "AI_headline_news_error"
            log_type = "total_summary.append(ai_summary) error"
            error_message = "total_summary.append(ai_summary) error"
            source = "lambda_function/AI_headline_news_analysisy.py/analyze_news()"
            log_error(log_collection=log_collection,log_type=log_type,error_message=error_message,source=source)

    final_system_prompt = """
        你將會看到多批次新聞摘要的整理結果，請基於這些內容，再次做出更高層級的整理與歸納。
    
        請閱讀新聞並完成七項任務，並**以 JSON 格式回傳以下欄位的結果**：

        {
        "summary": "請填入第 1 項：當日新聞的精簡摘要。",
        "important_news": "請填入第 2 項：真正重要的重點新聞（根據潛在意義與影響）。",
        "sentiment": "請填入第 3 項：整體情緒分析（正面／負面／中性）及理由。",
        "potential_stocks_and_industries": "請填入第 4 項的完整文字描述（包含推薦個股與產業的原因說明）。",
        "stock_list": [
            ["tw", "2330", "台積電"],
            ["us", "AAPL", "APPLE"]
        ],
        "industry_list": [
            "半導體",
            "光電"
        ],
        "source_news":[
            {"title":"美港口對陸船收費 長榮彈性調配不受影響","_id":"680b6917c3c5d94c43190b98"},
            {"title":"關稅衝擊〉全面防堵「洗產地」！5/7起 MIT貨品出口至美國 須附原產地聲明書","_id":"680b6917c3c5d94c43190b99"},
            {"title":"對美中貿易協議樂觀期待 美債殖利率持穩","_id":"680b6917c3c5d94c43190b9a"},
        ]
        }

        ---

        說明如下：
        1. 提供當日新聞的**精簡摘要**（summary）Datatype:String。
        2. 挑出真正**重要的重點新聞**（important_news），請根據新聞潛在意義與可能影響，不僅是出現次數。(如果要以條列方式撰寫，請以數字條列並在每個條列式結尾使用 **字串形式的 `\\n`**（即兩個反斜線加 n 字母），而不是實際的換行符號。避免變成一整段文字）。Datatype:String。
        3. 給出今日新聞的**情緒分析**（sentiment）:（正面／負面／中性），並說明你的判斷依據。Datatype:String。
        4. 根據新聞內容，推論出**值得高度關注的潛力個股與產業**（potential_stocks_and_industries），並解釋推薦原因（例如：政策利多、產業趨勢、事件驅動等）。(如果要以條列方式撰寫，請以數字條列並在每個條列式結尾使用 **字串形式的 `\\n`**（即兩個反斜線加 n 字母），而不是實際的換行符號。避免變成一整段文字）。Datatype:String。
        5. 將第 4 點提到的個股，**以 list 格式放入 stock_list 欄位**，格式如下：
        - 台股用 ["tw", "股票代碼", "公司名稱"]
        - 美股用 ["us", "股票代碼", "公司名稱"]
        - 港股用 ["hk", "股票代碼", "公司名稱"]
        - 日股用 ["jp", "股票代碼", "公司名稱"]
        - 中國股票用 ["cn", "股票代碼", "公司名稱"]
        6. 將第 4 點提到的產業，**以 list 格式放入 industry_list 欄位**，範例如下：
        - ["半導體", "AI", "鋼鐵"]
        - 注意：**不要加上「產業」兩字**
        7. source_news : 請將本次分析所根據的每一篇新聞，回傳其「標題」與「ID」，格式如下：
        - [
            {"title": "新聞標題A", "_id": "680b6917c3c5d94c43190b98"},
            {"title": "新聞標題B", "_id": "680b6917c3c5d94c43190b99"}
        ]

        特別注意：
        - 請優先挑出新聞中「雖然只出現一次但具有潛在重大意涵」的議題。
        - 在第 4 項中，若可提及具體公司名稱（如台積電、鴻海等）與產業（如半導體、AI、生技、綠能），並說明其與新聞的關聯，效果更佳。
        - 所有欄位都必須填入對應的內容，並以 JSON 結構格式回傳（不要有自然語言或段落），請務必嚴格依照上述格式與內容回傳單一 JSON。
    """
    
    total_summary_json = json.dumps(total_summary, ensure_ascii=False, indent=2)
    
    final_prompt = f"{final_system_prompt}\n\n以下是多批次的新聞摘要資料（JSON 格式）如下：\n{total_summary_json}"
    body = {
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": 5500,
        "temperature": 0.7,
        "top_p": 0.95,
        "top_k": 250,
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": final_prompt
                    }
                ]
            }
        ]
    }

    try:
        # 呼叫模型
        response = bedrock_client.invoke_model(
            modelId=MODEL_ID,
            body=json.dumps(body),
            contentType='application/json',
            accept='application/json'
        )
        result = json.loads(response['body'].read())
    except Exception as e:
        error_message = f"{e}"
        log_error("AI_headline_news_error","bedrock_client.invoke_model error", error_message,source="lambda_function/AI_headline_news_analysisy.py/analyze_news()")
        result = {}

    if isinstance(result.get("content"), list) and len(result["content"]) > 0 and "text" in result["content"][0]:
        
        # 嘗試把文字內容當作 JSON 解開
        try:
            final_ai_summary = result["content"][0]["text"]
            parsed_result = json.loads(final_ai_summary)
            summary = parsed_result.get("summary", False)
            important_news = parsed_result.get("important_news", False)
            sentiment = parsed_result.get("sentiment", False)
            potential_stocks_and_industries = parsed_result.get("potential_stocks_and_industries", False)
            stock_list = parsed_result.get("stock_list", False)
            industry_list = parsed_result.get("industry_list", False)
            source_news = parsed_result.get("source_news", False)
            publishAt = int(time.time())
            # 儲存每次批次結果到資料庫
            db_final_ai_summary = {
                "analysis_batch": -1,
                "is_summary":True,
                "category": "headline",
                "publishAt":publishAt,
                "summary":summary,
                "important_news":important_news,
                "sentiment":sentiment,
                "potential_stocks_and_industries":potential_stocks_and_industries,
                "stock_list":stock_list,
                "industry_list":industry_list,
                "source_news":source_news
                }
            # Store each AI analysis summary in the database
            insert_data_mongodb(
                db_final_ai_summary, 
                insert_db="stock_insight", 
                insert_collection="AI_news_analysis",
                log_success_collection="AI_headline_news_success",
                log_error_collection="AI_headline_news_error", 
                source=source
                )
            return {
                "ok":True,
                "message":"AI分析結果成功存入資料庫"
            }
        except json.JSONDecodeError as e:
            log_error("AI_headline_news_error", "JSON decode error", str(e), source="lambda_function/AI_headline_news_analysisy.py/analyze_news()")
            return {
                "ok":False,
                "message":"Claude 回傳內容不是合法 JSON"
            }
            
    else:
        return {
            "ok":False,
            "message":"Claude 沒有回傳摘要"
        }
        
      

def lambda_handler(event, context):
    try:
        key = get_latest_read_key("stock-insight-news-datalake")
        news_text = load_local_news_from_s3(bucket_name="stock-insight-news-datalake", key=key)
        
        result = analyze_news(news_text)
        if isinstance(result,dict) and result.get("ok",False) != False:
            
            successful_message = "AI headline news analysis success"
            lambda_result = {
                "statusCode": 200,
                "body": successful_message
            }
            log_success("AI_headline_news_success","daily",successful_message,source="lambda_function/AI_headline_news_analysisy.py/lambda_handler()")
            return lambda_result
    except Exception as e:
        error_message = f"AI headline news analysis error:{e}"
        log_error("AI_headline_news_error","daily",error_message,source="lambda_function/AI_headline_news_analysisy.py/lambda_handler()")
        return {
            "statusCode": 500,
            "body": error_message
        }


if __name__ == '__main__':
    lambda_handler({}, {})
    




