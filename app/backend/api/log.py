from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import JSONResponse
from module.mongodb_connection_pool import mongodb_pool
from datetime import datetime, timedelta


router = APIRouter()

# 使用連接池獲取 log collection
collection = mongodb_pool.get_collection("log")

@router.get("/api/log/ai_headline_news_error")
def get_ai_headline_news_error(
    date_ts: int = Query(..., description="指定某天的 timestamp（UNIX 秒）"),
    skip: int = Query(0, ge=0, description="跳過前幾筆資料"),
    limit: int = Query(20, ge=1, le=100, description="一次回傳筆數（最多100）"),
    sort_order: int = Query(-1, description="排序方式：1 為舊到新，-1 為新到舊")
):
    try:
        # 使用已定義的 collection
        cursor = collection.find(
            {
                "timestamp": {
                    "$gte": date_ts,
                    "$lt": date_ts + 86400  # 加一天（秒）
                }
            }
        ).skip(skip).limit(limit).sort("timestamp", sort_order)

        results = list(cursor)

        # ObjectId 轉為字串
        for r in results:
            r["_id"] = str(r["_id"])

        return results

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"伺服器錯誤：{str(e)}")
