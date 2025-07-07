from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import JSONResponse
from typing import Optional
from module.postgresql_connection_pool import postgresql_pool
from module.stock import Stock

router = APIRouter()




@router.get("/api/stock_info")
async def get_stock_info(
    stock_symbol: str = Query(..., description="股票代碼", min_length=1),
    country: str = Query(..., description="國家代碼 (tw, us, hk, jp, cn)", min_length=1)
):
    # 驗證股票代碼
    if not Stock.validate_stock_symbol(stock_symbol):
        raise HTTPException(
            status_code=400,
            detail="股票代碼格式不正確，只能包含英文字母和數字"
        )

    # 驗證國家代碼
    if not Stock.validate_country_code(country):
        raise HTTPException(
            status_code=400,
            detail="國家代碼格式不正確，只能包含英文字母"
        )

    # 獲取國家名稱
    try:
        country_name = Stock.get_country_name(country)
    except HTTPException as e:
        raise e

    try:
        async with postgresql_pool.get_connection() as conn:
            query = Stock.get_stock_info_query()
            result_record = await conn.fetchrow(query, stock_symbol, country_name)
            if not result_record:
                raise HTTPException(
                    status_code=404,
                    detail=f"找不到股票代碼 {stock_symbol} 在 {country_name} 的資料"
                )
            stock_info = Stock.format_stock_data(result_record)
            return JSONResponse(content={"data": stock_info})
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"查詢資料時發生錯誤：{str(e)}"
        ) 