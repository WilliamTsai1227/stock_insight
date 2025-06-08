from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import psycopg2
from typing import List, Optional

app = FastAPI(title="Financial Analytics API")

# 資料庫連線設定
def get_db_connection():
    return psycopg2.connect(dbname="financial_db", user="postgres", password="your_password")

@app.get("/stock_metrics")
async def stock_metrics(year: int, company_name: Optional[str] = None, stock_symbol: Optional[str] = None, country: Optional[str] = None):
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        # 查詢公司資訊
        if company_name:
            cur.execute("""
                SELECT c.company_id, c.company_name, c.sector_id, c.country, s.sector_name
                FROM Companies c
                JOIN Sectors s ON c.sector_id = s.sector_id
                WHERE c.company_name = %s
            """, (company_name,))
        elif stock_symbol and country:
            cur.execute("""
                SELECT c.company_id, c.company_name, c.sector_id, c.country, s.sector_name
                FROM Companies c
                JOIN Sectors s ON c.sector_id = s.sector_id
                WHERE c.stock_symbol = %s AND c.country = %s
            """, (stock_symbol, country))
        else:
            raise HTTPException(status_code=400, detail="Must provide company_name or both stock_symbol and country")

        if cur.rowcount == 0:
            raise HTTPException(status_code=404, detail="Company not found")
        company_id, company_name, sector_id, country, sector_name = cur.fetchone()

        # 獲取指定年份的年度數據
        cur.execute("""
            SELECT pe_ratio, revenue, operating_income, net_income
            FROM Income_Statements
            WHERE company_id = %s AND year = %s AND quarter IS NULL
        """, (company_id, year))
        pe_ratio, revenue, operating_income, net_income = cur.fetchone() if cur.rowcount > 0 else (None, None, None, None)

        # 獲取同業平均（同一產業，同一國家）
        cur.execute("""
            SELECT AVG(pe_ratio), AVG(revenue), AVG(operating_income), AVG(net_income)
            FROM Income_Statements i
            JOIN Companies c ON i.company_id = c.company_id
            WHERE c.sector_id = %s AND c.country = %s AND i.year = %s AND i.quarter IS NULL
        """, (sector_id, country, year))
        avg_pe_ratio, avg_revenue, avg_operating_income, avg_net_income = cur.fetchone()

        # 獲取排名
        cur.execute("""
            SELECT COUNT(*) + 1 AS rank, (SELECT COUNT(*) FROM Companies WHERE sector_id = %s AND country = %s) AS total
            FROM Income_Statements i
            JOIN Companies c ON i.company_id = c.company_id
            WHERE c.sector_id = %s AND c.country = %s AND i.year = %s AND i.quarter IS NULL
            AND i.pe_ratio > (SELECT pe_ratio FROM Income_Statements WHERE company_id = %s AND year = %s AND quarter IS NULL)
        """, (sector_id, country, sector_id, country, year, company_id, year))
        pe_rank, total_companies = cur.fetchone() if cur.rowcount > 0 else (None, None)

        cur.execute("""
            SELECT COUNT(*) + 1 AS rank
            FROM Income_Statements i
            JOIN Companies c ON i.company_id = c.company_id
            WHERE c.sector_id = %s AND c.country = %s AND i.year = %s AND i.quarter IS NULL
            AND i.revenue > (SELECT revenue FROM Income_Statements WHERE company_id = %s AND year = %s AND quarter IS NULL)
        """, (sector_id, country, year, company_id, year))
        revenue_rank = cur.fetchone()[0] if cur.rowcount > 0 else None

        cur.execute("""
            SELECT COUNT(*) + 1 AS rank
            FROM Income_Statements i
            JOIN Companies c ON i.company_id = c.company_id
            WHERE c.sector_id = %s AND c.country = %s AND i.year = %s AND i.quarter IS NULL
            AND i.operating_income > (SELECT operating_income FROM Income_Statements WHERE company_id = %s AND year = %s AND quarter IS NULL)
        """, (sector_id, country, year, company_id, year))
        operating_income_rank = cur.fetchone()[0] if cur.rowcount > 0 else None

        cur.execute("""
            SELECT COUNT(*) + 1 AS rank
            FROM Income_Statements i
            JOIN Companies c ON i.company_id = c.company_id
            WHERE c.sector_id = %s AND c.country = %s AND i.year = %s AND i.quarter IS NULL
            AND i.net_income > (SELECT net_income FROM Income_Statements WHERE company_id = %s AND year = %s AND quarter IS NULL)
        """, (sector_id, country, year, company_id, year))
        net_income_rank = cur.fetchone()[0] if cur.rowcount > 0 else None

        # 獲取歷史數據（季度）
        cur.execute("""
            SELECT year, quarter, pe_ratio, revenue, operating_income, net_income
            FROM Income_Statements
            WHERE company_id = %s AND quarter IS NOT NULL
            ORDER BY year, quarter
        """, (company_id,))
        company_history = [
            {'year': row[0], 'quarter': row[1], 'pe_ratio': row[2], 'revenue': row[3], 
             'operating_income': row[4], 'net_income': row[5]}
            for row in cur.fetchall()
        ]

        cur.execute("""
            SELECT i.year, i.quarter, AVG(i.pe_ratio), AVG(i.revenue), AVG(i.operating_income), AVG(i.net_income)
            FROM Income_Statements i
            JOIN Companies c ON i.company_id = c.company_id
            WHERE c.sector_id = %s AND c.country = %s AND i.quarter IS NOT NULL
            GROUP BY i.year, i.quarter
            ORDER BY i.year, i.quarter
        """, (sector_id, country))
        industry_history = [
            {'year': row[0], 'quarter': row[1], 'avg_pe_ratio': row[2], 'avg_revenue': row[3], 
             'avg_operating_income': row[4], 'avg_net_income': row[5]}
            for row in cur.fetchall()
        ]

        return {
            'company_id': company_id,
            'company_name': company_name,
            'sector_name': sector_name,
            'country': country,
            'year': year,
            'pe_ratio': pe_ratio,
            'pe_rank': pe_rank,
            'total_companies': total_companies,
            'avg_pe_ratio': avg_pe_ratio,
            'revenue': revenue,
            'revenue_rank': revenue_rank,
            'avg_revenue': avg_revenue,
            'operating_income': operating_income,
            'operating_income_rank': operating_income_rank,
            'avg_operating_income': avg_operating_income,
            'net_income': net_income,
            'net_income_rank': net_income_rank,
            'avg_net_income': avg_net_income,
            'company_history': company_history,
            'industry_history': industry_history
        }
    finally:
        cur.close()
        conn.close()

@app.get("/stock_growth_analysis")
async def stock_growth_analysis(company_name: Optional[str] = None, stock_symbol: Optional[str] = None, country: Optional[str] = None):
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        # 查詢公司資訊
        if company_name:
            cur.execute("""
                SELECT c.company_id, c.company_name, c.sector_id, c.country
                FROM Companies c
                WHERE c.company_name = %s
            """, (company_name,))
        elif stock_symbol and country:
            cur.execute("""
                SELECT c.company_id, c.company_name, c.sector_id, c.country
                FROM Companies c
                WHERE c.stock_symbol = %s AND c.country = %s
            """, (stock_symbol, country))
        else:
            raise HTTPException(status_code=400, detail="Must provide company_name or both stock_symbol and country")

        if cur.rowcount == 0:
            raise HTTPException(status_code=404, detail="Company not found")
        company_id, company_name, sector_id, country = cur.fetchone()

        # 獲取年度數據
        cur.execute("""
            SELECT year, revenue, operating_income, net_income
            FROM Income_Statements
            WHERE company_id = %s AND quarter IS NULL
            ORDER BY year
        """, (company_id,))
        income_data = [
            {'year': row[0], 'revenue': row[1], 'operating_income': row[2], 'net_income': row[3]}
            for row in cur.fetchall()
        ]

        cur.execute("""
            SELECT year, current_assets, current_liabilities, shareholders_equity
            FROM Balance_Sheets
            WHERE company_id = %s AND quarter IS NULL
            ORDER BY year
        """, (company_id,))
        balance_data = [
            {'year': row[0], 'current_assets': row[1], 'current_liabilities': row[2], 'shareholders_equity': row[3]}
            for row in cur.fetchall()
        ]

        cur.execute("""
            SELECT year, free_cash_flow
            FROM Cash_Flow_Statements
            WHERE company_id = %s AND quarter IS NULL
            ORDER BY year
        """, (company_id,))
        cash_flow_data = [{'year': row[0], 'free_cash_flow': row[1]} for row in cur.fetchall()]

        # 計算成長分析
        analysis = {
            'revenue': [], 'operating_income': [], 'net_income': [],
            'current_assets_vs_liabilities': [], 'shareholders_equity': [], 'free_cash_flow': []
        }

        for i in range(len(income_data)):
            year = income_data[i]['year']
            analysis['revenue'].append({'year': year, 'value': income_data[i]['revenue']})
            analysis['operating_income'].append({'year': year, 'value': income_data[i]['operating_income']})
            analysis['net_income'].append({'year': year, 'value': income_data[i]['net_income']})

        for i in range(len(balance_data)):
            year = balance_data[i]['year']
            current_assets = balance_data[i]['current_assets']
            current_liabilities = balance_data[i]['current_liabilities']
            analysis['current_assets_vs_liabilities'].append({
                'year': year,
                'current_assets': current_assets,
                'current_liabilities': current_liabilities,
                'status': '✓ Valid' if current_assets and current_liabilities and current_assets > current_liabilities else '❌ Invalid'
            })
            analysis['shareholders_equity'].append({'year': year, 'value': balance_data[i]['shareholders_equity']})

        for i in range(len(cash_flow_data)):
            year = cash_flow_data[i]['year']
            analysis['free_cash_flow'].append({'year': year, 'value': cash_flow_data[i]['free_cash_flow']})

        # 計算逐年變化
        for metric in ['revenue', 'operating_income', 'net_income', 'shareholders_equity', 'free_cash_flow']:
            analysis[metric + '_changes'] = []
            for i in range(1, len(analysis[metric])):
                curr = analysis[metric][i]
                prev = analysis[metric][i-1]
                change = curr['value'] - prev['value'] if curr['value'] and prev['value'] else None
                percentage = (change / prev['value'] * 100) if change and prev['value'] else None
                analysis[metric + '_changes'].append({
                    'from_year': prev['year'],
                    'to_year': curr['year'],
                    'change': change,
                    'percentage': percentage,
                    'direction': '📈' if change and change > 0 else '📉' if change else None
                })

            # 2022 vs. 2024 疫情恢復分析
            y2022 = next((x for x in analysis[metric] if x['year'] == 2022), None)
            y2024 = next((x for x in analysis[metric] if x['year'] == 2024), None)
            if y2022 and y2024:
                change = y2024['value'] - y2022['value'] if y2024['value'] and y2022['value'] else None
                percentage = (change / y2022['value'] * 100) if change and y2022['value'] else None
                analysis[metric + '_pandemic'] = {
                    'from_year': 2022,
                    'to_year': 2024,
                    'change': change,
                    'percentage': percentage,
                    'status': '⚠️ Not Recovered' if change and change < 0 else '✓ Recovered'
                }

            # 檢查非 2023 年成長
            non_2023_changes = [c for c in analysis[metric + '_changes'] if c['to_year'] != 2023]
            analysis[metric + '_non_2023_growth'] = all(c['change'] > 0 for c in non_2023_changes if c['change']) if non_2023_changes else False

        return {
            'company_id': company_id,
            'company_name': company_name,
            'analysis': analysis
        }
    finally:
        cur.close()
        conn.close()

class SearchRequest(BaseModel):
    years: List[int]
    quarters: List[str]
    countries: List[str]
    sectors: List[str]  # sector_name
    filters: List[str]

@app.post("/advanced_search")
async def advanced_search(request: SearchRequest):
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        years = request.years
        quarters = request.quarters
        countries = request.countries if request.countries else ['%']
        sectors = request.sectors if request.sectors else ['%']
        filters = request.filters

        # 構建查詢
        conditions = []
        joins = []
        params = []

        # 國家和產業篩選
        conditions.append("c.country LIKE ANY(%s)")
        conditions.append("s.sector_name LIKE ANY(%s)")
        params.extend([countries, sectors])

        for year in years:
            for quarter in quarters:
                q = 'NULL' if quarter == 'YEAR' else quarter
                for filter in filters:
                    if filter == 'pe_ratio_below_25':
                        conditions.append(f"(i{year}.pe_ratio < 25 AND i{year-1}.pe_ratio < 25)")
                        joins.append(f"""
                            LEFT JOIN Income_Statements i{year} ON i{year}.company_id = c.company_id AND i{year}.year = {year} AND i{year}.quarter {"= %s" if q != 'NULL' else "IS NULL"}
                            LEFT JOIN Income_Statements i{year-1} ON i{year-1}.company_id = c.company_id AND i{year-1}.year = {year-1} AND i{year-1}.quarter {"= %s" if q != 'NULL' else "IS NULL"}
                        """)
                        if q != 'NULL':
                            params.extend([q, q])
                    elif filter == 'pe_ratio_below_25_current':
                        conditions.append(f"i{year}.pe_ratio < 25")
                        joins.append(f"""
                            LEFT JOIN Income_Statements i{year} ON i{year}.company_id = c.company_id AND i{year}.year = {year} AND i{year}.quarter {"= %s" if q != 'NULL' else "IS NULL"}
                        """)
                        if q != 'NULL':
                            params.append(q)
                    elif filter == 'revenue_growth':
                        conditions.append(f"i{year}.revenue > i{year-1}.revenue")
                        joins.append(f"""
                            LEFT JOIN Income_Statements i{year} ON i{year}.company_id = c.company_id AND i{year}.year = {year} AND i{year}.quarter {"= %s" if q != 'NULL' else "IS NULL"}
                            LEFT JOIN Income_Statements i{year-1} ON i{year-1}.company_id = c.company_id AND i{year-1}.year = {year-1} AND i{year-1}.quarter {"= %s" if q != 'NULL' else "IS NULL"}
                        """)
                        if q != 'NULL':
                            params.extend([q, q])
                    elif filter == 'operating_income_growth':
                        conditions.append(f"i{year}.operating_income > i{year-1}.operating_income")
                        joins.append(f"""
                            LEFT JOIN Income_Statements i{year} ON i{year}.company_id = c.company_id AND i{year}.year = {year} AND i{year}.quarter {"= %s" if q != 'NULL' else "IS NULL"}
                            LEFT JOIN Income_Statements i{year-1} ON i{year-1}.company_id = c.company_id AND i{year-1}.year = {year-1} AND i{year-1}.quarter {"= %s" if q != 'NULL' else "IS NULL"}
                        """)
                        if q != 'NULL':
                            params.extend([q, q])
                    elif filter == 'net_income_growth':
                        conditions.append(f"i{year}.net_income > i{year-1}.net_income")
                        joins.append(f"""
                            LEFT JOIN Income_Statements i{year} ON i{year}.company_id = c.company_id AND i{year}.year = {year} AND i{year}.quarter {"= %s" if q != 'NULL' else "IS NULL"}
                            LEFT JOIN Income_Statements i{year-1} ON i{year-1}.company_id = c.company_id AND i{year-1}.year = {year-1} AND i{year-1}.quarter {"= %s" if q != 'NULL' else "IS NULL"}
                        """)
                        if q != 'NULL':
                            params.extend([q, q])
                    elif filter == 'current_assets_above_liabilities':
                        conditions.append(f"(b{year}.current_assets > b{year}.current_liabilities AND b{year-1}.current_assets > b{year-1}.current_liabilities)")
                        joins.append(f"""
                            LEFT JOIN Balance_Sheets b{year} ON b{year}.company_id = c.company_id AND b{year}.year = {year} AND b{year}.quarter {"= %s" if q != 'NULL' else "IS NULL"}
                            LEFT JOIN Balance_Sheets b{year-1} ON b{year-1}.company_id = c.company_id AND b{year-1}.year = {year-1} AND b{year-1}.quarter {"= %s" if q != 'NULL' else "IS NULL"}
                        """)
                        if q != 'NULL':
                            params.extend([q, q])
                    elif filter == 'current_assets_above_liabilities_current':
                        conditions.append(f"b{year}.current_assets > b{year}.current_liabilities")
                        joins.append(f"""
                            LEFT JOIN Balance_Sheets b{year} ON b{year}.company_id = c.company_id AND b{year}.year = {year} AND b{year}.quarter {"= %s" if q != 'NULL' else "IS NULL"}
                        """)
                        if q != 'NULL':
                            params.append(q)
                    elif filter == 'long_term_debt_to_net_income_below_4':
                        conditions.append(f"(b{year}.long_term_debt / i{year}.net_income < 4 AND b{year-1}.long_term_debt / i{year-1}.net_income < 4)")
                        joins.append(f"""
                            LEFT JOIN Income_Statements i{year} ON i{year}.company_id = c.company_id AND i{year}.year = {year} AND i{year}.quarter {"= %s" if q != 'NULL' else "IS NULL"}
                            LEFT JOIN Income_Statements i{year-1} ON i{year-1}.company_id = c.company_id AND i{year-1}.year = {year-1} AND i{year-1}.quarter {"= %s" if q != 'NULL' else "IS NULL"}
                            LEFT JOIN Balance_Sheets b{year} ON b{year}.company_id = c.company_id AND b{year}.year = {year} AND b{year}.quarter {"= %s" if q != 'NULL' else "IS NULL"}
                            LEFT JOIN Balance_Sheets b{year-1} ON b{year-1}.company_id = c.company_id AND b{year-1}.year = {year-1} AND b{year-1}.quarter {"= %s" if q != 'NULL' else "IS NULL"}
                        """)
                        if q != 'NULL':
                            params.extend([q, q, q, q])
                    elif filter == 'long_term_debt_to_net_income_below_4_current':
                        conditions.append(f"b{year}.long_term_debt / i{year}.net_income < 4")
                        joins.append(f"""
                            LEFT JOIN Income_Statements i{year} ON i{year}.company_id = c.company_id AND i{year}.year = {year} AND i{year}.quarter {"= %s" if q != 'NULL' else "IS NULL"}
                            LEFT JOIN Balance_Sheets b{year} ON b{year}.company_id = c.company_id AND b{year}.year = {year} AND b{year}.quarter {"= %s" if q != 'NULL' else "IS NULL"}
                        """)
                        if q != 'NULL':
                            params.extend([q, q])
                    elif filter == 'shareholders_equity_growth':
                        conditions.append(f"b{year}.shareholders_equity > b{year-1}.shareholders_equity")
                        joins.append(f"""
                            LEFT JOIN Balance_Sheets b{year} ON b{year}.company_id = c.company_id AND b{year}.year = {year} AND b{year}.quarter {"= %s" if q != 'NULL' else "IS NULL"}
                            LEFT JOIN Balance_Sheets b{year-1} ON b{year-1}.company_id = c.company_id AND b{year-1}.year = {year-1} AND b{year-1}.quarter {"= %s" if q != 'NULL' else "IS NULL"}
                        """)
                        if q != 'NULL':
                            params.extend([q, q])
                    elif filter == 'shares_outstanding_decline':
                        conditions.append(f"b{year}.shares_outstanding < b{year-1}.shares_outstanding")
                        joins.append(f"""
                            LEFT JOIN Balance_Sheets b{year} ON b{year}.company_id = c.company_id AND b{year}.year = {year} AND b{year}.quarter {"= %s" if q != 'NULL' else "IS NULL"}
                            LEFT JOIN Balance_Sheets b{year-1} ON b{year-1}.company_id = c.company_id AND b{year-1}.year = {year-1} AND b{year-1}.quarter {"= %s" if q != 'NULL' else "IS NULL"}
                        """)
                        if q != 'NULL':
                            params.extend([q, q])
                    elif filter == 'operating_cash_flow_above_investing_financing':
                        conditions.append(f"""
                            (cf{year}.operating_cash_flow > (cf{year}.investing_cash_flow + cf{year}.financing_cash_flow) AND
                             cf{year-1}.operating_cash_flow > (cf{year-1}.investing_cash_flow + cf{year-1}.financing_cash_flow))
                        """)
                        joins.append(f"""
                            LEFT JOIN Cash_Flow_Statements cf{year} ON cf{year}.company_id = c.company_id AND cf{year}.year = {year} AND cf{year}.quarter {"= %s" if q != 'NULL' else "IS NULL"}
                            LEFT JOIN Cash_Flow_Statements cf{year-1} ON cf{year-1}.company_id = c.company_id AND cf{year-1}.year = {year-1} AND cf{year-1}.quarter {"= %s" if q != 'NULL' else "IS NULL"}
                        """)
                        if q != 'NULL':
                            params.extend([q, q])
                    elif filter == 'operating_cash_flow_above_investing_financing_current':
                        conditions.append(f"cf{year}.operating_cash_flow > (cf{year}.investing_cash_flow + cf{year}.financing_cash_flow)")
                        joins.append(f"""
                            LEFT JOIN Cash_Flow_Statements cf{year} ON cf{year}.company_id = c.company_id AND cf{year}.year = {year} AND cf{year}.quarter {"= %s" if q != 'NULL' else "IS NULL"}
                        """)
                        if q != 'NULL':
                            params.append(q)
                    elif filter == 'free_cash_flow_growth':
                        conditions.append(f"cf{year}.free_cash_flow > cf{year-1}.free_cash_flow")
                        joins.append(f"""
                            LEFT JOIN Cash_Flow_Statements cf{year} ON cf{year}.company_id = c.company_id AND cf{year}.year = {year} AND cf{year}.quarter {"= %s" if q != 'NULL' else "IS NULL"}
                            LEFT JOIN Cash_Flow_Statements cf{year-1} ON cf{year-1}.company_id = c.company_id AND cf{year-1}.year = {year-1} AND cf{year-1}.quarter {"= %s" if q != 'NULL' else "IS NULL"}
                        """)
                        if q != 'NULL':
                            params.extend([q, q])

        query = f"""
            SELECT c.company_id, c.company_name, c.country, s.sector_name
            FROM Companies c
            JOIN Sectors s ON c.sector_id = s.sector_id
            {" ".join(set(joins))}
            WHERE {" AND ".join(conditions)}
            ORDER BY c.company_name
        """
        cur.execute(query, params)
        results = [
            {'company_id': row[0], 'company_name': row[1], 'country': row[2], 'sector_name': row[3]}
            for row in cur.fetchall()
        ]
        return results
    finally:
        cur.close()
        conn.close()