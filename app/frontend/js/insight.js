
let loadingIndicator = document.getElementById("loading-indicator");
let page = 1;
let isLoading = false; // Create a label to indicate whether data is loading
let keyword = "";
let industry = "";
let is_summary = false;
let hasMoreData = true;
let endTime = Math.floor(Date.now() / 1000);//現在時間轉換為 Unix timestamp（秒）
let startTime = Math.floor(new Date("2020-01-01T00:00:00Z").getTime() / 1000);// "2020-01-01 00:00:00" 轉換為 Unix timestamp（秒）

function initSearchParamsFromURL() {
    const params = new URLSearchParams(window.location.search);
    keyword = params.get('keyword') || "";
    industry = params.get('industry') || "";
    is_summary = params.get('is_summary') || false;  
    if (is_summary === "true"){
        is_summary = true;
    }
    if (is_summary === "false"){
        is_summary = false;
    }
    const startDateParam = params.get('start_time');
    const endDateParam = params.get('end_time');

    // 只有當 URL 中有有效的 start_time 參數時才覆蓋預設值
    if (startDateParam && /^\d+$/.test(startDateParam)) {
        startTime = parseInt(startDateParam, 10);
    } else {
        // 如果 URL 中沒有或無效，則使用程式碼預設的 2020-01-01
        startTime = Math.floor(new Date("2020-01-01T00:00:00Z").getTime() / 1000);
    }

    // 只有當 URL 中有有效的 end_time 參數時才覆蓋預設值
    if (endDateParam && /^\d+$/.test(endDateParam)) {
        endTime = parseInt(endDateParam, 10);
    } else {
        // 如果 URL 中沒有或無效，則使用程式碼預設的當前時間
        endTime = Math.floor(Date.now() / 1000);
    }
    // Default page number
    page = 1;
}

// 函式：設定搜尋框的值
function setSearchBarValue() {
    const searchBar = document.querySelector('.search-bar');
    if (searchBar) {
        searchBar.value = keyword; // 將全域變數 keyword 的值設定到搜尋框
    }
}

// 用於根據 is_summary 設定下拉選單顯示
function setAnalysisTypeSelect() {
    const selectElement = document.querySelector('.analysis-type-select');
    if (selectElement) {
        // 根據全域變數 is_summary 的布林值來選取對應的選項
        if (is_summary === true) {
            selectElement.value = "true"; // 設定為統整分析對應的值
        } else {
            selectElement.value = "false"; // 設定為逐條分析對應的值
        }
    }
}

function updateURLParams() {
    const params = new URLSearchParams();
    params.set('keyword', keyword);
    params.set('industry', industry);
    params.set('is_summary', is_summary);
    params.set('start_time', startTime);
    params.set('end_time', endTime);
    const newUrl = `${window.location.pathname}?${params.toString()}`;
    history.replaceState({}, '', newUrl); // 不重新整理，只更新網址
}


async function loadAllAIAnalysis(){
    try {
        if (isLoading === true || hasMoreData === false) return; // If data is being loaded, the load operation is not triggered
        isLoading = true; // Start loading data, set isLoading to true
        if (loadingIndicator) loadingIndicator.style.display = "flex"; // Display the loading indicator
        console.log(`fetch startTime:${startTime}, endTime: ${endTime}`)
        const response = await fetch(`/api/ai_news?keyword=${keyword}&industry=${industry}&is_summary=${is_summary}&start_time=${startTime}&end_time=${endTime}&page=${page}`);
        const result = await response.json();
        // 判斷是否還有下一頁資料
        if (result.nextPage === null || result.data.length === 0) {
            hasMoreData = false;
        } else {
            page = result.nextPage;
        }
        const dataList = result.data;

        const container = document.querySelector(".container");

        dataList.forEach(item => {
            const block = document.createElement("div");
            block.className = "block";


            

            // --- 包裹後面四個區塊的容器 ---
            const blockContent = document.createElement("div");
            blockContent.className = "block-content";


            // --- 1. Summary Section ---
            const aiSection = document.createElement("div");
            aiSection.className = "section ai-summary";
            const aiSectionDiv = document.createElement("div");
            
            const title = document.createElement('div');
            title.className = 'ai-analysis-article-title';
            title.textContent = item.article_title || '';
            aiSectionDiv.appendChild(title);
            aiSection.appendChild(aiSectionDiv);
            


            //洞察結果 重點新聞 情緒分析

            

            const summaryTitle = document.createElement("div");
            summaryTitle.textContent = "洞察結果: ";
            summaryTitle.className = "news-summary";

            const summaryContent = document.createElement("div");
            summaryContent.className = "news-summary-content";

            // 將句子以 "。" 分割，並加回 "。" + 換行處理
            const summaryLines = (item.summary || '').split('。');

            summaryLines.forEach((line) => {
                if (line.trim() !== '') {
                    summaryContent.appendChild(document.createTextNode(line + '。'));
                    summaryContent.appendChild(document.createElement("br"));
                    summaryContent.appendChild(document.createElement("br"));
                }
            });

            aiSectionDiv.appendChild(summaryTitle);
            aiSectionDiv.appendChild(summaryContent);
            
            const keyNewsTitle = document.createElement("div");
            keyNewsTitle.textContent = "重點新聞: ";
            keyNewsTitle.className = "key-news";
            const keyNewsContent = document.createElement("div");
            keyNewsContent.className = "key-news-content";
            const importantNewsLines = item.important_news.split('\n');// 使用 \n 拆分文字

            // 每一行都創建文字節點和 <br>
            importantNewsLines.forEach((importantNewsLines, index) => {
                keyNewsContent.appendChild(document.createTextNode(importantNewsLines));
                if (index < importantNewsLines.length - 1) {
                    keyNewsContent.appendChild(document.createElement("br"));
                }
            });
            aiSectionDiv.appendChild(keyNewsTitle);
            aiSectionDiv.appendChild(keyNewsContent);

            const sentimentTitle = document.createElement("div");
            sentimentTitle.textContent = "情緒分析: " ;
            sentimentTitle.className = "sentiment-analysis";
            const sentimentContent = document.createElement("div");
            sentimentContent.textContent = item.sentiment || '';;
            sentimentContent.className = "sentiment-analysis-content";
            aiSectionDiv.appendChild(sentimentTitle);
            aiSectionDiv.appendChild(sentimentContent);

            // 股票產業分析
            const potentialBigTitle = document.createElement("div");
            potentialBigTitle.textContent = "產業分析";
            potentialBigTitle.className = "section-title";
            aiSectionDiv.appendChild(potentialBigTitle);

            const potentialContentDiv= document.createElement("div");
            potentialContentDiv.className = "potential-content";
                        
            const lines = item.potential_stocks_and_industries.split('\n');// 使用 \n 拆分文字

            // 每一行都創建文字節點和 <br>
            lines.forEach((line, index) => {
                potentialContentDiv.appendChild(document.createTextNode(line));
                if (index < lines.length - 1) {
                    potentialContentDiv.appendChild(document.createElement("br"));
                }
            });
            aiSectionDiv.appendChild(potentialContentDiv);

            // --- 3. Stock List Section ---
            const listSection = document.createElement("div");
            listSection.className = "list-section";

            const stockListBigTitle = document.createElement("div");
            stockListBigTitle.textContent = "相關股票";
            stockListBigTitle.className = "section-title";
            listSection.appendChild(stockListBigTitle);
            aiSectionDiv.appendChild(listSection);

            const stockList = document.createElement('div');
            stockList.className = 'ai-analysis-stock-list';
            

            (item.stock_list || []).forEach(stock => {
                const div = document.createElement("div");
                div.className = "stock-list-item";
                div.textContent = stock[2] || '';
                const span = document.createElement("span");
                span.className = "stock-list-item-code";
                const firstTwo = stock.slice(0, 2); // 取第 0 和第 1 個元素
                span.textContent = firstTwo.join(",") || '';  // 例如："2330,TSMC"
                div.appendChild(span);
                const [market, number] = firstTwo;
                const tooltip = document.createElement('div');
                tooltip.className = 'stock-tooltip';
                tooltip.textContent = `股票代碼：${market} ${number}`|| '';
                div.appendChild(tooltip);
                stockList.appendChild(div);
                
            });
            listSection.appendChild(stockList);
            aiSectionDiv.appendChild(listSection);

            const industryListBigTitle = document.createElement("div");
            industryListBigTitle.textContent = "相關產業";
            industryListBigTitle.className = "section-title";
            listSection.appendChild(industryListBigTitle);
            aiSectionDiv.appendChild(listSection);

            const industryList = document.createElement('div');
            industryList.className = 'ai-analysis-industry-list';

            item.industry_list.forEach(ind => {
                const div = document.createElement("div");
                div.className = "industry-list-item";
                div.textContent = ind || '';
                industryList.appendChild(div);
                
            });
            listSection.appendChild(industryList);
            
            const newsSection = document.createElement("div");
            newsSection.className = "news-section";
            const newsBigTitle = document.createElement("div");
            newsBigTitle.textContent = "相關新聞";
            newsBigTitle.className = "section-title"
            newsSection.appendChild(newsBigTitle);
            aiSectionDiv.appendChild(newsSection);

            const sourceNewsList = document.createElement('div');
            sourceNewsList.className = 'ai-analysis-source-news-list';

            item.source_news.forEach(news => {
                const newsDiv = document.createElement("div");
                newsDiv.className = "news-item";
                newsDiv.textContent = news.title || '';
                const idSpan = document.createElement("span");
                idSpan.textContent = news["_id"] || "";
                idSpan.className = "news-item-id";
                newsDiv.appendChild(idSpan);
                sourceNewsList.appendChild(newsDiv);
                
            });
            newsSection.appendChild(sourceNewsList);

            //Establish a creation time block
            const publishAtDiv = document.createElement("div");
            publishAtDiv.className = "publishAtDiv";
            const timestamp = item.publishAt; // Unix timestamp（以秒為單位）
            const date = new Date(timestamp * 1000); // 轉成毫秒

            const taiwanTime = date.toLocaleString("zh-TW", {
            timeZone: "Asia/Taipei",
            });
            publishAtDiv.textContent = taiwanTime || '';
            aiSectionDiv.appendChild(publishAtDiv);



            blockContent.appendChild(aiSection);

            block.appendChild(blockContent);
            // 將整個 block 加入 container
            container.appendChild(block);
        });
        isLoading = false; // Data loading is complete, set isLoading to false
        if (loadingIndicator) loadingIndicator.style.display = "none"; // Hide the loading indicator
    } catch (error) {
        console.error("Error fetching AI news:", error);
        isLoading = false; // Data loading error, set isLoading to false
        if (loadingIndicator) loadingIndicator.style.display = "none"; // Hide the loading indicator
        const container = document.querySelector(".container");
        const errorMessage = document.createElement("div");
        errorMessage.textContent = "Oops! 載入時發生錯誤，請稍後再試。";
        errorMessage.className = "errorMessage";
        container.appendChild(errorMessage);
    }
    monitorNewsClicks();
    monitorStockClicks();
}

function scrollingAddAIAnalysis(){
    let footer = document.querySelector(".footer");
    window.addEventListener("scroll", function () {
      const { bottom } = footer.getBoundingClientRect();
      const windowHeight = window.innerHeight || document.documentElement.clientHeight;
      if (bottom <= windowHeight) {
        if (page != null){
            loadAllAIAnalysis();
        }
      }
    });
}

async function performSearch(){
    let input = document.querySelector(".search-bar");
    let container = document.querySelector(".container");

    endTime = Math.floor(Date.now() / 1000);
    const startDateInput = document.querySelector('.start-time-calendar');
    const startDateValue = startDateInput.value; // 格式是 "YYYY-MM-DD"
    const endDateInput = document.querySelector('.end-time-calendar');
    const endDateValue = endDateInput.value; // 格式是 "YYYY-MM-DD"
    const isSummaryValue = document.querySelector('.analysis-type-select').value;
    if (isSummaryValue === "true"){
        is_summary = true;
    }else if(isSummaryValue === "false"){
        is_summary = false;
    }

    if (startDateValue !== "") {
        startTime = Math.floor(new Date(startDateValue).getTime() / 1000);
    }else {
        startTime = Math.floor(new Date("2020-01-01T00:00:00Z").getTime() / 1000);
    }
    
    if (endDateValue !== "") {
        endTime = Math.floor(new Date(endDateValue).getTime() / 1000);
    }else {
        endTime = Math.floor(Date.now() / 1000); // If the user clears the date input box, reset it to the current time
    }
    page = 1;
    hasMoreData = true;
    keyword = input.value;
    while(container.firstChild){
        container.removeChild(container.firstChild);
    }
    updateURLParams();
    await loadAllAIAnalysis();

}

function search(){
    let button = document.querySelector(".search_icon");
    let input = document.querySelector(".search-bar");
    
    // 監聽搜尋按鈕點擊事件
    button.addEventListener("click", performSearch);

    // 監聽搜尋輸入框的鍵盤事件
    input.addEventListener("keydown", async (event) => {
        if (event.key === "Enter") {
            event.preventDefault(); // 阻止 Enter 鍵的預設行為 (例如提交表單)
            await performSearch();
        }
    });
}

function monitorNewsClicks() {
    let listItems = document.querySelectorAll(".news-item");
    listItems.forEach(item => {
        item.addEventListener("click", async () => {
            let objectIdElement = item.querySelector(".news-item-id");
            if (objectIdElement) {
                let objectId = objectIdElement.textContent.trim();
                try {
                    const response = await fetch(`/api/news/${objectId}`);
                    if (!response.ok) {
                        // 當 response.ok 為 false 時，表示 HTTP 狀態碼是 4xx 或 5xx,在這裡拋出錯誤，讓 catch 區塊處理
                        throw new Error(`HTTP 錯誤狀態碼: ${response.status}`);
                    }
                    const data = await response.json();
                    const news = data.data;
                    const sourceURL = news.url.trim();
                    window.open(sourceURL, '_blank');

                } catch (error) {
                    console.error("無法載入原始網站，請至搜尋引擎搜尋標題關鍵字，觀看原始網站文章", error);
                    alert("無法載入原始網站，請至搜尋引擎搜尋標題關鍵字，觀看原始網站文章");
                }
            }
        });
    });
}


function monitorStockClicks() {
    let listItems = document.querySelectorAll(".stock-list-item");
    listItems.forEach(item => {
        item.addEventListener("click", () => {
            // 獲取股票名稱
            let stockName = item.childNodes[0].textContent.trim();
            
            // 獲取股票代碼（例如 tw,4938 或 us,TSLA）
            let stockCodeElement = item.querySelector(".stock-list-item-code");
            let stockCodeText = stockCodeElement ? stockCodeElement.textContent.trim() : "";
            let [market, stockCode] = stockCodeText.split(",");

            if (market === "tw"){
                window.open(`/stock/${stockCode}/${market}`);
            }else{
                // 開啟Google 搜尋並保持當前窗口焦點
                let googleStockWindow = window.open(`https://www.google.com/search?q=${stockName}`, '_blank');
                if (!googleStockWindow) {
                    alert("Google 搜尋窗口被攔截，請檢查瀏覽器彈窗設定。");
                } else {
                    window.focus(); // 保持當前窗口焦點
                }    
            }
            

        });
    });
}


function initializeHamburgerMenu() {
    const hamburgerMenu = document.querySelector('.hamburger-menu');
    const navDropdown = document.querySelector('.nav-dropdown');
    const hamburgerClose = document.querySelector('.hamburger-menu-close');
  
    if (!hamburgerMenu || !navDropdown) {
        console.warn('漢堡選單或導覽下拉選單元素不存在。');
        return; // 如果必要的元素不存在，則不執行後續程式碼
    }
  
    hamburgerMenu.addEventListener('click', () => {
        hamburgerMenu.classList.toggle('active');
        navDropdown.classList.toggle('active');
    });
  
    if (hamburgerClose) { // 確保關閉按鈕存在才綁定事件
        hamburgerClose.addEventListener('click', () => {
            hamburgerMenu.classList.remove('active');
            navDropdown.classList.remove('active');
        });
    } else {
        console.warn('漢堡選單關閉按鈕元素不存在。');
    }
  
  
    navDropdown.querySelectorAll('a').forEach(link => {
        link.addEventListener('click', () => {
            hamburgerMenu.classList.remove('active');
            navDropdown.classList.remove('active');
        });
    });
  
    const handleResize = () => {
        if (window.innerWidth > 768) {
            hamburgerMenu.classList.remove('active');
            navDropdown.classList.remove('active');
        }
    };
  
    window.addEventListener('resize', handleResize);
    handleResize(); // 初始載入時執行一次
  }

function initializeFooterLinks() {
    document.getElementById('footer-purpose-link')?.addEventListener('click', function() {
        window.open('/info', '_blank', 'noopener,noreferrer');
    });
    document.getElementById('footer-contact-link')?.addEventListener('click', function() {
        window.open('/info', '_blank', 'noopener,noreferrer');
    });
    document.getElementById('footer-disclaimer-link')?.addEventListener('click', function() {
        window.open('/info', '_blank', 'noopener,noreferrer');
    });
}



async function excute(){
    initSearchParamsFromURL();
    setSearchBarValue();      // Set the value of the search box 
    setAnalysisTypeSelect(); 
    await loadAllAIAnalysis();
    scrollingAddAIAnalysis();
    search();
    initializeHamburgerMenu();
    initializeFooterLinks();
    
}
window.addEventListener("DOMContentLoaded", excute);