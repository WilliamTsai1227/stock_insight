from fastapi import APIRouter,HTTPException,Query
from fastapi.responses import JSONResponse
from module.postgresql_connection_pool import postgresql_pool
from module.financial_report import Financial_report


router = APIRouter()


@router.get("/api/financial_report")
async def get_financial_report(
    stock_symbol: str = Query(..., description="股票代碼", min_length=3),
    country: str = Query(..., description="國家代碼 (tw, us, hk, jp, cn)", min_length=2),
    report_type: str = Query(...,  description="財報種類 (balance_sheets,income_statements,cash_flow)", ),
    report_period: str = Query(..., description="財報期間 (quarterly, accumulated)"),    
):
    # 驗證股票代碼
    if not Financial_report.validate_stock_symbol(stock_symbol):
        raise HTTPException(
            status_code=400,
            detail="股票代碼格式不正確，只能包含英文字母和數字"
        )

    # 驗證國家代碼
    if not Financial_report.validate_country_code(country):
        raise HTTPException(
            status_code=400,
            detail="國家代碼格式不正確，只能包含英文字母"
        )
    
    table_name = ""
    if report_type == "balance_sheets":
        table_name = "Balance_Sheets"
    elif report_type == "income_statements":
        table_name = "Income_Statements"
    elif report_type == "cash_flow":
        table_name = "Cash_Flow_Statements"
    # 驗證財報種類
    if not Financial_report.validate_report_type(report_type):
        raise HTTPException(
            status_code=400,
            detail=f"不支援的財報種類：{report_type}。或潛在的 SQL 注入嘗試。"
        )
    # 驗證財報期間
    
    if not Financial_report.validate_report_period(report_period):
        raise HTTPException(
            status_code=400,
            detail=f"不支援的財報期間：{report_period}"
        )

    # 轉換國家代碼為國家名稱
    try:
        country_name = Financial_report.get_country_name(country)
    except HTTPException as e:
        raise e
    

    try:
        # 使用 asyncpg 的非同步連線池獲取連線
        async with postgresql_pool.get_connection() as conn:
            # 只有一種查詢模式：查詢該財報類別所有年份的所有資料
            query = f"""
                SELECT fr.*, c.stock_symbol, ct.country_name
                FROM {table_name} AS fr
                INNER JOIN Companies AS c ON fr.company_id = c.company_id
                INNER JOIN Countrys AS ct ON c.country_id = ct.country_id
                WHERE c.stock_symbol = $1 AND ct.country_name = $2 AND fr.report_type = $3
                ORDER BY fr.year DESC, fr.quarter DESC;
            """
            params = [stock_symbol, country_name, report_period]
            results = await conn.fetch(query, *params)
            
            # 將 asyncpg.Record 物件轉換為字典列表
            formatted_results = [dict(record) for record in results]
            formatted_results = Financial_report.decimal_to_float(formatted_results)

            if not formatted_results:
                return JSONResponse(status_code=404, content={"message": "未找到相關財報資料"})

            return JSONResponse(status_code=200,content={"data":formatted_results,"status":"ok"})

    except HTTPException as e:
        raise e
    except Exception as e:
        # 捕捉其他未預期的資料庫錯誤
        print(f"資料庫查詢錯誤: {e}")
        raise HTTPException(status_code=500, detail="內部伺服器錯誤")