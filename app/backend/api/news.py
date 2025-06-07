from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from bson import ObjectId
from typing import Optional
from module.mongodb_connection_pool import mongodb_pool

router = APIRouter()

# 使用連接池獲取 news collection
collection = mongodb_pool.get_collection("news")

@router.get("/api/news/{object_id}")
async def get_single_news(object_id: str):
    try:
        obj_id = ObjectId(object_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid ObjectId")

    result = collection.find_one({"_id": obj_id})
    
    if not result:
        raise HTTPException(status_code=404, detail="News not found")

    result["_id"] = str(result["_id"])
    return JSONResponse(content={"data": result})


@router.get("/api/news")
async def get_news(
    keyword: Optional[str] = None,
    start_time: Optional[int] = None,
    end_time: Optional[int] = None,
    page: int = 1
):
    limit = 20
    skip = (page - 1) * limit

    # 組查詢條件
    query = {}

    if keyword:
        query["$or"] = [
            {"title": {"$regex": keyword, "$options": "i"}},
            {"summary": {"$regex": keyword, "$options": "i"}},
            {"content": {"$regex": keyword, "$options": "i"}}
        ]

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