CREATE TABLE Sectors (
    sector_id SERIAL PRIMARY KEY,
    sector_name VARCHAR(100) NOT NULL UNIQUE,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX idx_sectors_sector_name ON Sectors(sector_name);


CREATE TABLE Countrys (
    country_id SERIAL PRIMARY KEY,
    country_name VARCHAR(100) NOT NULL UNIQUE
);
CREATE INDEX idx_countrys_country_name ON Countrys(country_name);


-- Companies Table 企業基本資料表
CREATE TABLE Companies (
    company_id SERIAL PRIMARY KEY,
    stock_symbol VARCHAR(10) NOT NULL, -- 股票代碼
    company_name VARCHAR(255) NOT NULL,       -- 公司名稱
    abbreviation VARCHAR(100),                -- 公司簡稱
    founding_date DATE,                       -- 成立日期
    listed_date DATE,                         -- 上市日期 (取代原有的 listing_date)
    otc_listed_date DATE,                     -- 上櫃日期
    market VARCHAR(50),                       -- 上市/櫃市場 (例如: TWSE, TPEX)
    country_id INTEGER REFERENCES Countrys(country_id), -- 國家 (外鍵）
    address VARCHAR(255),                     -- 公司住址
    chairman VARCHAR(100),                    -- 董事長
    general_manager VARCHAR(100),             -- 總經理
    spokesperson VARCHAR(100),                -- 發言人
    spokesperson_title VARCHAR(100),          -- 發言人職稱
    outstanding_common_shares BIGINT,         -- 已發行普通股數或TDR原發行股數
    private_placement_common_shares BIGINT,   -- 私募普通股(股)
    preferred_shares BIGINT,                  -- 特別股(股)
    accounting_firm VARCHAR(255),               -- 簽證會計師事務所
    accountant_1 VARCHAR(100),                   -- 簽證會計師1
    accountant_2 VARCHAR(100),                   -- 簽證會計師2
    website VARCHAR(255),                     -- 公司網址
    common_stock_dividend_frequency VARCHAR(50), -- 普通股盈餘分派或虧損撥補頻率
    common_stock_dividend_decision_level VARCHAR(50), -- 普通股年度(含第4季或後半年度)現金股息及紅利決議層級
    description TEXT,                         -- 公司簡介
    is_verified BOOLEAN DEFAULT FALSE,        -- 是否已驗證
    sector_id INTEGER REFERENCES Sectors(sector_id), -- 產業ID (外部鍵)
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP, -- 最後更新時間
    CONSTRAINT uq_companies_stock_country UNIQUE (stock_symbol, country_id) 
);
CREATE INDEX idx_companies_sector_id ON Companies(sector_id);
CREATE INDEX idx_companies_country_id ON Companies(country_id);
CREATE INDEX idx_companies_company_name ON Companies(company_name);
CREATE INDEX idx_companies_stock_symbol ON Companies (stock_symbol);


-- Creating Balance_Sheets table 資產負債表
CREATE TABLE Balance_Sheets (
    balance_id SERIAL PRIMARY KEY,
    company_id INTEGER REFERENCES Companies(company_id),
    sector_id INTEGER REFERENCES Sectors(sector_id), -- 產業ID (外部鍵)
    country_id INTEGER REFERENCES Countrys(country_id), -- 國家 (外鍵）
    report_type VARCHAR(20) NOT NULL CHECK (report_type IN ('quarterly', 'annual')), -- 報告類型（季報/年報）
    year INTEGER NOT NULL, -- 年度
    quarter INTEGER CHECK (quarter IN (1, 2, 3, 4) OR quarter IS NULL), -- 季度
    original_currency VARCHAR(3) NOT NULL, -- 原始幣別
    current_assets DECIMAL(20,2), -- 流動資產
    cash_and_equivalents DECIMAL(20,2), -- 現金及約當現金
    accounts_receivable DECIMAL(20,2), -- 應收帳款
    inventory DECIMAL(20,2), -- 存貨
    total_assets DECIMAL(20,2), -- 資產總計
    property_plant_equipment DECIMAL(20,2), -- 不動產、廠房及設備
    intangible_assets DECIMAL(20,2), -- 無形資產
    long_term_investments DECIMAL(20,2), -- 長期投資
    current_liabilities DECIMAL(20,2), -- 流動負債
    accounts_payable DECIMAL(20,2), -- 應付帳款
    short_term_debt DECIMAL(20,2), -- 短期借款
    total_liabilities DECIMAL(20,2), -- 負債總計
    long_term_debt DECIMAL(20,2), -- 長期借款
    shareholders_equity DECIMAL(20,2), -- 股東權益
    common_stock DECIMAL(20,2), -- 普通股股本
    retained_earnings DECIMAL(20,2), -- 保留盈餘
    report_date DATE NOT NULL, -- 報告日期
    CONSTRAINT uq_balance_company_year_quarter UNIQUE (company_id, year, quarter) 
);
CREATE INDEX idx_balance_sheets_secto_country_year_quarter ON Balance_Sheets (sector_id, country_id, year, quarter);



-- Creating Income_Statements table 損益表
CREATE TABLE Income_Statements (
    income_id SERIAL PRIMARY KEY, -- 損益表ID (主鍵)
    company_id INTEGER REFERENCES Companies(company_id), -- 公司ID (外部鍵)
    report_type VARCHAR(20) NOT NULL CHECK (report_type IN ('quarterly', 'accumulated')), -- 報告類型：'quarterly' (單季) 或 'accumulated' (累積)
    year INTEGER NOT NULL, -- 年度
    quarter INTEGER CHECK (quarter IN (1, 2, 3, 4) OR quarter IS NULL), -- 季度：1, 2, 3, 4 (季度報告) 或 NULL (年度報告，如果適用，但通常累積報告會使用 quarter=4)
    original_currency VARCHAR(3) NOT NULL, -- 原始幣別

    -- 損益表主要欄位
    revenue DECIMAL(20,2), -- 營業收入 (Sales Revenue)
    revenue_pct DECIMAL(5,2), -- 營業收入佔營收百分比
    cost_of_revenue DECIMAL(20,2), -- 營業成本 (Cost of Revenue / Cost of Goods Sold)
    cost_of_revenue_pct DECIMAL(5,2), -- 營業成本佔營收百分比
    gross_profit DECIMAL(20,2), -- 營業毛利 (Gross Profit)
    gross_profit_pct DECIMAL(5,2), -- 營業毛利佔營收百分比
    sales_expenses DECIMAL(20,2), -- 銷售費用 (Selling Expenses)
    sales_expenses_pct DECIMAL(5,2), -- 銷售費用佔營收百分比
    administrative_expenses DECIMAL(20,2), -- 管理費用 (Administrative Expenses)
    administrative_expenses_pct DECIMAL(5,2), -- 管理費用佔營收百分比
    research_and_development_expenses DECIMAL(20,2), -- 研發費用 (Research and Development Expenses)
    research_and_development_expenses_pct DECIMAL(5,2), -- 研發費用佔營收百分比
    operating_expenses DECIMAL(20,2), -- 營業費用 (Operating Expenses) - 通常為銷售、管理、研發費用之和
    operating_expenses_pct DECIMAL(5,2), -- 營業費用佔營收百分比
    operating_income DECIMAL(20,2), -- 營業利益 (Operating Income / EBIT)
    operating_income_pct DECIMAL(5,2), -- 營業利益佔營收百分比
    pre_tax_income DECIMAL(20,2), -- 稅前淨利 (Pre-tax Income / EBT)
    pre_tax_income_pct DECIMAL(5,2), -- 稅前淨利佔營收百分比
    net_income DECIMAL(20,2), -- 稅後淨利 (Net Income)
    net_income_pct DECIMAL(5,2), -- 稅後淨利佔營收百分比
    net_income_attributable_to_parent DECIMAL(20,2), -- 母公司業主淨利 (Net Income Attributable to Parent Company Shareholders)
    net_income_attributable_to_parent_pct DECIMAL(5,2), -- 母公司業主淨利佔營收百分比
    basic_eps DECIMAL(10,4), -- 基本每股盈餘 (Basic Earnings Per Share)
    diluted_eps DECIMAL(10,4) -- 稀釋每股盈餘 (Diluted Earnings Per Share)
    
);

-- 索引：提高按產業、國家、年度和季度查詢的效率
CREATE INDEX idx_income_statements_sector_country_year_quarter ON Income_Statements (sector_id, country_id, year, quarter);
-- 索引：提高 某家公司所有年度的某季查詢 以及 某家公司特定年度的特定季度查詢
CREATE INDEX idx_income_statements_company_year_quarter ON Income_Statements (company_id, year, quarter);


-- Creating Cash_Flow_Statements table 現金流量表
CREATE TABLE Cash_Flow_Statements (
    cash_flow_id SERIAL PRIMARY KEY,
    company_id INTEGER REFERENCES Companies(company_id),
    report_type VARCHAR(20) NOT NULL CHECK (report_type IN ('quarterly', 'accumulated')), -- 報告類型（單季/累積）
    year INTEGER NOT NULL, -- 年度
    quarter INTEGER CHECK (quarter IN (1, 2, 3, 4) OR quarter IS NULL), -- 季度
    original_currency VARCHAR(3) NOT NULL, -- 原始幣別
    depreciation DECIMAL(20,2), -- 折舊
    amortization DECIMAL(20,2), -- 攤銷
    operating_cash_flow DECIMAL(20,2), -- 營業活動之現金流量 (營業現金流)
    investing_cash_flow DECIMAL(20,2), -- 投資活動之現金流量 (投資現金流)
    capital_expenditures DECIMAL(20,2), -- 資本支出
    financing_cash_flow DECIMAL(20,2), -- 籌資活動之現金流量 (融資現金流)
    dividends_paid DECIMAL(20,2), -- 股利發放 (現金股利發放)
    free_cash_flow DECIMAL(20,2), -- 自由現金流量
    net_change_in_cash DECIMAL(20,2), -- 現金及約當現金淨變動 (淨現金流)
    
    CONSTRAINT uq_cash_flow_company_year_quarter_type UNIQUE (company_id, year, quarter, report_type) 
);



CREATE TABLE Stock_Analysis (
    analysis_id SERIAL PRIMARY KEY,
    company_id INTEGER REFERENCES Companies(company_id), -- 公司ID
    sector_id INTEGER REFERENCES Sectors(sector_id), -- 產業ID (外部鍵)
    country_id INTEGER REFERENCES Countrys(country_id), -- 國家 (外鍵）
    year INTEGER NOT NULL, -- 年度
    quarter INTEGER CHECK (quarter IN (1, 2, 3, 4) OR quarter IS NULL), -- 季度
    pe_ratio DECIMAL(20,2), -- 本益比
    pe_achieved BOOLEAN, -- 是否達到本益比目標
    pe_rank_above_median BOOLEAN, -- 本益比是否高於產業中位數
    pe_rank_in_sector INTEGER, -- 本益比在產業中的排名
    revenue_growth BOOLEAN, -- 營收是否成長
    revenue_rank_above_median BOOLEAN, -- 營收是否高於產業中位數
    revenue_rank_in_sector INTEGER, -- 營收在產業中的排名
    operating_income_growth BOOLEAN, -- 營業利益是否成長
    operating_income_rank_above_median BOOLEAN, -- 營業利益是否高於產業中位數
    operating_income_rank_in_sector INTEGER, -- 營業利益在產業中的排名
    net_income_growth BOOLEAN, -- 稅後淨利是否成長
    net_income_rank_above_median BOOLEAN, -- 稅後淨利是否高於產業中位數
    net_income_rank_in_sector INTEGER, -- 稅後淨利在產業中的排名
    current_ratio_above1 BOOLEAN, -- 流動比率是否大於1
    longTermBebt_netIncome_ratio_below4 BOOLEAN, -- 長期負債/淨利是否小於4
    shareholders_equity_growth BOOLEAN, -- 股東權益是否成長
    OCF_above_InvestCF BOOLEAN, -- 營業現金流是否大於投資現金流
    CONSTRAINT uq_stock_analysis_company_year_quarter UNIQUE (company_id, year, quarter) 
);
CREATE INDEX idx_Stock_Analysis_sector_country_year_quarter ON Stock_Analysis (sector_id, country_id, year, quarter);


CREATE TABLE Sector_Analysis (
    analysis_id SERIAL PRIMARY KEY,
    sector_id INTEGER REFERENCES Sectors(sector_id), -- 產業ID (外鍵)
    country_id INTEGER REFERENCES Countrys(country_id), -- 國家 (外鍵）
    year INTEGER NOT NULL, -- 年度
    quarter INTEGER CHECK (quarter IN (1, 2, 3, 4) OR quarter IS NULL), -- 季度
    pe_avg DECIMAL(20,2), -- 產業平均本益比
    pe_median DECIMAL(20,2), -- 產業中位數本益比
    revenue_avg DECIMAL(20,2), -- 產業平均營收
    revenue_median DECIMAL(20,2), -- 產業中位數營收
    operating_income_avg DECIMAL(20,2), -- 產業平均營業利益
    operating_income_median DECIMAL(20,2), -- 產業中位數營業利益
    net_income_avg DECIMAL(20,2), -- 產業平均稅後淨利
    net_income_median DECIMAL(20,2), -- 產業中位數稅後淨利
    CONSTRAINT uq_sector_analysis_sector_year_quarter UNIQUE (sector_id, year, quarter) 
);
CREATE INDEX idx_Sector_Analysis_sector_country_year_quarter ON Sector_Analysis (sector_id, country_id, year, quarter);

CREATE TABLE Financial_Ratios (
    ratio_id SERIAL PRIMARY KEY,
    company_id INTEGER REFERENCES Companies(company_id), -- 公司ID
    sector_id INTEGER REFERENCES Sectors(sector_id), -- 產業ID (外部鍵)
    country_id INTEGER REFERENCES Countrys(country_id), -- 國家 (外鍵）
    year INTEGER NOT NULL, -- 年度
    quarter INTEGER CHECK (quarter IN (1, 2, 3, 4) OR quarter IS NULL), -- 季度
    
    -- 獲利能力比率
    gross_margin DECIMAL(5,2), -- 毛利率
    operating_margin DECIMAL(5,2), -- 營業利益率
    net_margin DECIMAL(5,2), -- 淨利率
    
    -- 市場價值比率
    pe_ratio DECIMAL(5,2), -- 本益比
    
    report_date DATE , -- 報告日期
    CONSTRAINT uq_financial_ratios_company_year_quarter UNIQUE (company_id, year, quarter)
);

CREATE INDEX idx_financial_ratios_sector_country_year_quarter ON Financial_Ratios (sector_id, country_id, year, quarter);