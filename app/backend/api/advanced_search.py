from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import JSONResponse
from module.postgresql_connection_pool import postgresql_pool
from module.financial_report import Financial_report
from typing import Optional, List
import re
from decimal import Decimal

router = APIRouter()

class AdvancedSearch:
    # 支援的排行榜類型
    SUPPORTED_RANKINGS = {
        # 現金流量表
        'operating_cash_flow': {
            'table': 'Cash_Flow_Statements',
            'field': 'operating_cash_flow',
            'description': '營業活動之現金流量排行榜'
        },
        'free_cash_flow': {
            'table': 'Cash_Flow_Statements',
            'field': 'free_cash_flow',
            'description': '自由現金流量排行榜'
        },
        'net_change_in_cash': {
            'table': 'Cash_Flow_Statements',
            'field': 'net_change_in_cash',
            'description': '現金及約當現金淨變動排行榜'
        },
        
        # 損益表
        'revenue': {
            'table': 'Income_Statements',
            'field': 'revenue',
            'description': '營收排行榜'
        },
        'gross_profit': {
            'table': 'Income_Statements',
            'field': 'gross_profit',
            'description': '營業毛利排行榜'
        },
        'operating_expenses': {
            'table': 'Income_Statements',
            'field': 'operating_expenses',
            'description': '營業費用排行榜'
        },
        'operating_income': {
            'table': 'Income_Statements',
            'field': 'operating_income',
            'description': '營業利益排行榜'
        },
        'net_income': {
            'table': 'Income_Statements',
            'field': 'net_income',
            'description': '稅後淨利排行榜'
        },
        'gross_profit_pct': {
            'table': 'Income_Statements',
            'field': 'gross_profit_pct',
            'description': '營業毛利佔營收百分比排行榜'
        },
        'sales_expenses_pct': {
            'table': 'Income_Statements',
            'field': 'sales_expenses_pct',
            'description': '銷售費用佔營收百分比排行榜'
        },
        'administrative_expenses_pct': {
            'table': 'Income_Statements',
            'field': 'administrative_expenses_pct',
            'description': '管理費用佔營收百分比排行榜'
        },
        'research_and_development_expenses_pct': {
            'table': 'Income_Statements',
            'field': 'research_and_development_expenses_pct',
            'description': '研發費用佔營收百分比排行榜'
        },
        'operating_expenses_pct': {
            'table': 'Income_Statements',
            'field': 'operating_expenses_pct',
            'description': '營業費用佔營收百分比排行榜'
        },
        'operating_income_pct': {
            'table': 'Income_Statements',
            'field': 'operating_income_pct',
            'description': '營業利益佔營收百分比排行榜'
        },
        'net_income_pct': {
            'table': 'Income_Statements',
            'field': 'net_income_pct',
            'description': '稅後淨利佔營收百分比排行榜'
        },
        'cost_of_revenue_pct': {
            'table': 'Income_Statements',
            'field': 'cost_of_revenue_pct',
            'description': '營業成本佔營收百分比排行榜'
        },
        
        # 資產負債表
        'cash_and_equivalents': {
            'table': 'Balance_Sheets',
            'field': 'cash_and_equivalents',
            'description': '現金及約當現金排行榜'
        },
        'short_term_investments': {
            'table': 'Balance_Sheets',
            'field': 'short_term_investments',
            'description': '短期投資排行榜'
        },
        'accounts_receivable_and_notes': {
            'table': 'Balance_Sheets',
            'field': 'accounts_receivable_and_notes',
            'description': '應收帳款及票據排行榜'
        },
        'inventory': {
            'table': 'Balance_Sheets',
            'field': 'inventory',
            'description': '存貨排行榜'
        },
        'current_assets': {
            'table': 'Balance_Sheets',
            'field': 'current_assets',
            'description': '流動資產排行榜'
        },
        'fixed_assets_total': {
            'table': 'Balance_Sheets',
            'field': 'fixed_assets_total',
            'description': '固定資產排行榜'
        },
        'total_assets': {
            'table': 'Balance_Sheets',
            'field': 'total_assets',
            'description': '總資產排行榜'
        },
        'cash_and_equivalents_pct': {
            'table': 'Balance_Sheets',
            'field': 'cash_and_equivalents_pct',
            'description': '現金及約當現金佔總資產百分比排行榜'
        },
        'short_term_investments_pct': {
            'table': 'Balance_Sheets',
            'field': 'short_term_investments_pct',
            'description': '短期投資佔總資產百分比排行榜'
        },
        'accounts_receivable_and_notes_pct': {
            'table': 'Balance_Sheets',
            'field': 'accounts_receivable_and_notes_pct',
            'description': '應收帳款及票據佔總資產百分比排行榜'
        },
        'inventory_pct': {
            'table': 'Balance_Sheets',
            'field': 'inventory_pct',
            'description': '存貨佔總資產百分比排行榜'
        },
        'current_assets_pct': {
            'table': 'Balance_Sheets',
            'field': 'current_assets_pct',
            'description': '流動資產佔總資產百分比排行榜'
        },
        'fixed_assets_total_pct': {
            'table': 'Balance_Sheets',
            'field': 'fixed_assets_total_pct',
            'description': '固定資產佔總資產百分比排行榜'
        },
        'other_non_current_assets_pct': {
            'table': 'Balance_Sheets',
            'field': 'other_non_current_assets_pct',
            'description': '其餘資產佔總資產百分比排行榜'
        }
    }

    @staticmethod
    def validate_ranking_type(ranking_type: str) -> bool:
        """驗證排行榜類型"""
        return ranking_type in AdvancedSearch.SUPPORTED_RANKINGS

    @staticmethod
    def validate_year(year: int) -> bool:
        """驗證年份"""
        return 1900 <= year <= 2025

    @staticmethod
    def validate_quarter(quarter: Optional[int]) -> bool:
        """驗證季度"""
        if quarter is None:
            return True
        return quarter in [1, 2, 3, 4]

    @staticmethod
    def validate_report_period(report_period: str) -> bool:
        """驗證財報期間"""
        return report_period in ['quarterly', 'annual']
    
    @staticmethod
    def convert_report_period(report_period: str) -> str:
        """將前端傳送的財報期間轉換為資料庫格式"""
        if report_period == 'annual':
            return 'accumulated'
        return report_period
    
    @staticmethod
    def validate_report_type_combination(table_name: str, report_period: str) -> bool:
        """驗證財報類型與期間的組合是否有效"""
        if table_name == 'Cash_Flow_Statements':
            # 現金流量表只支援 accumulated
            return report_period == 'accumulated'
        elif table_name == 'Balance_Sheets':
            # 資產負債表只支援 quarterly
            return report_period == 'quarterly'
        elif table_name == 'Income_Statements':
            # 損益表支援兩種
            return report_period in ['quarterly', 'accumulated']
        return False
    
    @staticmethod
    def get_default_quarter(report_period: str) -> int:
        """根據財報期間獲取預設季度"""
        if report_period == 'accumulated':
            return 4
        return None  # quarterly 需要明確指定季度

    @staticmethod
    def validate_sector_name(sector_name: str) -> bool:
        """驗證產業名稱"""
        if not sector_name:
            return False
        # 只允許中英文、數字和空格
        return bool(re.match(r'^[\u4e00-\u9fa5a-zA-Z0-9\s]+$', sector_name))

    @staticmethod
    def validate_limit(limit: int) -> bool:
        """驗證限制數量"""
        return 1 <= limit <= 1000

    @staticmethod
    def decimal_to_float(obj):
        """將 Decimal 轉換為 float"""
        if isinstance(obj, dict):
            return {k: AdvancedSearch.decimal_to_float(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [AdvancedSearch.decimal_to_float(i) for i in obj]
        elif isinstance(obj, Decimal):
            return float(obj)
        else:
            return obj
    
    @staticmethod
    def _validate_report_type_for_ranking(table_name: str, report_type: str) -> bool:
        """
        根據財報類型規則驗證是否支援該排行榜
        
        Args:
            table_name: 資料表名稱
            report_type: 財報期間類型 (quarterly, accumulated)
        
        Returns:
            bool: 是否支援該排行榜
        """
        # Cash_Flow_Statements 只支援 accumulated
        if table_name == 'Cash_Flow_Statements' and report_type != 'accumulated':
            return False
        
        # Balance_Sheets 只支援 quarterly
        if table_name == 'Balance_Sheets' and report_type != 'quarterly':
            return False
        
        # Income_Statements 支援 quarterly 和 accumulated
        if table_name == 'Income_Statements' and report_type not in ['quarterly', 'accumulated']:
            return False
        
        return True


@router.get("/api/advanced_search/ranking")
async def get_financial_ranking(
    ranking_type: str = Query(..., description="排行榜類型"),
    year: int = Query(..., description="年份"),
    report_type: str = Query(..., description="財報期間 (quarterly, annual)"),
    sector_name: Optional[str] = Query(None, description="產業名稱 (可選)"),
    quarter: Optional[int] = Query(None, description="季度 (1-4, 可選)"),
    limit: int = Query(50, description="回傳筆數限制 (1-1000)", ge=1, le=1000),
    page: int = Query(1, description="頁碼 (從1開始)", ge=1)
):
    """
    進階搜尋 API - 財務排行榜
    
    支援的排行榜類型:
    - 現金流量表: operating_cash_flow, free_cash_flow, net_change_in_cash
    - 損益表: revenue, gross_profit, operating_expenses, operating_income, net_income
    - 損益表百分比: gross_profit_pct, sales_expenses_pct, administrative_expenses_pct, 
                   research_and_development_expenses_pct, operating_expenses_pct, 
                   operating_income_pct, net_income_pct, cost_of_revenue_pct
    - 資產負債表: cash_and_equivalents, short_term_investments, accounts_receivable_and_notes,
                  inventory, current_assets, fixed_assets_total, total_assets
    - 資產負債表百分比: cash_and_equivalents_pct, short_term_investments_pct, 
                       accounts_receivable_and_notes_pct, inventory_pct, current_assets_pct,
                       fixed_assets_total_pct, other_non_current_assets_pct
    
    財報期間說明:
    - quarterly: 單季財報，需要指定季度 (1-4)
    - annual: 年度財報，自動查詢第4季累積資料
    
    分頁說明:
    - 每頁固定回傳30筆資料
    - 前端可透過 page 參數控制頁碼
    """
    
    # 驗證排行榜類型
    if not AdvancedSearch.validate_ranking_type(ranking_type):
        supported_types = list(AdvancedSearch.SUPPORTED_RANKINGS.keys())
        raise HTTPException(
            status_code=400,
            detail=f"不支援的排行榜類型：{ranking_type}。支援的類型：{', '.join(supported_types)}"
        )

    # 驗證年份
    if not AdvancedSearch.validate_year(year):
        raise HTTPException(
            status_code=400,
            detail="年份格式不正確，請輸入 1900-2025 之間的年份"
        )

    # 驗證季度
    if not AdvancedSearch.validate_quarter(quarter):
        raise HTTPException(
            status_code=400,
            detail="季度格式不正確，請輸入 1-4 之間的數字"
        )
    
    # 處理季度邏輯
    if report_type == 'quarterly':
        if quarter is None:
            raise HTTPException(
                status_code=400,
                detail="quarterly 財報期間必須指定季度 (1-4)"
            )
    elif report_type == 'annual':
        # annual 財報自動使用第4季
        if quarter is None:
            quarter = 4
        elif quarter != 4:
            raise HTTPException(
                status_code=400,
                detail="annual 財報期間只能使用第4季"
            )

    # 驗證財報期間
    if not AdvancedSearch.validate_report_period(report_type):
        raise HTTPException(
            status_code=400,
            detail="財報期間格式不正確，請輸入 quarterly 或 annual"
        )

    # 獲取排行榜配置
    ranking_config = AdvancedSearch.SUPPORTED_RANKINGS[ranking_type]
    table_name = ranking_config['table']
    
    # 轉換財報期間為資料庫格式
    db_report_type = AdvancedSearch.convert_report_period(report_type)
    
    # 驗證財報類型與期間的組合
    if not AdvancedSearch.validate_report_type_combination(table_name, db_report_type):
        if table_name == 'Cash_Flow_Statements':
            raise HTTPException(
                status_code=400,
                detail="現金流量表只支援 annual 財報期間"
            )
        elif table_name == 'Balance_Sheets':
            raise HTTPException(
                status_code=400,
                detail="資產負債表只支援 quarterly 財報期間"
            )
        else:
            raise HTTPException(
                status_code=400,
                detail=f"不支援的財報類型與期間組合：{table_name} + {report_type}"
            )

    # 驗證產業名稱
    if sector_name and not AdvancedSearch.validate_sector_name(sector_name):
        raise HTTPException(
            status_code=400,
            detail="產業名稱格式不正確，只能包含中英文、數字和空格"
        )

    # 驗證限制數量
    if not AdvancedSearch.validate_limit(limit):
        raise HTTPException(
            status_code=400,
            detail="限制數量格式不正確，請輸入 1-1000 之間的數字"
        )
    
    # 固定每頁筆數為30
    page_size = 30
    
    # 計算分頁偏移量
    offset = (page - 1) * page_size

    try:
        # 獲取排行榜配置
        field_name = ranking_config['field']
        
        # 使用 asyncpg 的非同步連線池獲取連線
        async with postgresql_pool.get_connection() as conn:
            # 構建查詢條件
            where_conditions = ["fr.year = $1", "fr.report_type = $2"]
            params = [year, db_report_type]
            param_index = 3
            
            # 添加季度條件
            if quarter is not None:
                where_conditions.append(f"fr.quarter = ${param_index}")
                params.append(quarter)
                param_index += 1
            
            # 添加產業條件
            if sector_name:
                where_conditions.append(f"s.sector_name = ${param_index}")
                params.append(sector_name)
                param_index += 1
            
            # 構建完整的查詢語句 (使用分頁)
            query = f"""
                SELECT 
                    c.stock_symbol,
                    c.company_name,
                    s.sector_name,
                    ct.country_name,
                    fr.{field_name},
                    fr.year,
                    fr.quarter,
                    fr.report_type,
                    ROW_NUMBER() OVER (ORDER BY fr.{field_name} DESC NULLS LAST) as rank
                FROM {table_name} AS fr
                INNER JOIN Companies AS c ON fr.company_id = c.company_id
                INNER JOIN Sectors AS s ON c.sector_id = s.sector_id
                INNER JOIN Countrys AS ct ON c.country_id = ct.country_id
                WHERE {' AND '.join(where_conditions)}
                ORDER BY fr.{field_name} DESC NULLS LAST
                LIMIT ${param_index} OFFSET ${param_index + 1};
            """
            params.extend([page_size, offset])
            
            results = await conn.fetch(query, *params)
            
            # 將 asyncpg.Record 物件轉換為字典列表
            formatted_results = [dict(record) for record in results]
            formatted_results = AdvancedSearch.decimal_to_float(formatted_results)

            if not formatted_results:
                return JSONResponse(
                    status_code=404, 
                    content={
                        "message": "未找到相關排行榜資料",
                        "ranking_type": ranking_type,
                        "year": year,
                        "report_type": report_type,
                        "sector_name": sector_name,
                        "quarter": quarter
                    }
                )

            return JSONResponse(
                status_code=200,
                content={
                    "data": formatted_results,
                    "metadata": {
                        "ranking_type": ranking_type,
                        "description": ranking_config['description'],
                        "year": year,
                        "report_type": report_type,
                        "db_report_type": db_report_type,
                        "sector_name": sector_name,
                        "quarter": quarter,
                        "limit": limit,
                        "page": page,
                        "page_size": page_size,
                        "current_page_count": len(formatted_results),
                        "has_next_page": len(formatted_results) == page_size and (page * page_size) < limit
                    },
                    "status": "ok"
                }
            )

    except Exception as e:
        # 捕捉其他未預期的資料庫錯誤
        print(f"資料庫查詢錯誤: {e}")
        raise HTTPException(status_code=500, detail="內部伺服器錯誤")


@router.get("/api/advanced_search/supported_rankings")
async def get_supported_rankings():
    """
    獲取支援的排行榜類型列表
    """
    return JSONResponse(
        status_code=200,
        content={
            "data": AdvancedSearch.SUPPORTED_RANKINGS,
            "status": "ok"
        }
    )


@router.get("/api/advanced_search/report_type_rules")
async def get_report_type_rules():
    """
    獲取財報類型與期間的對應規則
    """
    rules = {
        'Cash_Flow_Statements': {
            'supported_periods': ['annual'],
            'quarter_rule': '自動使用第4季',
            'description': '現金流量表只支援年度財報'
        },
        'Income_Statements': {
            'supported_periods': ['quarterly', 'annual'],
            'quarter_rule': 'quarterly需指定季度(1-4), annual自動使用第4季',
            'description': '損益表支援單季和年度財報'
        },
        'Balance_Sheets': {
            'supported_periods': ['quarterly'],
            'quarter_rule': '必須指定季度(1-4)',
            'description': '資產負債表只支援單季財報'
        }
    }
    
    return JSONResponse(
        status_code=200,
        content={
            "data": rules,
            "status": "ok"
        }
    )


@router.get("/api/advanced_search/count")
async def get_ranking_count(
    ranking_type: str = Query(..., description="排行榜類型"),
    year: int = Query(..., description="年份"),
    report_type: str = Query(..., description="財報期間 (quarterly, annual)"),
    sector_name: Optional[str] = Query(None, description="產業名稱 (可選)"),
    quarter: Optional[int] = Query(None, description="季度 (1-4, 可選)")
):
    """
    獲取排行榜總筆數 (用於分頁計算)
    """
    
    # 驗證排行榜類型
    if not AdvancedSearch.validate_ranking_type(ranking_type):
        supported_types = list(AdvancedSearch.SUPPORTED_RANKINGS.keys())
        raise HTTPException(
            status_code=400,
            detail=f"不支援的排行榜類型：{ranking_type}。支援的類型：{', '.join(supported_types)}"
        )

    # 驗證年份
    if not AdvancedSearch.validate_year(year):
        raise HTTPException(
            status_code=400,
            detail="年份格式不正確，請輸入 1900-2025 之間的年份"
        )

    # 驗證季度
    if not AdvancedSearch.validate_quarter(quarter):
        raise HTTPException(
            status_code=400,
            detail="季度格式不正確，請輸入 1-4 之間的數字"
        )
    
    # 處理季度邏輯
    if report_type == 'quarterly':
        if quarter is None:
            raise HTTPException(
                status_code=400,
                detail="quarterly 財報期間必須指定季度 (1-4)"
            )
    elif report_type == 'annual':
        # annual 財報自動使用第4季
        if quarter is None:
            quarter = 4
        elif quarter != 4:
            raise HTTPException(
                status_code=400,
                detail="annual 財報期間只能使用第4季"
            )

    # 驗證財報期間
    if not AdvancedSearch.validate_report_period(report_type):
        raise HTTPException(
            status_code=400,
            detail="財報期間格式不正確，請輸入 quarterly 或 annual"
        )

    # 獲取排行榜配置
    ranking_config = AdvancedSearch.SUPPORTED_RANKINGS[ranking_type]
    table_name = ranking_config['table']
    
    # 轉換財報期間為資料庫格式
    db_report_type = AdvancedSearch.convert_report_period(report_type)
    
    # 驗證財報類型與期間的組合
    if not AdvancedSearch.validate_report_type_combination(table_name, db_report_type):
        if table_name == 'Cash_Flow_Statements':
            raise HTTPException(
                status_code=400,
                detail="現金流量表只支援 annual 財報期間"
            )
        elif table_name == 'Balance_Sheets':
            raise HTTPException(
                status_code=400,
                detail="資產負債表只支援 quarterly 財報期間"
            )
        else:
            raise HTTPException(
                status_code=400,
                detail=f"不支援的財報類型與期間組合：{table_name} + {report_type}"
            )

    # 驗證產業名稱
    if sector_name and not AdvancedSearch.validate_sector_name(sector_name):
        raise HTTPException(
            status_code=400,
            detail="產業名稱格式不正確，只能包含中英文、數字和空格"
        )

    try:
        # 使用 asyncpg 的非同步連線池獲取連線
        async with postgresql_pool.get_connection() as conn:
            # 構建查詢條件
            where_conditions = ["fr.year = $1", "fr.report_type = $2"]
            params = [year, db_report_type]
            param_index = 3
            
            # 添加季度條件
            if quarter is not None:
                where_conditions.append(f"fr.quarter = ${param_index}")
                params.append(quarter)
                param_index += 1
            
            # 添加產業條件
            if sector_name:
                where_conditions.append(f"s.sector_name = ${param_index}")
                params.append(sector_name)
                param_index += 1
            
            # 構建計數查詢語句
            count_query = f"""
                SELECT COUNT(*) as total_count
                FROM {table_name} AS fr
                INNER JOIN Companies AS c ON fr.company_id = c.company_id
                INNER JOIN Sectors AS s ON c.sector_id = s.sector_id
                INNER JOIN Countrys AS ct ON c.country_id = ct.country_id
                WHERE {' AND '.join(where_conditions)};
            """
            
            result = await conn.fetchrow(count_query, *params)
            total_count = result['total_count'] if result else 0

            return JSONResponse(
                status_code=200,
                content={
                    "data": {
                        "total_count": total_count,
                        "ranking_type": ranking_type,
                        "year": year,
                        "report_type": report_type,
                        "sector_name": sector_name,
                        "quarter": quarter
                    },
                    "status": "ok"
                }
            )

    except Exception as e:
        # 捕捉其他未預期的資料庫錯誤
        print(f"資料庫查詢錯誤: {e}")
        raise HTTPException(status_code=500, detail="內部伺服器錯誤") 


@router.get("/api/advanced_search/stock_ranking")
async def get_stock_ranking(
    stock_symbol: str = Query(..., description="股票代碼", min_length=3),
    year: int = Query(..., description="年份"),
    report_type: str = Query(..., description="財報期間 (quarterly, annual)"),
    quarter: Optional[int] = Query(None, description="季度 (1-4, 可選)"),
    statement_type: str = Query(..., description="財報表類型 (cash_flow, income_statement, balance_sheet)")
):
    """
    查詢單一股票在指定財報表的所有指標中的排名
    
    查詢邏輯：
    1. 根據股票代碼查詢該股票所在的國家和產業
    2. 根據 statement_type 僅查詢該表的指標
    3. 根據財報類型規則驗證參數：
       - cash_flow: 只支援 report_type=annual (accumulated, quarter=4)
       - income_statement: 支援 quarterly 和 annual
       - balance_sheet: 只支援 quarterly
    4. 查詢該股票在相同國家、產業、年份、季度下的所有指標排名
    5. 回傳包含排名資訊的完整結果
    """
    # 驗證股票代碼
    if not Financial_report.validate_stock_symbol(stock_symbol):
        raise HTTPException(
            status_code=400,
            detail="股票代碼格式不正確，只能包含英文字母和數字"
        )
    # 驗證年份
    if not AdvancedSearch.validate_year(year):
        raise HTTPException(
            status_code=400,
            detail="年份格式不正確，必須在 1900-2025 之間"
        )
    # 驗證 statement_type
    valid_statement_types = ["cash_flow", "income_statement", "balance_sheet"]
    if statement_type not in valid_statement_types:
        raise HTTPException(
            status_code=400,
            detail=f"statement_type 必須為 {valid_statement_types} 之一"
        )
    # 驗證 report_type
    if not AdvancedSearch.validate_report_period(report_type):
        raise HTTPException(
            status_code=400,
            detail="不支援的財報期間，必須是 'quarterly' 或 'annual'"
        )
    db_report_type = AdvancedSearch.convert_report_period(report_type)
    # 根據 statement_type 檢查 report_type/quarter 規則
    if statement_type == "cash_flow":
        if db_report_type != "accumulated":
            raise HTTPException(
                status_code=400,
                detail="現金流量表只支援年報 (annual) 查詢"
            )
        quarter = 4
    elif statement_type == "income_statement":
        if db_report_type == "accumulated":
            quarter = 4
        elif db_report_type == "quarterly":
            if quarter is None:
                raise HTTPException(
                    status_code=400,
                    detail="損益表季報查詢必須指定季度 (1-4)"
                )
            if not AdvancedSearch.validate_quarter(quarter):
                raise HTTPException(
                    status_code=400,
                    detail="季度格式不正確，必須是 1-4"
                )
    elif statement_type == "balance_sheet":
        if db_report_type != "quarterly":
            raise HTTPException(
                status_code=400,
                detail="資產負債表只支援季報 (quarterly) 查詢"
            )
        if quarter is None:
            raise HTTPException(
                status_code=400,
                detail="資產負債表季報查詢必須指定季度 (1-4)"
            )
        if not AdvancedSearch.validate_quarter(quarter):
            raise HTTPException(
                status_code=400,
                detail="季度格式不正確，必須是 1-4"
            )
    try:
        async with postgresql_pool.get_connection() as conn:
            stock_info_query = """
                SELECT 
                    c.stock_symbol,
                    ct.country_name,
                    s.sector_name,
                    c.company_id
                FROM Companies AS c
                INNER JOIN Countrys AS ct ON c.country_id = ct.country_id
                INNER JOIN Sectors AS s ON c.sector_id = s.sector_id
                WHERE c.stock_symbol = $1
            """
            stock_info = await conn.fetchrow(stock_info_query, stock_symbol)
            if not stock_info:
                raise HTTPException(
                    status_code=404,
                    detail=f"未找到股票代碼 {stock_symbol} 的資料"
                )
            country_name = stock_info['country_name']
            sector_name = stock_info['sector_name']
            company_id = stock_info['company_id']
            # 只查詢該 statement_type 對應的指標
            table_map = {
                "cash_flow": "Cash_Flow_Statements",
                "income_statement": "Income_Statements",
                "balance_sheet": "Balance_Sheets"
            }
            table_name = table_map[statement_type]
            # 過濾指標
            filtered_rankings = {
                k: v for k, v in AdvancedSearch.SUPPORTED_RANKINGS.items() if v['table'] == table_name
            }
            results = {}
            for ranking_key, ranking_config in filtered_rankings.items():
                field_name = ranking_config['field']
                ranking_query = f"""
                    WITH RankedData AS (
                        SELECT 
                            c.stock_symbol,
                            c.company_id,
                            fr.{field_name},
                            ROW_NUMBER() OVER (
                                ORDER BY fr.{field_name} DESC NULLS LAST
                            ) as rank,
                            COUNT(*) OVER () as total_count
                        FROM {table_name} AS fr
                        INNER JOIN Companies AS c ON fr.company_id = c.company_id
                        INNER JOIN Countrys AS ct ON c.country_id = ct.country_id
                        INNER JOIN Sectors AS s ON c.sector_id = s.sector_id
                        WHERE ct.country_name = $1 
                        AND s.sector_name = $2 
                        AND fr.year = $3 
                        AND fr.report_type = $4 
                        AND fr.quarter = $5
                        AND fr.{field_name} IS NOT NULL
                    )
                    SELECT 
                        stock_symbol,
                        {field_name} as value,
                        rank,
                        total_count
                    FROM RankedData
                    WHERE company_id = $6
                """
                ranking_result = await conn.fetchrow(
                    ranking_query, 
                    country_name, 
                    sector_name, 
                    year, 
                    db_report_type, 
                    quarter, 
                    company_id
                )
                if ranking_result:
                    results[ranking_key] = {
                        'description': ranking_config['description'],
                        'value': float(ranking_result['value']) if ranking_result['value'] is not None else None,
                        'rank': ranking_result['rank'],
                        'total_count': ranking_result['total_count'],
                        'table': table_name,
                        'field': field_name
                    }
                else:
                    results[ranking_key] = {
                        'description': ranking_config['description'],
                        'value': None,
                        'rank': None,
                        'total_count': 0,
                        'table': table_name,
                        'field': field_name,
                        'note': '該指標在此期間無資料'
                    }
            response_data = {
                'stock_info': {
                    'stock_symbol': stock_symbol,
                    'country': country_name,
                    'sector': sector_name
                },
                'query_params': {
                    'year': year,
                    'report_type': report_type,
                    'quarter': quarter,
                    'statement_type': statement_type
                },
                'rankings': results,
                'summary': {
                    'total_metrics': len(results),
                    'metrics_with_rank': len([r for r in results.values() if r['rank'] is not None]),
                    'metrics_without_data': len([r for r in results.values() if r['rank'] is None])
                }
            }
            return JSONResponse(
                status_code=200,
                content={
                    "data": response_data,
                    "status": "ok"
                }
            )
    except HTTPException as e:
        raise e
    except Exception as e:
        print(f"查詢股票排名時發生錯誤: {e}")
        raise HTTPException(status_code=500, detail="內部伺服器錯誤")


 