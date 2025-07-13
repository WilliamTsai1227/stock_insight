# Advanced Search Stock Ranking API 說明文件

## 概述

`/api/advanced_search/stock_ranking` API 用於查詢單一股票在**指定財報表**的所有財務指標中的排名。此 API 會根據股票代碼自動識別該股票所在的國家和產業，然後查詢該股票在相同條件下**指定表**的所有支援財務指標排名。

## API 端點

```
GET /api/advanced_search/stock_ranking
```

## 查詢參數

| 參數 | 類型 | 必填 | 描述 | 範例 |
|------|------|------|------|------|
| `stock_symbol` | string | 是 | 股票代碼 | "2330" |
| `year` | integer | 是 | 年份 (1900-2025) | 2023 |
| `report_type` | string | 是 | 財報期間 | "quarterly" 或 "annual" |
| `quarter` | integer | 條件性 | 季度 (1-4) | 1, 2, 3, 4 |
| `statement_type` | string | 是 | 財報表類型 | "cash_flow", "income_statement", "balance_sheet" |

### 參數說明

- **stock_symbol**: 股票代碼，只允許英文字母和數字
- **year**: 查詢年份，必須在 1900-2025 之間
- **report_type**: 
  - `quarterly`: 季度財報
  - `annual`: 年度財報（會自動轉換為 accumulated，quarter=4）
- **quarter**: 僅在 `report_type=quarterly` 時必填，值為 1-4
- **statement_type**: 指定要查詢哪一個財報表的指標
  - `cash_flow`: 現金流量表
  - `income_statement`: 損益表
  - `balance_sheet`: 資產負債表

## 財報類型規則

### cash_flow (現金流量表)
- 只支援 `report_type=annual`（自動設定 `quarter=4`）
- 只回傳現金流量表的指標

### income_statement (損益表)
- 支援 `report_type=quarterly`（需指定 quarter）和 `report_type=annual`（自動設定 `quarter=4`）
- 只回傳損益表的指標

### balance_sheet (資產負債表)
- 只支援 `report_type=quarterly`（需指定 quarter）
- 只回傳資產負債表的指標

## 回傳格式

```json
{
  "status": "ok",
  "data": {
    "stock_info": {
      "stock_symbol": "2330",
      "country": "Taiwan",
      "sector": "半導體業"
    },
    "query_params": {
      "year": 2023,
      "report_type": "annual",
      "quarter": 4,
      "statement_type": "cash_flow"
    },
    "rankings": {
      "operating_cash_flow": {
        "description": "營業活動之現金流量排行榜",
        "value": 12345.6,
        "rank": 3,
        "total_count": 45,
        "table": "Cash_Flow_Statements",
        "field": "operating_cash_flow"
      },
      "free_cash_flow": {
        "description": "自由現金流量排行榜",
        "value": null,
        "rank": null,
        "total_count": 0,
        "table": "Cash_Flow_Statements",
        "field": "free_cash_flow",
        "note": "該指標在此期間無資料"
      }
    },
    "summary": {
      "total_metrics": 3,
      "metrics_with_rank": 1,
      "metrics_without_data": 2
    }
  }
}
```

## 回傳欄位說明

### stock_info
- `stock_symbol`: 股票代碼
- `country`: 國家名稱
- `sector`: 產業名稱

### query_params
- `year`: 查詢年份
- `report_type`: 查詢的財報期間
- `quarter`: 實際使用的季度
- `statement_type`: 查詢的財報表類型

### rankings
只包含該 statement_type 對應的指標，每個指標包含：
- `description`: 指標描述
- `value`: 指標數值（如果有資料）
- `rank`: 排名（如果有資料）
- `total_count`: 該指標的總公司數
- `table`: 資料來源表
- `field`: 資料欄位名稱
- `note`: 備註（如果沒有資料）

### summary
- `total_metrics`: 總指標數
- `metrics_with_rank`: 有排名資料的指標數
- `metrics_without_data`: 無資料的指標數

## 錯誤處理

### 400 Bad Request
- 股票代碼格式不正確
- 年份格式不正確
- 不支援的財報期間
- statement_type 不正確
- 現金流量表只支援年報
- 損益表季報查詢必須指定季度
- 資產負債表只支援季報
- 季度格式不正確

### 404 Not Found
- 未找到股票代碼的資料

### 500 Internal Server Error
- 資料庫查詢錯誤

## 使用範例

### 查詢現金流量表（年報）
```bash
curl "http://localhost:8000/api/advanced_search/stock_ranking?stock_symbol=2330&year=2023&report_type=annual&statement_type=cash_flow"
```

### 查詢損益表（季報 Q2）
```bash
curl "http://localhost:8000/api/advanced_search/stock_ranking?stock_symbol=2330&year=2023&report_type=quarterly&quarter=2&statement_type=income_statement"
```

### 查詢資產負債表（季報 Q4）
```bash
curl "http://localhost:8000/api/advanced_search/stock_ranking?stock_symbol=2330&year=2023&report_type=quarterly&quarter=4&statement_type=balance_sheet"
```

## 查詢邏輯

1. **股票資訊查詢**: 根據股票代碼查詢該股票所在的國家和產業
2. **參數驗證**: 驗證年份、財報期間、statement_type 等參數
3. **季度處理**: 
   - `annual` 自動轉換為 `accumulated` 並設定 `quarter=4`
   - `quarterly` 需要驗證季度參數
4. **只查詢指定表的指標**: 根據 statement_type 過濾指標
5. **排名查詢**: 對每個支援的指標，在相同國家、產業、年份、季度條件下查詢排名
6. **結果整理**: 回傳包含所有指標排名的完整結果

## 效能考量

- 只查詢指定表的指標，回傳資料更精簡
- 使用 WITH 子句進行排名計算
- 只查詢有資料的指標
- 提供摘要資訊方便前端處理
- 支援大量指標的批次查詢 



# Advanced Search Ranking API 說明文件

## 概述

`/api/advanced_search/ranking` API 用於查詢各種財報指標的公司排行榜，支援依據年份、財報期間、產業、季度等條件進行進階搜尋，並支援分頁。

## API 端點

```
GET /api/advanced_search/ranking
```

## 查詢參數

| 參數 | 類型 | 必填 | 描述 | 範例 |
|------|------|------|------|------|
| `ranking_type` | string | 是 | 排行榜類型 | "revenue"、"operating_income" 等 |
| `year` | integer | 是 | 年份 (1900-2025) | 2023 |
| `report_type` | string | 是 | 財報期間 | "quarterly" 或 "annual" |
| `quarter` | integer | 條件性 | 季度 (1-4) | 1, 2, 3, 4 |
| `sector_name` | string | 否 | 產業名稱 | "半導體業" |
| `page` | integer | 否 | 頁碼 (從1開始) | 1 |

> 備註：每頁固定回傳 30 筆資料，`page` 預設為 1。

### 參數說明

- **ranking_type**: 指定要查詢的排行榜指標（如營收、毛利、現金流等，詳見支援指標列表）
- **year**: 查詢年份，必須在 1900-2025 之間
- **report_type**: 
  - `quarterly`: 季度財報
  - `annual`: 年度財報（自動查詢第4季，資料庫查詢為 accumulated）
- **quarter**: 僅在 `report_type=quarterly` 時必填，值為 1-4
- **sector_name**: 可選，指定產業名稱
- **page**: 分頁頁碼，預設 1

## 財報類型規則

- **現金流量表 (Cash_Flow_Statements)**: 只支援 `report_type=annual`，自動查詢第4季
- **損益表 (Income_Statements)**: 支援 `report_type=quarterly`（需指定 quarter）和 `report_type=annual`（自動查詢第4季）
- **資產負債表 (Balance_Sheets)**: 只支援 `report_type=quarterly`（需指定 quarter）

## 支援的排行榜類型

- 現金流量表：
  - `operating_cash_flow`：營業活動之現金流量排行榜
  - `free_cash_flow`：自由現金流量排行榜
  - `net_change_in_cash`：現金及約當現金淨變動排行榜
- 損益表：
  - `revenue`：營收排行榜
  - `gross_profit`：營業毛利排行榜
  - `operating_expenses`：營業費用排行榜
  - `operating_income`：營業利益排行榜
  - `net_income`：稅後淨利排行榜
  - `gross_profit_pct`：營業毛利佔營收百分比排行榜
  - `sales_expenses_pct`：銷售費用佔營收百分比排行榜
  - `administrative_expenses_pct`：管理費用佔營收百分比排行榜
  - `research_and_development_expenses_pct`：研發費用佔營收百分比排行榜
  - `operating_expenses_pct`：營業費用佔營收百分比排行榜
  - `operating_income_pct`：營業利益佔營收百分比排行榜
  - `net_income_pct`：稅後淨利佔營收百分比排行榜
  - `cost_of_revenue_pct`：營業成本佔營收百分比排行榜
- 資產負債表：
  - `cash_and_equivalents`：現金及約當現金排行榜
  - `short_term_investments`：短期投資排行榜
  - `accounts_receivable_and_notes`：應收帳款及票據排行榜
  - `inventory`：存貨排行榜
  - `current_assets`：流動資產排行榜
  - `fixed_assets_total`：固定資產排行榜
  - `total_assets`：總資產排行榜
  - `cash_and_equivalents_pct`：現金及約當現金佔總資產百分比排行榜
  - `short_term_investments_pct`：短期投資佔總資產百分比排行榜
  - `accounts_receivable_and_notes_pct`：應收帳款及票據佔總資產百分比排行榜
  - `inventory_pct`：存貨佔總資產百分比排行榜
  - `current_assets_pct`：流動資產佔總資產百分比排行榜
  - `fixed_assets_total_pct`：固定資產佔總資產百分比排行榜
  - `other_non_current_assets_pct`：其餘資產佔總資產百分比排行榜

## 回傳格式

```json
{
  "data": [
    {
      "stock_symbol": "2330",
      "company_name": "台積電",
      "sector_name": "半導體業",
      "country_name": "Taiwan",
      "revenue": 21617.36,
      "year": 2023,
      "quarter": 4,
      "report_type": "accumulated",
      "rank": 1
    },
    ...
  ],
  "metadata": {
    "ranking_type": "revenue",
    "description": "營收排行榜",
    "year": 2023,
    "report_type": "annual",
    "db_report_type": "accumulated",
    "sector_name": null,
    "quarter": 4,
    "page": 1,
    "page_size": 30,
    "current_page_count": 30,
    "has_next_page": true
  },
  "status": "ok"
}
```

## 錯誤處理

- 400 Bad Request：參數錯誤、格式錯誤、財報期間不支援等
- 404 Not Found：查無資料
- 500 Internal Server Error：伺服器錯誤

## 使用範例

### 查詢 2023 年度財報的營收排行榜（分頁查詢）
```bash
curl "http://localhost:8000/api/advanced_search/ranking?ranking_type=revenue&year=2023&report_type=annual&page=1"
```

### 查詢 2023 年第2季半導體業的營業利益排行榜
```bash
curl "http://localhost:8000/api/advanced_search/ranking?ranking_type=operating_income&year=2023&report_type=quarterly&quarter=2&sector_name=半導體業&page=1"
```

### 查詢 2023 年現金流量表排行榜（只能 annual）
```bash
curl "http://localhost:8000/api/advanced_search/ranking?ranking_type=operating_cash_flow&year=2023&report_type=annual&page=1"
```

### 查詢 2023 年第4季資產負債表排行榜（只能 quarterly）
```bash
curl "http://localhost:8000/api/advanced_search/ranking?ranking_type=total_assets&year=2023&report_type=quarterly&quarter=4&page=1"
```

## 分頁說明

- 每頁固定回傳 30 筆資料
- `page` 參數指定頁碼，預設為 1
- 回傳欄位 `has_next_page` 可判斷是否還有下一頁
- 建議搭配 `/api/advanced_search/count` 取得總筆數 