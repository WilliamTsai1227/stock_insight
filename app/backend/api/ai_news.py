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




router = APIRouter()


@router.get("/api/ai_news")
async def get_ai_news(
    keyword: Optional[str] = None,
    industry: Optional[str] = None,
    is_summary: Optional[bool] = None,
    start_time: Optional[int] = None,
    end_time: Optional[int] = None,
    page: int = 1
):
    limit = 10
    skip = (page - 1) * limit

    # 組查詢條件
    query = {}

    if keyword:
        query["summary"] = {"$regex": keyword, "$options": "i"}  # 模糊搜尋 summary 欄位

    if industry:
        query["industry_list"] = {"$in": [industry]}

    if is_summary is not None:
        query["is_summary"] = is_summary

    if start_time is not None and end_time is not None:
        query["publishAt"] = {
            "$gte": start_time,
            "$lte": end_time
        }

    # 查詢 + 排序 + 分頁
    results = list(
        collection.find(query)
        .sort("publishAt", -1)
        .skip(skip)
        .limit(limit)
    )

    # 處理 ObjectId
    for r in results:
        r["_id"] = str(r["_id"])

    return JSONResponse(content={"page": page, "data": results})