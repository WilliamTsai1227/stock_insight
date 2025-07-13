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

function fillYearSelect(selectId) {
    const select = document.getElementById(selectId);
    select.innerHTML = '';
    for (let y = 2025; y >= 2015; y--) {
        const opt = document.createElement('option');
        opt.value = y;
        opt.textContent = y + '年';
        select.appendChild(opt);
    }
}

function fillSectorSelect(selectId) {
    const select = document.getElementById(selectId);
    select.innerHTML = '';
    sectorList.forEach(sector => {
        const opt = document.createElement('option');
        opt.value = sector;
        opt.textContent = sector;
        select.appendChild(opt);
    });
}

function fillMetricSelect(selectId, type) {
    const select = document.getElementById(selectId);
    select.innerHTML = '';
    (supportedRankings[type] || []).forEach(item => {
        const opt = document.createElement('option');
        opt.value = item.key;
        opt.textContent = item.description;
        select.appendChild(opt);
    });
}

function fillTypeSelect(selectId, type) {
    const select = document.getElementById(selectId);
    select.innerHTML = '';
    (reportTypeRules[type].supported_periods || []).forEach(period => {
        const opt = document.createElement('option');
        opt.value = period;
        opt.textContent = period === 'annual' ? '年報' : '季報';
        select.appendChild(opt);
    });
}

function fillQuarterSelect(selectId) {
    const select = document.getElementById(selectId);
    select.innerHTML = '';
    ['1','2','3','4'].forEach(q => {
        const opt = document.createElement('option');
        opt.value = q;
        opt.textContent = `第${q}季`;
        select.appendChild(opt);
    });
}

// 2. 初始化所有下拉選單
async function initPage() {
    await fetchInitialData();
    // 現金流量表
    fillMetricSelect('cash-flow-metric-select', 'cash_flow');
    fillYearSelect('cash-flow-year-select');
    fillSectorSelect('cash-flow-sector-select');
    // 損益表
    fillMetricSelect('income-metric-select', 'income_statement');
    fillYearSelect('income-year-select');
    fillTypeSelect('income-type-select', 'income_statement');
    fillQuarterSelect('income-quarter-select');
    fillSectorSelect('income-sector-select');
    // 資產負債表
    fillMetricSelect('balance-metric-select', 'balance_sheet');
    fillYearSelect('balance-year-select');
    fillTypeSelect('balance-type-select', 'balance_sheet');
    fillQuarterSelect('balance-quarter-select');
    fillSectorSelect('balance-sector-select');
    // 預設禁用季/類型選單（依規則）
    document.getElementById('cash-flow-metric-select').addEventListener('change', () => {});
    document.getElementById('income-type-select').addEventListener('change', handleIncomeTypeChange);
    document.getElementById('balance-type-select').addEventListener('change', handleBalanceTypeChange);
    // 查詢按鈕
    document.getElementById('cash-flow-search-btn').onclick = () => searchRanking('cash_flow');
    document.getElementById('income-search-btn').onclick = () => searchRanking('income_statement');
    document.getElementById('balance-search-btn').onclick = () => searchRanking('balance_sheet');
    // 分頁按鈕
    document.getElementById('cash-flow-next-page').onclick = () => nextPage('cash_flow');
    document.getElementById('income-next-page').onclick = () => nextPage('income_statement');
    document.getElementById('balance-next-page').onclick = () => nextPage('balance_sheet');
    // 預設禁用季選單（現金流量表）
    document.getElementById('cash-flow-metric-select').disabled = false;
    document.getElementById('cash-flow-year-select').disabled = false;
    document.getElementById('cash-flow-sector-select').disabled = false;
    document.getElementById('cash-flow-search-btn').disabled = false;
    document.getElementById('cash-flow-next-page').style.display = 'none';
    handleIncomeTypeChange();
    handleBalanceTypeChange();
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
    let metric, year, report_type, quarter, sector, resultListId, nextPageBtnId;
    if (type === 'cash_flow') {
        metric = document.getElementById('cash-flow-metric-select').value;
        year = document.getElementById('cash-flow-year-select').value;
        report_type = 'annual';
        quarter = 4;
        sector = document.getElementById('cash-flow-sector-select').value;
        resultListId = 'cash-flow-result-list';
        nextPageBtnId = 'cash-flow-next-page';
    } else if (type === 'income_statement') {
        metric = document.getElementById('income-metric-select').value;
        year = document.getElementById('income-year-select').value;
        report_type = document.getElementById('income-type-select').value;
        quarter = report_type === 'quarterly' ? document.getElementById('income-quarter-select').value : 4;
        sector = document.getElementById('income-sector-select').value;
        resultListId = 'income-result-list';
        nextPageBtnId = 'income-next-page';
    } else {
        metric = document.getElementById('balance-metric-select').value;
        year = document.getElementById('balance-year-select').value;
        report_type = document.getElementById('balance-type-select').value;
        quarter = report_type === 'quarterly' ? document.getElementById('balance-quarter-select').value : 4;
        sector = document.getElementById('balance-sector-select').value;
        resultListId = 'balance-result-list';
        nextPageBtnId = 'balance-next-page';
    }
    pageState[type] = 1;
    await fetchAndRenderRanking(type, metric, year, report_type, quarter, sector, resultListId, nextPageBtnId, 1);
}

async function nextPage(type) {
    let metric, year, report_type, quarter, sector, resultListId, nextPageBtnId;
    if (type === 'cash_flow') {
        metric = document.getElementById('cash-flow-metric-select').value;
        year = document.getElementById('cash-flow-year-select').value;
        report_type = 'annual';
        quarter = 4;
        sector = document.getElementById('cash-flow-sector-select').value;
        resultListId = 'cash-flow-result-list';
        nextPageBtnId = 'cash-flow-next-page';
    } else if (type === 'income_statement') {
        metric = document.getElementById('income-metric-select').value;
        year = document.getElementById('income-year-select').value;
        report_type = document.getElementById('income-type-select').value;
        quarter = report_type === 'quarterly' ? document.getElementById('income-quarter-select').value : 4;
        sector = document.getElementById('income-sector-select').value;
        resultListId = 'income-result-list';
        nextPageBtnId = 'income-next-page';
    } else {
        metric = document.getElementById('balance-metric-select').value;
        year = document.getElementById('balance-year-select').value;
        report_type = document.getElementById('balance-type-select').value;
        quarter = report_type === 'quarterly' ? document.getElementById('balance-quarter-select').value : 4;
        sector = document.getElementById('balance-sector-select').value;
        resultListId = 'balance-result-list';
        nextPageBtnId = 'balance-next-page';
    }
    pageState[type]++;
    await fetchAndRenderRanking(type, metric, year, report_type, quarter, sector, resultListId, nextPageBtnId, pageState[type]);
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
async function fetchAndRenderRanking(type, metric, year, report_type, quarter, sector, resultListId, nextPageBtnId, page) {
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
    listDiv.innerHTML = '';
    if (data.data && Array.isArray(data.data) && data.data.length > 0) {
        data.data.forEach(item => {
            const div = document.createElement('div');
            div.className = 'result-item';
            // 條列式：公司名稱、代碼、產業名稱、查詢財報項目、數值、年份、(季份)、排名
            div.innerHTML = `
                <span class="company-link" data-symbol="${item.stock_symbol}">${item.company_name}</span>
                <span class="stock-symbol">(${item.stock_symbol})</span>
                <span class="sector">產業名稱：${item.sector_name}</span>
                <span class="metric">${getMetricLabel(type, metric)}</span>
                <span class="value">${formatValue(item[metric])}</span>
                <span class="year">年份：${item.year}</span>
                ${item.quarter ? `<span class="quarter">Q${item.quarter}</span>` : ''}
                <span class="rank">排名：${item.rank}</span>
            `;
            div.querySelector('.company-link').onclick = () => {
                window.open(`/stock/${item.stock_symbol}/tw`, '_blank');
            };
            listDiv.appendChild(div);
        });
        document.getElementById(nextPageBtnId).style.display = data.metadata && data.metadata.has_next_page ? '' : 'none';
    } else {
        listDiv.innerHTML = '<div class="no-result">查無資料</div>';
        document.getElementById(nextPageBtnId).style.display = 'none';
    }
}

document.addEventListener('DOMContentLoaded', initPage); 