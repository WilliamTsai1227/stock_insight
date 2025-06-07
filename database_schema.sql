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


-- Creating Balance_Sheets table 資產負債表
CREATE TABLE Balance_Sheets (
    balance_id SERIAL PRIMARY KEY,
    company_id INTEGER REFERENCES Companies(company_id),
    sector_id INTEGER REFERENCES Sectors(sector_id), -- 產業ID (外部鍵)
    country_id INTEGER REFERENCES Countrys(country_id), -- 國家 (外鍵）
    report_type VARCHAR(20) NOT NULL CHECK (report_type IN ('quarterly', 'annual')),
    year INTEGER NOT NULL,
    quarter INTEGER CHECK (quarter IN (1, 2, 3, 4) OR quarter IS NULL),
    original_currency VARCHAR(3) NOT NULL, -- e.g., 'TWD', 'USD', 'JPY'
    current_assets DECIMAL(20,2),
    cash_and_equivalents DECIMAL(20,2),
    accounts_receivable DECIMAL(20,2),
    inventory DECIMAL(20,2),
    total_assets DECIMAL(20,2),
    property_plant_equipment DECIMAL(20,2),
    intangible_assets DECIMAL(20,2),
    long_term_investments DECIMAL(20,2),
    current_liabilities DECIMAL(20,2),
    accounts_payable DECIMAL(20,2),
    short_term_debt DECIMAL(20,2),
    total_liabilities DECIMAL(20,2),
    long_term_debt DECIMAL(20,2),
    shareholders_equity DECIMAL(20,2),
    common_stock DECIMAL(20,2),
    retained_earnings DECIMAL(20,2),
    shares_outstanding BIGINT,
    report_date DATE NOT NULL,
    CONSTRAINT uq_balance_company_year_quarter UNIQUE (company_id, year, quarter) 
);
CREATE INDEX idx_balance_sheets_secto_country_year_quarter ON Balance_Sheets (sector_id, country_id, year, quarter);

-- Creating Income_Statements table 損益表
CREATE TABLE Income_Statements (
    income_id SERIAL PRIMARY KEY,
    company_id INTEGER REFERENCES Companies(company_id),
    sector_id INTEGER REFERENCES Sectors(sector_id), -- 產業ID (外部鍵)
    country_id INTEGER REFERENCES Countrys(country_id), -- 國家 (外鍵）
    report_type VARCHAR(20) NOT NULL CHECK (report_type IN ('quarterly', 'annual')),
    year INTEGER NOT NULL,
    quarter INTEGER CHECK (quarter IN (1, 2, 3, 4) OR quarter IS NULL),
    eps DECIMAL(10,2), -- Earnings Per Share
    pe_ratio DECIMAL(10,2), -- Price-to-Earnings Ratio
    original_currency VARCHAR(3) NOT NULL, -- e.g., 'TWD', 'USD', 'JPY'
    revenue DECIMAL(20,2),
    gross_profit DECIMAL(20,2),
    operating_income DECIMAL(20,2),
    operating_expenses DECIMAL(20,2),
    pre_tax_income DECIMAL(20,2),
    interest_expense DECIMAL(20,2),
    net_income DECIMAL(20,2),
    ebitda DECIMAL(20,2),
    total_other_income DECIMAL(20,2),
    total_other_expenditure DECIMAL(20,2),
    cost_of_revenue DECIMAL(20,2),
    report_date DATE NOT NULL,
    CONSTRAINT uq_income_company_year_quarter UNIQUE (company_id, year, quarter) 
);
CREATE INDEX idx_income_statements_sector_country_year_quarter ON Income_Statements (sector_id, country_id, year, quarter);

-- Creating Cash_Flow_Statements table 現金流量表
CREATE TABLE Cash_Flow_Statements (
    cash_flow_id SERIAL PRIMARY KEY,
    company_id INTEGER REFERENCES Companies(company_id),
    sector_id INTEGER REFERENCES Sectors(sector_id), -- 產業ID (外部鍵)
    country_id INTEGER REFERENCES Countrys(country_id), -- 國家 (外鍵）
    report_type VARCHAR(20) NOT NULL CHECK (report_type IN ('quarterly', 'annual')),
    year INTEGER NOT NULL,
    quarter INTEGER CHECK (quarter IN (1, 2, 3, 4) OR quarter IS NULL),
    original_currency VARCHAR(3) NOT NULL, -- e.g., 'TWD', 'USD', 'JPY'
    operating_cash_flow DECIMAL(20,2),
    investing_cash_flow DECIMAL(20,2), 
    capital_expenditures DECIMAL(20,2),
    financing_cash_flow DECIMAL(20,2),
    stock_issuance_repurchase DECIMAL(20,2),
    debt_issuance_repayment DECIMAL(20,2),
    dividends_paid DECIMAL(20,2),
    free_cash_flow DECIMAL(20,2),
    net_change_in_cash DECIMAL(20,2),
    report_date DATE NOT NULL,
    CONSTRAINT uq_cash_flow_company_year_quarter UNIQUE (company_id, year, quarter) 
);
CREATE INDEX idx_cash_flow_statements_sector_country_year_quarter ON Cash_Flow_Statements (sector_id, country_id, year, quarter);


CREATE TABLE Stock_Analysis (
    analysis_id SERIAL PRIMARY KEY,
    company_id INTEGER REFERENCES Companies(company_id),
    sector_id INTEGER REFERENCES Sectors(sector_id), -- 產業ID (外部鍵)
    country_id INTEGER REFERENCES Countrys(country_id), -- 國家 (外鍵）
    year INTEGER NOT NULL,
    quarter INTEGER CHECK (quarter IN (1, 2, 3, 4) OR quarter IS NULL),
    pe_ratio DECIMAL(20,2),
    pe_achieved BOOLEAN,
    pe_rank_above_median BOOLEAN,
    pe_rank_in_sector INTEGER,
    revenue_growth BOOLEAN,
    revenue_rank_above_median BOOLEAN,
    revenue_rank_in_sector INTEGER,
    operating_income_growth BOOLEAN,
    operating_income_rank_above_median BOOLEAN,
    operating_income_rank_in_sector INTEGER,
    net_income_growth BOOLEAN,
    net_income_rank_above_median BOOLEAN,
    net_income_rank_in_sector INTEGER,
    current_ratio_above1 BOOLEAN,                   -- 流動資產是否大於流動負債
    longTermBebt_netIncome_ratio_below4 BOOLEAN,    -- 長期負債／淨利是否 <4
    shareholders_equity_growth BOOLEAN,             -- 股東權益有無成長
    OCF_above_InvestCF BOOLEAN,                     -- 營業現金流 > 投資現金流      
    CONSTRAINT uq_stock_analysis_company_year_quarter UNIQUE (company_id, year, quarter) 
);
CREATE INDEX idx_Stock_Analysis_sector_country_year_quarter ON Stock_Analysis (sector_id, country_id, year, quarter);


CREATE TABLE Sector_Analysis (
    analysis_id SERIAL PRIMARY KEY,
    sector_id INTEGER REFERENCES Sectors(sector_id), -- 產業ID (外鍵)
    country_id INTEGER REFERENCES Countrys(country_id), -- 國家 (外鍵）
    year INTEGER NOT NULL,
    quarter INTEGER CHECK (quarter IN (1, 2, 3, 4) OR quarter IS NULL),
    pe_avg DECIMAL(20,2),
    pe_median DECIMAL(20,2),
    revenue_avg DECIMAL(20,2),
    revenue_median DECIMAL(20,2),
    operating_income_avg DECIMAL(20,2),
    operating_income_median DECIMAL(20,2),
    net_income_avg DECIMAL(20,2),
    net_income_median DECIMAL(20,2),
    CONSTRAINT uq_sector_analysis_sector_year_quarter UNIQUE (sector_id, year, quarter) 
);
CREATE INDEX idx_Sector_Analysis_sector_country_year_quarter ON Sector_Analysis (sector_id, country_id, year, quarter);