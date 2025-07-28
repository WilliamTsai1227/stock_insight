# Stock Insight: 後端與數據工程面試作品集

**網站網址**: [Stock Insight](https://stockinsight-ai.com/)

## 專案介紹
Stock Insight 是一個整合股市新聞、AI 洞察分析與個股數據的平台。本專案旨在展示我在後端開發與數據工程領域的綜合能力，涵蓋了從大規模數據採集、ETL 流程、高效數據庫設計、分散式系統建置到自動化部署與安全防護的完整解決方案。

## 核心功能
- **定時新聞更新與查詢**：每日自動化更新新聞，支援根據關鍵字與時間區間進行查詢。
- **AI 洞察**：AI 根據新聞內容生成深度洞察，包括重點新聞摘要、情緒分析、潛力股票推薦及產業趨勢分析。
- **個股頁面**：提供個股詳盡資料，包含十年財報（季報/年報/累計）、財報指標在同產業中的排名、個股相關新聞及 AI 洞察。
- **進階搜尋**：允許使用者根據財報欄位、年份、報表類型及特定產業，搜尋並對產業內的個股進行排名。

## 技術棧

### 後端與數據工程
- **雲端服務**：AWS Lambda, AWS Step Functions, AWS ECS, AWS SQS, AWS S3, AWS PostgreSQL (RDS), AWS EC2, AWS Bedrock
- **數據庫**：PostgreSQL (關係型), MongoDB (NoSQL)
- **容器化**：Docker Swarm
- **網路與安全**：AWS Application Load Balancer (ALB), AWS Route53, AWS WAF, AWS Certificate Manager (ACM)
- **後端框架**：Python FastAPI
- **語言**：Python

### 前端
- **技術**：HTML, CSS, JavaScript (Chart.js)

## 架構概覽
本專案採用現代微服務與分散式架構，旨在提供高可用性、可擴展性與強大的安全性。

## 關鍵技術實踐

### 新聞與 AI 洞察管道

#### 新聞爬蟲
- 利用 Python 腳本，部署於 AWS Lambda。
- 通過 AWS EventBridge 設定定時觸發，每日多次執行爬蟲任務。
- 抓取到的新聞數據更新至 MongoDB。

#### AI 洞察處理 (ETL)
- Python 腳本運行於 AWS Lambda。
- **提取 (Extract)**：批量從 MongoDB 讀取新聞數據，並暫存至 AWS S3。
- **轉換 (Transform)**：AWS Lambda 從 S3 提取數據進行整理。
- **分析 (Analyze)**：整理後的數據餵給 AWS Bedrock 進行 AI 分析。
- **結果檢查**：另一個 AWS Lambda Function 會對 AI 生成的結果進行檢查，確保數據品質。
- **載入 (Load)**：分析結果存回 MongoDB。

### 財務數據管理
- **數據規模**：支援台灣 1906 家上市櫃公司，涵蓋十年現金流量表、資產負債表、損益表，總計約 21 萬筆數據。
- **數據庫設計**：
  - 使用 AWS PostgreSQL (RDS) 建立高效能關聯式資料庫。
  - 精心設計並建立索引，確保快速查詢與排名計算。

#### 分散式財報爬蟲
- 為大幅縮短 21 萬筆數據的爬取時間，實作分散式爬蟲系統。
- 利用 AWS ECS 部署 6 個爬蟲實例，搭配 AWS SQS 作為任務佇列。
- ECS 實例同時從 SQS 獲取任務並執行爬取。
- 爬取到的原始數據 (raw data) 存入 AWS S3。
- 後續 ETL 流程從 S3 提取、清洗、轉換數據，並載入至 PostgreSQL，確保所有財報數據與公司基本資料的正確關聯，以支援個股頁面的完整查詢。

### 財報排名與進階查詢
- 利用 PostgreSQL 強大的 SQL 排序與聚合功能，實現複雜的財報欄位排名與進階查詢。

### 個股頁面可視化
- 前端利用 Chart.js 庫，將十年財報數據以直觀的折線圖形式呈現，便於使用者分析數據變化趨勢。

## 基礎設施部署與安全

### 後端系統部署
- 採用 Docker Swarm 進行容器編排與部署。
- 在 AWS EC2 上架設 1 個 Manager 節點與 3 個 Worker 節點。
- 實現服務的高可用性、負載分流，並確保在版本更新或回溯時服務不中斷。Manager 節點負責監控 Worker 節點的健康狀況。

### 網路與安全防護

#### 流量負載平衡
- 使用 AWS Application Load Balancer (ALB) 進行流量負載均衡，將請求導向後端的 EC2 群組。

#### DNS 服務
- AWS Route53 作為 DNS Server，將域名解析並導向 ALB。

#### 安全連線 (HTTPS)
- 透過 AWS Certificate Manager (ACM) 申請並管理 SSL 憑證，提供安全的 HTTPS 連線。所有 HTTP 請求會自動重導向 HTTPS。

#### Web 應用防火牆 (WAF)
- 在 ALB 上部署 AWS WAF，提供應用層級的安全防護，有效阻擋常見的網路攻擊：
  - **Core Rule Set**：防範 OWASP Top 10 漏洞，如 SQL Injection, Cross-Site Scripting (XSS), Cross-Site Request Forgery (CSRF)。
  - **AWS IP Reputation List**：阻擋來自已知惡意 IP 地址的流量。
  - **IP Rate Limit**：限制單一 IP 每分鐘可發送的請求數量，防止 DDoS 攻擊。
- 同時防範不符合 HTTP 協議規範的請求、路徑遍歷 (Path Traversal)、遠端/本地文件包含 (RFI/LFI) 等攻擊。

### 數據庫配置
- **關聯式數據庫**：AWS PostgreSQL (RDS) 專用於儲存個股基本資訊及所有財報數據。
- **非關聯式數據庫**：MongoDB 專用於儲存新聞內容及 AI 洞察結果。
- **後端伺服器**：EC2 上的後端應用程式負責從 PostgreSQL 和 MongoDB 獲取數據並提供服務。

## API 設計
- 遵循 RESTful API 設計原則，提供清晰、標準化的介面供前端應用程式調用。