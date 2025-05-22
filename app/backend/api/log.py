from fastapi import APIRouter, HTTPException, Query
from module.connection_pool import get_log_data_db
from datetime import datetime, timedelta


router = APIRouter()

@router.get("/api/log/ai_headline_news_error")
def get_ai_headline_news_error(
    date_ts: int = Query(..., description="指定某天的 timestamp（UNIX 秒）"),
    skip: int = Query(0, ge=0, description="跳過前幾筆資料"),
    limit: int = Query(20, ge=1, le=100, description="一次回傳筆數（最多100）"),
    sort_order: int = Query(-1, description="排序方式：1 為舊到新，-1 為新到舊")
):
    try:
        db = get_log_data_db()
        collection = db["AI_headline_news_error"]

        # 把 timestamp 轉為當天的起始與結束（秒）
        start_ts = date_ts
        end_ts = date_ts + 86400  # 加一天（秒）

        cursor = collection.find(
            {
                "timestamp": {
                    "$gte": start_ts,
                    "$lt": end_ts
                }
            }
        ).skip(skip).limit(limit).sort("timestamp", sort_order)  # 預設為-1 為最新到舊

        results = list(cursor)

        # ObjectId 轉為字串
        for r in results:
            r["_id"] = str(r["_id"])

        return results

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"伺服器錯誤：{str(e)}")
