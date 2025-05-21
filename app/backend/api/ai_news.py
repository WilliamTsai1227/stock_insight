from fastapi import APIRouter, HTTPException, Query
from typing import Optional
from fastapi.responses import JSONResponse
from pymongo import MongoClient
from dotenv import load_dotenv
import os
load_dotenv()

# MongoDB 連線
db_user = os.getenv('mongodb_user')
db_password = os.getenv('mongodb_password')
uri = f"mongodb+srv://{db_user}:{db_password}@stock-main.kbyokcd.mongodb.net/?retryWrites=true&w=majority&appName=stock-main"
client = MongoClient(uri)
db = client["stock_insight"]
collection = db["AI_news_analysis"]




router = APIRouter

@router.get("/api/ai_news")
async def get_ai_news(
    keyword: Optional[str] = None,
    industry: Optional[str] = None,
    is_summary: Optional[bool] = None,
    start_time: Optional[str] = None,
    end_time: Optional[str] = None,
    page: int = 1
):
    limit = 10
    skip = (page - 1) * limit

    # 組成查詢條件
    query = {}

    if keyword:
        query["content"] = {"$regex": keyword, "$options": "i"}  # 模糊搜尋
    if industry:
        query["industry"] = industry
    if is_summary is not None:
        query["is_summary"] = is_summary
    if start_time and end_time:
        query["created_at"] = {
            "$gte": start_time,
            "$lte": end_time
        }

    # 查詢資料
    results = list(collection.find(query).skip(skip).limit(limit))

    # 將 MongoDB ObjectId 轉成字串
    for r in results:
        r["_id"] = str(r["_id"])

    return JSONResponse(content={"page": page, "data": results})