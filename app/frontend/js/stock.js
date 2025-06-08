let loadingIndicator = document.getElementById("loading-indicator");
let stockSymbol = "";
let country = "tw";

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
        document.getElementById('stock-header').innerHTML = '';
        document.getElementById('stock-chart').innerHTML = '';
        document.getElementById('stock-info').innerHTML = '';
        
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
        document.getElementById('stock-header').innerHTML = '';
        document.getElementById('stock-chart').innerHTML = '';
        document.getElementById('stock-info').innerHTML = '';
        
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
    stockHeader.innerHTML = `
        <h1 class="stock-title">${data.company_name || '-'} (${data.stock_symbol || '-'}.${country})</h1>
    `;

    // 顯示K線圖（這裡先留空，之後可以加入）
    const stockChartDiv = document.getElementById('stock-chart');
    stockChartDiv.innerHTML = '<canvas id="priceChart"></canvas>';

    // 顯示詳細資訊
    const stockInfo = document.getElementById('stock-info');
    stockInfo.innerHTML = `
        <table class="stock-info-table">
            <tr>
                <th>公司簡稱</th>
                <td>${data.abbreviation || '-'}</td>
                <th>成立日期</th>
                <td>${data.founding_date || '-'}</td>
            </tr>
            <tr>
                <th>上市日期</th>
                <td>${data.listed_date || '-'}</td>
                <th>上櫃日期</th>
                <td>${data.otc_listed_date || '-'}</td>
            </tr>
            <tr>
                <th>市場</th>
                <td>${data.market || '-'}</td>
                <th>產業</th>
                <td>${data.sector_name || '-'}</td>
            </tr>
            <tr>
                <th>公司地址</th>
                <td colspan="3">${data.address || '-'}</td>
            </tr>
            <tr>
                <th>董事長</th>
                <td>${data.chairman || '-'}</td>
                <th>總經理</th>
                <td>${data.general_manager || '-'}</td>
            </tr>
            <tr>
                <th>發言人</th>
                <td>${data.spokesperson || '-'}</td>
                <th>發言人職稱</th>
                <td>${data.spokesperson_title || '-'}</td>
            </tr>
            <tr>
                <th>已發行普通股數</th>
                <td>${data.outstanding_common_shares?.toLocaleString() || '-'}</td>
                <th>私募普通股</th>
                <td>${data.private_placement_common_shares?.toLocaleString() || '-'}</td>
            </tr>
            <tr>
                <th>特別股</th>
                <td>${data.preferred_shares?.toLocaleString() || '-'}</td>
                <th>簽證會計師事務所</th>
                <td>${data.accounting_firm || '-'}</td>
            </tr>
            <tr>
                <th>簽證會計師1</th>
                <td>${data.accountant_1 || '-'}</td>
                <th>簽證會計師2</th>
                <td>${data.accountant_2 || '-'}</td>
            </tr>
            <tr>
                <th>公司網址</th>
                <td colspan="3">
                    ${data.website ? `<a href="${data.website}" target="_blank">${data.website}</a>` : '-'}
                </td>
            </tr>
            <tr>
                <th>普通股盈餘分派頻率</th>
                <td>${data.common_stock_dividend_frequency || '-'}</td>
                <th>現金股息決議層級</th>
                <td>${data.common_stock_dividend_decision_level || '-'}</td>
            </tr>
            <tr>
                <th>公司簡介</th>
                <td colspan="3">${data.description || '-'}</td>
            </tr>
        </table>
    `;
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

// 執行搜尋
async function performSearch() {
    const searchBar = document.querySelector('.search-bar');
    if (!searchBar) return;

    stockSymbol = searchBar.value.trim();
    if (stockSymbol) {
        updateURLParams();
        await loadStockInfo();
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

// 執行所有初始化功能
async function execute() {
    initSearchParamsFromURL();
    setSearchBarValue();
    initializeHamburgerMenu();
    initializeSearch();
    
    if (stockSymbol) {
        await loadStockInfo();
    }
}

// 頁面載入時執行初始化
document.addEventListener('DOMContentLoaded', execute); 