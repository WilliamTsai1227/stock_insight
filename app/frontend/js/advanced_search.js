// advanced_search.js
// 1. 載入三個 API
let supportedRankings = {};
let reportTypeRules = {};
let sectorList = [];

async function fetchInitialData() {
    const [rankingsRes, rulesRes, sectorRes] = await Promise.all([
        fetch('/api/advanced_search/supported_rankings'),
        fetch('/api/advanced_search/report_type_rules'),
        fetch('/api/sector/list')
    ]);
    supportedRankings = (await rankingsRes.json()).data;
    reportTypeRules = (await rulesRes.json()).data;
    sectorList = (await sectorRes.json()).data;
}

// ========== 下拉選單初始化與互動規則 ========== //
function fillYearSelect(selectId, minYear, maxYear, defaultYear) {
    const select = document.getElementById(selectId);
    while (select.firstChild) select.removeChild(select.firstChild);
    for (let y = maxYear; y >= minYear; y--) {
        const opt = document.createElement('option');
        opt.value = y;
        opt.textContent = y;
        if (y === defaultYear) opt.selected = true;
        select.appendChild(opt);
    }
}
function fillQuarterSelect(selectId, defaultQuarter) {
    const select = document.getElementById(selectId);
    while (select.firstChild) select.removeChild(select.firstChild);
    for (let q = 1; q <= 4; q++) {
        const opt = document.createElement('option');
        opt.value = q;
        opt.textContent = q;
        if (q === defaultQuarter) opt.selected = true;
        select.appendChild(opt);
    }
}
function fillTypeSelect(selectId, type) {
    const select = document.getElementById(selectId);
    while (select.firstChild) select.removeChild(select.firstChild);
    if (type === 'cash_flow') {
        select.appendChild(new Option('年報', 'annual', true, true));
        select.appendChild(new Option('累計', 'accumulated'));
    } else if (type === 'income_statement') {
        select.appendChild(new Option('年報', 'annual', true, true));
        select.appendChild(new Option('季報', 'quarterly'));
        select.appendChild(new Option('累計', 'accumulated'));
    } else if (type === 'balance_sheet') {
        select.appendChild(new Option('年報', 'annual', false, false));
        select.appendChild(new Option('季報', 'quarterly', true, true));
        select.appendChild(new Option('累計', 'accumulated', false, false));
        select.options[0].disabled = true;
        select.options[2].disabled = true;
    }
}
function updateCashFlowQuarterAndType() {
    const type = document.getElementById('cash-flow-type-select').value;
    const year = parseInt(document.getElementById('cash-flow-year-select').value);
    const quarterSelect = document.getElementById('cash-flow-quarter-select');
    const yearSelect = document.getElementById('cash-flow-year-select');
    // 年報時2025反灰
    for (let i = 0; i < yearSelect.options.length; i++) {
        yearSelect.options[i].disabled = false;
    }
    if (type === 'annual') {
        for (let i = 0; i < yearSelect.options.length; i++) {
            if (yearSelect.options[i].value === '2025') yearSelect.options[i].disabled = true;
        }
        quarterSelect.value = '4';
        for (let i = 0; i < quarterSelect.options.length; i++) {
            quarterSelect.options[i].disabled = true;
        }
    } else if (type === 'accumulated') {
        for (let i = 0; i < yearSelect.options.length; i++) {
            yearSelect.options[i].disabled = false;
        }
        if (year === 2025) {
            quarterSelect.value = '1';
            for (let i = 0; i < quarterSelect.options.length; i++) {
                quarterSelect.options[i].disabled = (quarterSelect.options[i].value !== '1');
            }
        } else {
            if (!['1','2','3'].includes(quarterSelect.value)) quarterSelect.value = '1';
            for (let i = 0; i < quarterSelect.options.length; i++) {
                quarterSelect.options[i].disabled = !['1','2','3'].includes(quarterSelect.options[i].value);
            }
        }
    }
}
function updateIncomeQuarterAndType() {
    const type = document.getElementById('income-type-select').value;
    const year = parseInt(document.getElementById('income-year-select').value);
    const quarterSelect = document.getElementById('income-quarter-select');
    const yearSelect = document.getElementById('income-year-select');
    for (let i = 0; i < yearSelect.options.length; i++) {
        yearSelect.options[i].disabled = false;
    }
    if (type === 'annual') {
        for (let i = 0; i < yearSelect.options.length; i++) {
            if (yearSelect.options[i].value === '2025') yearSelect.options[i].disabled = true;
        }
    }
    for (let i = 0; i < quarterSelect.options.length; i++) {
        quarterSelect.options[i].disabled = false;
    }
    if (type === 'annual') {
        quarterSelect.value = '4';
        for (let i = 0; i < quarterSelect.options.length; i++) {
            quarterSelect.options[i].disabled = true;
        }
    } else if (type === 'accumulated') {
        if (year === 2025) {
            quarterSelect.value = '1';
            for (let i = 0; i < quarterSelect.options.length; i++) {
                quarterSelect.options[i].disabled = (quarterSelect.options[i].value !== '1');
            }
        } else {
            if (!['1','2','3'].includes(quarterSelect.value)) quarterSelect.value = '1';
            for (let i = 0; i < quarterSelect.options.length; i++) {
                quarterSelect.options[i].disabled = !['1','2','3'].includes(quarterSelect.options[i].value);
            }
        }
    } else if (type === 'quarterly') {
        if (year === 2025) {
            quarterSelect.value = '1';
            for (let i = 0; i < quarterSelect.options.length; i++) {
                quarterSelect.options[i].disabled = (quarterSelect.options[i].value !== '1');
            }
        } else {
            if (!['1','2','3','4'].includes(quarterSelect.value)) quarterSelect.value = '1';
            for (let i = 0; i < quarterSelect.options.length; i++) {
                quarterSelect.options[i].disabled = false;
            }
        }
    }
}
function updateBalanceQuarterAndType() {
    const type = document.getElementById('balance-type-select').value;
    const year = parseInt(document.getElementById('balance-year-select').value);
    const quarterSelect = document.getElementById('balance-quarter-select');
    const typeSelect = document.getElementById('balance-type-select');
    // 僅季報可選
    typeSelect.options[0].disabled = true;
    typeSelect.options[2].disabled = true;
    typeSelect.value = 'quarterly';
    for (let i = 0; i < quarterSelect.options.length; i++) {
        quarterSelect.options[i].disabled = false;
    }
    if (year === 2025) {
        quarterSelect.value = '1';
        for (let i = 0; i < quarterSelect.options.length; i++) {
            quarterSelect.options[i].disabled = (quarterSelect.options[i].value !== '1');
        }
    } else {
        if (!['1','2','3','4'].includes(quarterSelect.value)) quarterSelect.value = '1';
        for (let i = 0; i < quarterSelect.options.length; i++) {
            quarterSelect.options[i].disabled = false;
        }
    }
}
function fillMetricSelect(selectId, type) {
    const select = document.getElementById(selectId);
    select.textContent = '';
    const arr = supportedRankings[type] || [];
    arr.forEach(item => {
        const opt = document.createElement('option');
        opt.value = item.key;
        opt.textContent = item.description;
        select.appendChild(opt);
    });
}
function fillSectorSelect(selectId) {
    const select = document.getElementById(selectId);
    select.textContent = '';
    const opt = document.createElement('option');
    opt.value = '';
    opt.textContent = '全部產業';
    select.appendChild(opt);
    sectorList.forEach(sector => {
        const o = document.createElement('option');
        o.value = sector;
        o.textContent = sector;
        select.appendChild(o);
    });
}
async function initPage() {
    await fetchInitialData();
    // 現金流量表
    fillMetricSelect('cash-flow-metric-select', 'cash_flow');
    fillTypeSelect('cash-flow-type-select', 'cash_flow');
    fillYearSelect('cash-flow-year-select', 2016, 2025, 2024);
    fillQuarterSelect('cash-flow-quarter-select', 4);
    fillSectorSelect('cash-flow-sector-select');
    // 損益表
    fillMetricSelect('income-metric-select', 'income_statement');
    fillTypeSelect('income-type-select', 'income_statement');
    fillYearSelect('income-year-select', 2015, 2025, 2024);
    fillQuarterSelect('income-quarter-select', 4);
    fillSectorSelect('income-sector-select');
    // 資產負債表
    fillMetricSelect('balance-metric-select', 'balance_sheet');
    fillTypeSelect('balance-type-select', 'balance_sheet');
    fillYearSelect('balance-year-select', 2015, 2025, 2024);
    fillQuarterSelect('balance-quarter-select', 4);
    fillSectorSelect('balance-sector-select');
    // 綁定互動
    document.getElementById('cash-flow-type-select').addEventListener('change', updateCashFlowQuarterAndType);
    document.getElementById('cash-flow-year-select').addEventListener('change', updateCashFlowQuarterAndType);
    document.getElementById('income-type-select').addEventListener('change', updateIncomeQuarterAndType);
    document.getElementById('income-year-select').addEventListener('change', updateIncomeQuarterAndType);
    document.getElementById('balance-type-select').addEventListener('change', updateBalanceQuarterAndType);
    document.getElementById('balance-year-select').addEventListener('change', updateBalanceQuarterAndType);
    // 查詢按鈕
    document.getElementById('cash-flow-search-btn').onclick = () => searchRanking('cash_flow');
    document.getElementById('income-search-btn').onclick = () => searchRanking('income_statement');
    document.getElementById('balance-search-btn').onclick = () => searchRanking('balance_sheet');
    // 分頁按鈕
    document.getElementById('cash-flow-prev-page').onclick = () => prevPage('cash_flow');
    document.getElementById('cash-flow-next-page').onclick = () => nextPage('cash_flow');
    document.getElementById('income-prev-page').onclick = () => prevPage('income_statement');
    document.getElementById('income-next-page').onclick = () => nextPage('income_statement');
    document.getElementById('balance-prev-page').onclick = () => prevPage('balance_sheet');
    document.getElementById('balance-next-page').onclick = () => nextPage('balance_sheet');
    // 預設狀態
    updateCashFlowQuarterAndType();
    updateIncomeQuarterAndType();
    updateBalanceQuarterAndType();
}

function handleIncomeTypeChange() {
    const type = document.getElementById('income-type-select').value;
    document.getElementById('income-quarter-select').disabled = (type !== 'quarterly');
}
function handleBalanceTypeChange() {
    const type = document.getElementById('balance-type-select').value;
    document.getElementById('balance-quarter-select').disabled = (type !== 'quarterly');
}

// 3. 查詢 API 並渲染結果
let pageState = { cash_flow: 1, income_statement: 1, balance_sheet: 1 };
async function searchRanking(type) {
    pageState[type] = 1;
    await fetchAndRenderRanking(type, getMetric(type), getYear(type), getReportType(type), getQuarter(type), getSector(type), getResultListId(type), getPrevBtnId(type), getNextBtnId(type), 1);
}
async function nextPage(type) {
    pageState[type]++;
    await fetchAndRenderRanking(type, getMetric(type), getYear(type), getReportType(type), getQuarter(type), getSector(type), getResultListId(type), getPrevBtnId(type), getNextBtnId(type), pageState[type]);
}
async function prevPage(type) {
    if (pageState[type] > 1) {
        pageState[type]--;
        await fetchAndRenderRanking(type, getMetric(type), getYear(type), getReportType(type), getQuarter(type), getSector(type), getResultListId(type), getPrevBtnId(type), getNextBtnId(type), pageState[type]);
    }
}
function getMetric(type) {
    if (type === 'cash_flow') return document.getElementById('cash-flow-metric-select').value;
    if (type === 'income_statement') return document.getElementById('income-metric-select').value;
    return document.getElementById('balance-metric-select').value;
}
function getYear(type) {
    if (type === 'cash_flow') return document.getElementById('cash-flow-year-select').value;
    if (type === 'income_statement') return document.getElementById('income-year-select').value;
    return document.getElementById('balance-year-select').value;
}
// 查詢時正確帶入三個下拉選單的值
function getReportType(type) {
    if (type === 'cash_flow') return document.getElementById('cash-flow-type-select').value;
    if (type === 'income_statement') return document.getElementById('income-type-select').value;
    return document.getElementById('balance-type-select').value;
}
function getQuarter(type) {
    if (type === 'cash_flow') return document.getElementById('cash-flow-quarter-select').value;
    if (type === 'income_statement') return document.getElementById('income-quarter-select').value;
    return document.getElementById('balance-quarter-select').value;
}
function getSector(type) {
    if (type === 'cash_flow') return document.getElementById('cash-flow-sector-select').value;
    if (type === 'income_statement') return document.getElementById('income-sector-select').value;
    return document.getElementById('balance-sector-select').value;
}
function getResultListId(type) {
    if (type === 'cash_flow') return 'cash-flow-result-list';
    if (type === 'income_statement') return 'income-result-list';
    return 'balance-result-list';
}
function getPrevBtnId(type) {
    if (type === 'cash_flow') return 'cash-flow-prev-page';
    if (type === 'income_statement') return 'income-prev-page';
    return 'balance-prev-page';
}
function getNextBtnId(type) {
    if (type === 'cash_flow') return 'cash-flow-next-page';
    if (type === 'income_statement') return 'income-next-page';
    return 'balance-next-page';
}
function getMetricLabel(type, metricKey) {
    const arr = supportedRankings[type] || [];
    const found = arr.find(item => item.key === metricKey);
    return found ? found.description : metricKey;
}
function formatValue(val) {
    if (val === null || val === undefined || val === '') return '-';
    if (typeof val === 'number') return val.toLocaleString('zh-TW', {maximumFractionDigits: 2});
    if (!isNaN(val)) return Number(val).toLocaleString('zh-TW', {maximumFractionDigits: 2});
    return val;
}
// 季別渲染：根據 report_type 決定顯示內容
function renderQuarterText(reportType, quarter) {
    if (reportType === 'annual') return '-';
    if (reportType === 'accumulated') return `Q${quarter}累計`;
    if (quarter) return `Q${quarter}`;
    return '';
}
async function fetchAndRenderRanking(type, metric, year, report_type, quarter, sector, resultListId, prevBtnId, nextBtnId, page) {
    const params = new URLSearchParams({
        ranking_type: metric,
        year,
        report_type,
        quarter,
        sector_name: sector,
        page
    });
    const res = await fetch(`/api/advanced_search/ranking?${params.toString()}`);
    const data = await res.json();
    const listDiv = document.getElementById(resultListId);
    listDiv.textContent = '';
    const prevBtn = document.getElementById(prevBtnId);
    const nextBtn = document.getElementById(nextBtnId);
    prevBtn.style.display = 'none';
    nextBtn.style.display = 'none';
    if (data.data && Array.isArray(data.data) && data.data.length > 0) {
        data.data.forEach(item => {
            const div = document.createElement('div');
            div.className = 'result-item';
            // 公司名稱（可點擊）
            const companyLink = document.createElement('span');
            companyLink.className = 'company-link';
            companyLink.textContent = item.company_name;
            companyLink.setAttribute('data-symbol', item.stock_symbol);
            companyLink.onclick = () => {
                window.open(`/stock/${item.stock_symbol}/tw`, '_blank');
            };
            div.appendChild(companyLink);
            // 股票代碼
            const stockSymbol = document.createElement('span');
            stockSymbol.className = 'stock-symbol';
            stockSymbol.textContent = `(${item.stock_symbol})`;
            div.appendChild(stockSymbol);
            // 產業名稱
            const sector = document.createElement('span');
            sector.className = 'sector';
            sector.textContent = `產業名稱：${item.sector_name}`;
            div.appendChild(sector);
            // 指標名稱
            const metricSpan = document.createElement('span');
            metricSpan.className = 'metric';
            metricSpan.textContent = getMetricLabel(type, metric);
            div.appendChild(metricSpan);
            // 數值
            const valueSpan = document.createElement('span');
            valueSpan.className = 'value';
            valueSpan.textContent = formatValue(item[metric]);
            div.appendChild(valueSpan);
            // 年份
            const yearSpan = document.createElement('span');
            yearSpan.className = 'year';
            yearSpan.textContent = `年份：${item.year}`;
            div.appendChild(yearSpan);
            // 季別（可選）
            if (item.quarter) {
                const quarterSpan = document.createElement('span');
                quarterSpan.className = 'quarter';
                quarterSpan.textContent = renderQuarterText(report_type, item.quarter);
                div.appendChild(quarterSpan);
            }
            // 排名
            const rankSpan = document.createElement('span');
            rankSpan.className = 'rank';
            rankSpan.textContent = `排名：${item.rank}`;
            div.appendChild(rankSpan);
            listDiv.appendChild(div);
        });
        // 分頁按鈕顯示邏輯
        if (page > 1 && data.metadata && data.metadata.has_next_page) {
            prevBtn.style.display = '';
            nextBtn.style.display = '';
        } else if (page > 1) {
            prevBtn.style.display = '';
        } else if (data.metadata && data.metadata.has_next_page) {
            nextBtn.style.display = '';
        }
    } else {
        // 無資料
        const noResultDiv = document.createElement('div');
        noResultDiv.className = 'no-result';
        noResultDiv.textContent = '查無資料';
        listDiv.appendChild(noResultDiv);
    }
}

// ========== 新增：漢堡選單初始化 ========== //
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

document.addEventListener('DOMContentLoaded', () => {
    initPage();
    initializeHamburgerMenu(); // 新增這行
    document.getElementById('cash-flow-prev-page').onclick = () => prevPage('cash_flow');
    document.getElementById('cash-flow-next-page').onclick = () => nextPage('cash_flow');
    document.getElementById('income-prev-page').onclick = () => prevPage('income_statement');
    document.getElementById('income-next-page').onclick = () => nextPage('income_statement');
    document.getElementById('balance-prev-page').onclick = () => prevPage('balance_sheet');
    document.getElementById('balance-next-page').onclick = () => nextPage('balance_sheet');
}); 