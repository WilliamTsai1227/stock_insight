let myChart = null; // 全域唯一 Chart 實例
let loadingIndicator = document.getElementById("loading-indicator");
let stockSymbol = "";
let country = "tw";

// 定義財報欄位的中文名稱、顯示順序和固定顏色
const REPORT_FIELD_MAP = {
    cash_flow: {
        title: '現金流量表',
        fields: [
            { key: 'operating_cash_flow', label: '營業活動之現金流量 (營業現金流)', color: '#4CAF50' }, // Green
            { key: 'investing_cash_flow', label: '投資活動之現金流量 (投資現金流)', color: '#FFC107' }, // Amber
            { key: 'financing_cash_flow', label: '籌資活動之現金流量 (融資現金流)', color: '#2196F3' }, // Blue
            { key: 'free_cash_flow', label: '自由現金流量', color: '#9C27B0' }, // Purple
            { key: 'net_change_in_cash', label: '現金及約當現金淨變動 (淨現金流)', color: '#FF5722' }, // Deep Orange
            { key: 'depreciation', label: '折舊', color: '#607D8B' }, // Blue Grey
            { key: 'amortization', label: '攤銷', color: '#795548' }, // Brown
            { key: 'capital_expenditures', label: '資本支出', color: '#F44336' }, // Red
            { key: 'dividends_paid', label: '股利發放 (現金股利發放)', color: '#E91E63' }  // Pink
        ]
    },
    income_statements: {
        title: '損益表',
        fields: [
            { key: 'revenue', label: '營業收入', color: '#4CAF50' },
            { key: 'gross_profit', label: '營業毛利', color: '#FFC107' },
            { key: 'operating_income', label: '營業利益', color: '#2196F3' },
            { key: 'pre_tax_income', label: '稅前淨利', color: '#9C27B0' },
            { key: 'net_income', label: '稅後淨利', color: '#FF5722' },
            { key: 'net_income_attributable_to_parent', label: '母公司業主淨利', color: '#607D8B' },
            { key: 'basic_eps', label: '基本每股盈餘 (EPS)', color: '#795548' },
            { key: 'diluted_eps', label: '稀釋每股盈餘', color: '#F44336' },
            { key: 'revenue_pct', label: '營業收入佔營收百分比', color: '#8BC34A' }, // Light Green
            { key: 'cost_of_revenue', label: '營業成本', color: '#FFEB3B' }, // Yellow
            { key: 'cost_of_revenue_pct', label: '營業成本佔營收百分比', color: '#BBF0F3' }, // Cyan Light
            { key: 'gross_profit_pct', label: '營業毛利佔營收百分比', color: '#E1BEE7' }, // Purple Light
            { key: 'sales_expenses', label: '銷售費用', color: '#FFCDD2' }, // Red Light
            { key: 'sales_expenses_pct', label: '銷售費用佔營收百分比', color: '#F8BBD0' }, // Pink Light
            { key: 'administrative_expenses', label: '管理費用', color: '#B2DFDB' }, // Teal Light
            { key: 'administrative_expenses_pct', label: '管理費用佔營收百分比', color: '#D1C4E9' }, // Deep Purple Light
            { key: 'research_and_development_expenses', label: '研發費用', color: '#C5CAE9' }, // Indigo Light
            { key: 'research_and_development_expenses_pct', label: '研發費用佔營收百分比', color: '#BBDEFB' }, // Blue Light
            { key: 'operating_expenses', label: '營業費用', color: '#B3E5FC' }, // Light Blue Light
            { key: 'operating_expenses_pct', label: '營業費用佔營收百分比', color: '#C8E6C9' }, // Green Light
            { key: 'operating_income_pct', label: '營業利益佔營收百分比', color: '#FFF9C4' }, // Yellow Light
            { key: 'pre_tax_income_pct', label: '稅前淨利佔營收百分比', color: '#FCE4EC' }, // Pink Light
            { key: 'net_income_pct', label: '稅後淨利佔營收百分比', color: '#FFECB3' }, // Amber Light
            { key: 'net_income_attributable_to_parent_pct', label: '母公司業主淨利佔營收百分比', color: '#CFD8DC' } // Blue Grey Light
        ]
    },
    balance_sheets: {
        title: '資產負債表',
        fields: [
            { key: 'total_assets', label: '資產總計', color: '#4CAF50' },
            { key: 'current_assets', label: '流動資產', color: '#FFC107' },
            { key: 'cash_and_equivalents', label: '現金及約當現金', color: '#2196F3' },
            { key: 'accounts_receivable', label: '應收帳款', color: '#9C27B0' },
            { key: 'inventory', label: '存貨', color: '#FF5722' },
            { key: 'property_plant_equipment', label: '不動產、廠房及設備', color: '#607D8B' },
            { key: 'intangible_assets', label: '無形資產', color: '#795548' },
            { key: 'long_term_investments', label: '長期投資', color: '#F44336' },
            { key: 'total_liabilities', label: '負債總計', color: '#E91E63' },
            { key: 'current_liabilities', label: '流動負債', color: '#00BCD4' }, // Cyan
            { key: 'accounts_payable', label: '應付帳款', color: '#CDDC39' }, // Lime
            { key: 'short_term_debt', label: '短期借款', color: '#FF9800' }, // Orange
            { key: 'long_term_debt', label: '長期借款', color: '#673AB7' }, // Deep Purple
            { key: 'shareholders_equity', label: '股東權益', color: '#009688' }, // Teal
            { key: 'common_stock', label: '普通股股本', color: '#A1887F' }, // Brown Light
            { key: 'retained_earnings', label: '保留盈餘', color: '#81C784' }, // Green Light
            { key: 'report_date', label: '報告日期', color: '#B0BEC5' } // Blue Grey Light
        ]
    }
};

// 初始化搜尋參數
function initSearchParamsFromURL() {
    const pathParts = window.location.pathname.split('/');
    stockSymbol = pathParts[2] || ""; // /stock/股票代碼/國家
    country = pathParts[3] || "tw";
}

// 設定搜尋框的值
function setSearchBarValue() {
    const searchBar = document.querySelector('.search-bar');
    if (searchBar) {
        searchBar.value = stockSymbol;
    }
}

// 更新 URL 參數
function updateURLParams() {
    const newUrl = `/stock/${stockSymbol}/${country}`;
    history.replaceState({}, '', newUrl);
}

// 載入股票資訊
async function loadStockInfo() {
    try {
        // 清除前一次的內容
        document.getElementById('stock-header').textContent = '';
        document.getElementById('stock-info').textContent = '';
        
        // 顯示載入中
        document.getElementById('loading-indicator').style.display = 'flex';
        
        const response = await fetch(`http://localhost:8000/api/stock_info?stock_symbol=${stockSymbol}&country=${country}`);
        
        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.detail || '載入股票時發生錯誤，請稍後再試。');
        }

        const responseData = await response.json();
        if (!responseData.data) {
            throw new Error('回傳資料格式不正確');
        }
        
        // 隱藏載入中
        document.getElementById('loading-indicator').style.display = 'none';
        
        // 顯示股票資訊
        displayStockInfo(responseData.data);
    } catch (error) {
        // 隱藏載入中
        document.getElementById('loading-indicator').style.display = 'none';
        
        // 清除所有內容
        document.getElementById('stock-header').textContent = '';
        document.getElementById('stock-info').textContent = '';
        
        // 顯示錯誤訊息
        displayError(error.message);
    }
}

// 顯示股票資訊
function displayStockInfo(data) {
    if (!data) {
        displayError("找不到股票資料");
        return;
    }

    // 顯示標題
    const stockHeader = document.getElementById('stock-header');
    stockHeader.textContent = ""; // 先清空
    const h1 = document.createElement("h1");
    h1.className = "stock-title";
    h1.textContent = `${data.company_name || '-'} (${data.stock_symbol || '-'}.${country})`;
    stockHeader.appendChild(h1);

    // 顯示詳細資訊
    const stockInfo = document.getElementById('stock-info');
    stockInfo.textContent = ""; // 先清空
    const table = document.createElement("table");
    table.className = "stock-info-table";

    // 建立每一行
    function addRow(th1, td1, th2, td2) {
        const tr = document.createElement("tr");
        const thEl1 = document.createElement("th");
        thEl1.textContent = th1;
        tr.appendChild(thEl1);
        const tdEl1 = document.createElement("td");
        tdEl1.textContent = td1;
        tr.appendChild(tdEl1);
        const thEl2 = document.createElement("th");
        thEl2.textContent = th2;
        tr.appendChild(thEl2);
        const tdEl2 = document.createElement("td");
        tdEl2.textContent = td2;
        tr.appendChild(tdEl2);
        table.appendChild(tr);
    }
    // colspan 3 欄位
    function addRowColspan(th, td) {
        const tr = document.createElement("tr");
        const thEl = document.createElement("th");
        thEl.textContent = th;
        tr.appendChild(thEl);
        const tdEl = document.createElement("td");
        tdEl.textContent = td;
        tdEl.colSpan = 3;
        tr.appendChild(tdEl);
        table.appendChild(tr);
    }
    // 網址欄位
    function addRowWebsite(th, url) {
        const tr = document.createElement("tr");
        const thEl = document.createElement("th");
        thEl.textContent = th;
        tr.appendChild(thEl);
        const tdEl = document.createElement("td");
        tdEl.colSpan = 3;
        if (url) {
            const a = document.createElement("a");
            a.href = url;
            a.target = "_blank";
            a.rel = "noopener noreferrer";
            a.textContent = url;
            tdEl.appendChild(a);
        } else {
            tdEl.textContent = "-";
        }
        tr.appendChild(tdEl);
        table.appendChild(tr);
    }
    // 依序加入所有欄位
    addRow("公司簡稱", data.abbreviation || "-", "成立日期", data.founding_date || "-");
    addRow("上市日期", data.listed_date || "-", "上櫃日期", data.otc_listed_date || "-");
    addRow("市場", data.market || "-", "產業", data.sector_name || "-");
    addRowColspan("公司地址", data.address || "-");
    addRow("董事長", data.chairman || "-", "總經理", data.general_manager || "-");
    addRow("發言人", data.spokesperson || "-", "發言人職稱", data.spokesperson_title || "-");
    addRow("已發行普通股數", data.outstanding_common_shares?.toLocaleString() || "-", "私募普通股", data.private_placement_common_shares?.toLocaleString() || "-");
    addRow("特別股", data.preferred_shares?.toLocaleString() || "-", "簽證會計師事務所", data.accounting_firm || "-");
    addRow("簽證會計師1", data.accountant_1 || "-", "簽證會計師2", data.accountant_2 || "-");
    addRowWebsite("公司網址", data.website);
    addRow("普通股盈餘分派頻率", data.common_stock_dividend_frequency || "-", "現金股息決議層級", data.common_stock_dividend_decision_level || "-");
    addRowColspan("公司簡介", data.description || "-");
    stockInfo.appendChild(table);
}

// 顯示錯誤訊息
function displayError(message) {
    const stockInfo = document.getElementById('stock-info');
    const errorMessage = document.createElement('div');
    errorMessage.className = 'error-message';
    
    // 如果是 404 錯誤，只顯示找不到股票的部分
    if (message.includes("找不到股票代碼")) {
        const match = message.match(/找不到股票代碼.*?的資料/);
        if (match) {
            errorMessage.textContent = match[0];
        } else {
            errorMessage.textContent = message;
        }
    } else {
        errorMessage.textContent = message;
    }
    
    stockInfo.appendChild(errorMessage);
}

// 包裝財報查詢/繪圖為 function
async function loadFinancialReport(stockSymbol, country) {
    const API_BASE_URL = "http://localhost:8000/api/financial_report";
    let currentFinancialData = [];
    let currentOriginalCurrency = '';

    // 內部 function: 取得目前選擇的 reportType/reportPeriod
    function getReportType() {
        return document.getElementById('reportType').value;
    }
    function getReportPeriod() {
        return document.getElementById('reportPeriod').value;
    }



    // 內部 function: 畫圖
    function drawChartBasedOnSelection() {
        if (currentFinancialData.length === 0) {
            if (myChart) {
                myChart.destroy();
                myChart = null;
            }
            return;
        }

        const reportType = document.getElementById('reportType').value;
        const labels = currentFinancialData.map(d => `${d.year} Q${d.quarter}`);
        const allFields = REPORT_FIELD_MAP[reportType].fields;

        // 取得所有被勾選的指標鍵值
        const selectedMetricKeys = Array.from(document.querySelectorAll('input[name="chartMetric"]:checked'))
                                        .map(checkbox => checkbox.value);

        // 構建 Chart.js 的 datasets，只包含被勾選的項目
        const datasets = allFields.filter(field => {
            const isChartable = !field.key.includes('_pct') && field.key !== 'report_date';
            const isSelected = selectedMetricKeys.includes(field.key);
            return isChartable && isSelected;
        }).map(field => {
            return {
                label: field.label,
                data: currentFinancialData.map(d => d[field.key] !== null ? d[field.key] : NaN),
                borderColor: field.color,
                backgroundColor: field.color.replace('rgb', 'rgba').replace(')', ', 0.2)'),
                fill: false,
                tension: 0.1
            };
        });

        // 獲取所有「可繪製圖表」的指標，用於圖例顯示 (無論是否勾選)
        const legendDatasets = allFields.filter(field => {
            return !field.key.includes('_pct') && field.key !== 'report_date';
        }).map(field => ({
            key: field.key, // 新增 key 屬性以便在 onClick 中查找
            label: field.label,
            borderColor: field.color,
            backgroundColor: field.color.replace('rgb', 'rgba').replace(')', ', 0.2)')
        }));

        const ctx = document.getElementById('financialChart').getContext('2d');

        // 定義圖例的點擊事件處理器
        const legendOnClickHandler = function(e, legendItem, legend) {
            const datasetLabel = legendItem.text;
            const fieldKey = legendDatasets.find(d => d.label === datasetLabel)?.key;

            if (fieldKey) {
                const checkbox = document.querySelector(`input[name="chartMetric"][value="${fieldKey}"]`);
                if (checkbox) {
                    checkbox.checked = !checkbox.checked; // 反轉勾選狀態
                    // 觸發 change 事件，確保勾選框視覺更新並重新繪圖
                    checkbox.dispatchEvent(new Event('change')); 
                }
            }
        };

        // 定義圖例標籤的生成器
        const legendGenerateLabels = function(chart) {
            return legendDatasets.map((dataset, i) => {
                const hidden = !selectedMetricKeys.includes(dataset.key);
                
                return {
                    text: dataset.label,
                    fillStyle: dataset.backgroundColor,
                    strokeStyle: dataset.borderColor,
                    lineWidth: 1,
                    hidden: hidden,
                    datasetIndex: i
                };
            });
        };

        if (myChart) {
            // 如果圖表已存在，更新其數據和選項
            myChart.data.labels = labels;
            myChart.data.datasets = datasets; // 直接替換數據集為選中的
            myChart.options.plugins.title.text = `${REPORT_FIELD_MAP[reportType].title} - 指標趨勢 (${currentOriginalCurrency} 千元)`;
            myChart.options.animation.duration = 1000;
            // **核心修正：每次更新時，確保重新設定 generateLabels 函式**
            myChart.options.plugins.legend.labels.generateLabels = legendGenerateLabels;
            myChart.options.plugins.legend.labels.onClick = legendOnClickHandler; // 確保點擊處理器也更新
            myChart.update();
        } else {
            // 否則，創建一個新的圖表實例
            myChart = new Chart(ctx, {
                type: 'line',
                data: {
                    labels: labels,
                    datasets: datasets
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    animation: {
                        duration: 1000 // 1 秒動畫
                    },
                    scales: {
                        x: {
                            title: {
                                display: true,
                                text: '時間 (年/季度)'
                            }
                        },
                        y: {
                            title: {
                                display: true,
                                text: `金額 (${currentOriginalCurrency} 千元)`
                            },
                            beginAtZero: false // 根據數據調整起始點
                        }
                    },
                    plugins: {
                        tooltip: {
                            callbacks: {
                                label: function(context) {
                                    let label = context.dataset.label || '';
                                    if (label) {
                                        label += ': ';
                                    }
                                    if (context.parsed.y !== null && !isNaN(context.parsed.y)) {
                                        // 這裡假設後端提供的百分比數據就是 50 代表 50%
                                        if (context.dataset.label.includes('百分比')) { // 簡單判斷是否為百分比
                                            label += `${context.parsed.y.toFixed(2)}%`;
                                        } else {
                                            label += new Intl.NumberFormat('zh-TW', { style: 'decimal', minimumFractionDigits: 0, maximumFractionDigits: 0 }).format(context.parsed.y);
                                        }
                                    } else {
                                        label += 'N/A';
                                    }
                                    return label;
                                }
                            }
                        },
                        title: {
                            display: true,
                            text: `${REPORT_FIELD_MAP[reportType].title} - 指標趨勢 (${currentOriginalCurrency} 千元)`,
                            font: {
                                size: 18
                            }
                        },
                        legend: {
                            display: true,
                            position: 'top',
                            labels: {
                                generateLabels: legendGenerateLabels, // 使用定義好的生成器
                                onClick: legendOnClickHandler // 使用定義好的點擊處理器
                            }
                        }
                    }
                }
            });
        }
    }

    // 內部 function: 更新勾選框
    function updateChartOptions() {
        const reportType = getReportType();
        const checkboxContainer = document.getElementById('checkboxContainer');
        while (checkboxContainer.firstChild) {
            checkboxContainer.removeChild(checkboxContainer.firstChild);
        }
        const fields = REPORT_FIELD_MAP[reportType].fields;
        const chartableFields = fields.filter(field => {
            return !field.key.includes('_pct') && field.key !== 'report_date';
        });
        
        // 每次更新選項時，重新生成勾選框並綁定事件
        chartableFields.forEach(field => {
            const label = document.createElement('label');
            const checkbox = document.createElement('input');
            checkbox.type = 'checkbox';
            checkbox.value = field.key;
            checkbox.checked = true; // 預設全部勾選
            checkbox.name = 'chartMetric';
            // 點擊勾選框時直接更新圖表
            checkbox.onchange = drawChartBasedOnSelection; 
            
            label.appendChild(checkbox);
            label.appendChild(document.createTextNode(field.label));
            checkboxContainer.appendChild(label);
        });
    }

    // 內部 function: 建表
    function createTable(financialData, reportType, originalCurrency) {
        const tableContainer = document.getElementById('financialDataTable');
        const tableTitle = document.getElementById('tableTitle');
        const reportInfo = REPORT_FIELD_MAP[reportType];
        tableTitle.textContent = `${reportInfo.title} | 原始幣別: ${originalCurrency} (單位: 千元)`;
        while (tableContainer.firstChild) {
            tableContainer.removeChild(tableContainer.firstChild);
        }
        const table = document.createElement('table');
        const thead = document.createElement('thead');
        const tbody = document.createElement('tbody');
        const headerRow = document.createElement('tr');
        headerRow.appendChild(createTextElement('th', '科目 / 時間'));
        financialData.forEach(data => {
            headerRow.appendChild(createTextElement('th', `${data.year} Q${data.quarter}`));
        });
        thead.appendChild(headerRow);
        table.appendChild(thead);
        reportInfo.fields.forEach(field => {
            const row = document.createElement('tr');
            row.appendChild(createTextElement('td', field.label));
            financialData.forEach(data => {
                const cell = document.createElement('td');
                let value = data[field.key];
                if (value === null || value === undefined) {
                    cell.textContent = '-';
                } else if (field.key.includes('_pct')) {
                    // 百分比欄位：直接顯示後端傳來的數值並加上 '%'
                    // 假設後端已經是實際百分比數值 (例如 50 代表 50%)
                    cell.textContent = `${value.toFixed(2)}%`; 
                } else if (field.key.includes('eps')) {
                    // EPS 欄位，保留小數點後兩位
                    cell.textContent = value.toFixed(2);
                } else if (field.key === 'report_date') {
                    // 報告日期欄位，顯示為日期格式
                    cell.textContent = new Date(value).toLocaleDateString('zh-TW'); // 確保日期格式化
                } else {
                    // 其他數值欄位，格式化為千位分隔，不帶小數
                    cell.textContent = new Intl.NumberFormat('zh-TW', { style: 'decimal', minimumFractionDigits: 0, maximumFractionDigits: 0 }).format(value);
                }
                row.appendChild(cell);
            });
            tbody.appendChild(row);
        });
        table.appendChild(tbody);
        tableContainer.appendChild(table);
    }

    // 內部 function: 輔助
    function createTextElement(tag, textContent) {
        const element = document.createElement(tag);
        element.textContent = textContent;
        return element;
    }

    // 內部 function: 處理 reportType 變更
    // 這個函式會處理下拉選單的 disabled 狀態，並觸發數據載入和圖表更新
    function handleReportTypeChange() {
        const reportType = getReportType();
        const reportPeriodSelect = document.getElementById('reportPeriod');
        if (reportType === 'cash_flow') {
            reportPeriodSelect.value = 'accumulated'; // 強制設為累計
            reportPeriodSelect.options[0].disabled = false; // 累計可選
            reportPeriodSelect.options[1].disabled = true;  // 季報禁用
        } else {
            reportPeriodSelect.options[0].disabled = false;
            reportPeriodSelect.options[1].disabled = false;
        }
        updateChartOptions(); // 更新勾選框，因財報類型不同指標也不同
        fetchAndDrawChartAndTable(); // 重新獲取數據並繪圖/表
    }

    // 內部 function: 查詢並畫圖/表
    // 這個函式負責向後端請求數據，並在獲取後調用繪圖和建表函式
    async function fetchAndDrawChartAndTable() {
        const reportType = getReportType();
        const reportPeriod = getReportPeriod();
        const loadingDiv = document.getElementById('loading');
        const errorDiv = document.getElementById('error');
        const financialDataTableDiv = document.getElementById('financialDataTable');
        const tableTitle = document.getElementById('tableTitle');

        loadingDiv.style.display = 'block';
        errorDiv.style.display = 'none';
        errorDiv.textContent = '';
        while (financialDataTableDiv.firstChild) {
            financialDataTableDiv.removeChild(financialDataTableDiv.firstChild);
        }
        tableTitle.textContent = '';

        try {
            const response = await fetch(`${API_BASE_URL}?stock_symbol=${stockSymbol}&country=${country}&report_type=${reportType}&report_period=${reportPeriod}`);
            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || `HTTP 錯誤：${response.status}`);
            }
            const data = await response.json();

            if (data.data && data.data.length > 0) {
                data.data.sort((a, b) => {
                    if (a.year !== b.year) return a.year - b.year;
                    return a.quarter - b.quarter;
                });
                currentFinancialData = data.data;
                currentOriginalCurrency = data.data[0].original_currency;
                
                // 在數據載入成功後，才根據勾選狀態繪製圖表和建立表格
                drawChartBasedOnSelection(); 
                createTable(data.data, reportType, currentOriginalCurrency);
            } else {
                errorDiv.textContent = '未找到相關財報資料。';
                errorDiv.style.display = 'block';
                if (myChart) {
                    myChart.destroy();
                    myChart = null;
                }
                currentFinancialData = [];
                currentOriginalCurrency = '';
            }
        } catch (error) {
            console.error('獲取財報資料失敗:', error);
            errorDiv.textContent = `載入資料時發生錯誤：${error.message || error}`;
            errorDiv.style.display = 'block';
            if (myChart) {
                myChart.destroy();
                myChart = null;
            }
            currentFinancialData = [];
            currentOriginalCurrency = '';
        } finally {
            loadingDiv.style.display = 'none';
        }
    }

    // 首次載入財報區塊時，先初始化下拉選單狀態
    handleReportTypeChange(); // 這會觸發 updateChartOptions 和 fetchAndDrawChartAndTable

    // 將內部函數暴露為全域以便 HTML 中呼叫
    window.handleReportTypeChange = handleReportTypeChange;
    window.fetchAndDrawChartAndTable = fetchAndDrawChartAndTable;
    window.drawChartBasedOnSelection = drawChartBasedOnSelection;
}

// 修改 performSearch 讓搜尋時同時查詢財報
async function performSearch() {
    const searchBar = document.querySelector('.search-bar');
    if (!searchBar) return;
    stockSymbol = searchBar.value.trim();
    if (stockSymbol) {
        updateURLParams();
        await loadStockInfo();
        // 每次重新搜尋股票時，都要重新載入財報圖表和數據
        await loadFinancialReport(stockSymbol, country);
    }
}

// 初始化搜尋功能
function initializeSearch() {
    const searchBar = document.querySelector('.search-bar');
    const searchIcon = document.querySelector('.search_icon');

    if (!searchBar || !searchIcon) {
        console.log('找不到搜索相關元素');
        return;
    }

    // 點擊搜索圖標時執行搜索
    searchIcon.addEventListener('click', performSearch);

    // 在搜索欄中按下 Enter 鍵時執行搜索
    searchBar.addEventListener('keypress', (event) => {
        if (event.key === 'Enter') {
            event.preventDefault();
            performSearch();
        }
    });
}

// 初始化漢堡選單功能
function initializeHamburgerMenu() {
    const hamburgerMenu = document.querySelector('.hamburger-menu');
    const navDropdown = document.querySelector('.nav-dropdown');
    const closeButton = document.querySelector('.hamburger-menu-close');

    if (!hamburgerMenu || !navDropdown) {
        console.log('找不到漢堡選單或導航下拉選單元素');
        return;
    }

    // 點擊漢堡選單時切換選單狀態
    hamburgerMenu.addEventListener('click', () => {
        navDropdown.classList.toggle('active');
    });

    // 點擊關閉按鈕時關閉選單
    if (closeButton) {
        closeButton.addEventListener('click', () => {
            navDropdown.classList.remove('active');
        });
    }

    // 點擊下拉選單中的連結時關閉選單
    const dropdownLinks = document.querySelectorAll('.nav-dropdown a');
    dropdownLinks.forEach(link => {
        link.addEventListener('click', () => {
            navDropdown.classList.remove('active');
        });
    });
}

// 頁面載入時執行初始化
document.addEventListener('DOMContentLoaded', async () => {
    initSearchParamsFromURL();
    setSearchBarValue();
    initializeHamburgerMenu();
    initializeSearch();
    if (stockSymbol) {
        await loadStockInfo();
        await loadFinancialReport(stockSymbol, country);
    }
});