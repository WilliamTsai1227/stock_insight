from fastapi import APIRouter, HTTPException, Query
from typing import Optional
from fastapi.responses import JSONResponse
from bson import ObjectId
from module.mongodb_connection_pool import mongodb_pool

router = APIRouter()

# 使用連接池獲取 AI_news_analysis collection
collection = mongodb_pool.get_collection("AI_news_analysis")

@router.get("/api/ai_news")
async def get_ai_news(
    keyword: Optional[str] = None,
    industry: Optional[str] = None,
    is_summary: Optional[bool] = None,
    start_time: Optional[int] = None,
    end_time: Optional[int] = None,
    page: int = 1
):
    limit = 15
    skip = (page - 1) * limit

    # 組查詢條件
    query = {}

    if keyword:
        query["$or"] = [
            {"summary": {"$regex": keyword, "$options": "i"}},
            {"important_news": {"$regex": keyword, "$options": "i"}},
            {"potential_stocks_and_industries": {"$regex": keyword, "$options": "i"}},
            {"source_news.title": {"$regex": keyword, "$options": "i"}}
        ]
    if industry:
        query["industry_list"] = {
            "$elemMatch": {"$regex": industry, "$options": "i"}
        }

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

    return JSONResponse(content={"nextPage":page + 1 if len(results) == limit else None,"page": page, "data": results}) 