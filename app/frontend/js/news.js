
let loadingIndicator = document.getElementById("loading-indicator");
let page = 1;
let isLoading = false; // Create a label to indicate whether data is loading
let keyword = "";


let hasMoreData = true;
let endTime = Math.floor(Date.now() / 1000);//現在時間轉換為 Unix timestamp（秒）
let startTime = Math.floor(new Date("2020-01-01T00:00:00Z").getTime() / 1000);// "2020-01-01 00:00:00" 轉換為 Unix timestamp（秒）

function initSearchParamsFromURL() {
    const params = new URLSearchParams(window.location.search);
    keyword = params.get('keyword') || "";
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
        searchBar.value = keyword; // Set the value of the global variable keyword to the search box 
    }
}

function updateURLParams() {
    const params = new URLSearchParams();
    params.set('keyword', keyword);
    params.set('start_time', startTime);
    params.set('end_time', endTime);
    const newUrl = `${window.location.pathname}?${params.toString()}`;
    history.replaceState({}, '', newUrl); // 不重新整理，只更新網址
}


async function loadAllNews(){
    try {
        if (isLoading === true || hasMoreData === false) return; // If data is being loaded, the load operation is not triggered
        isLoading = true; // Start loading data, set isLoading to true
        if (loadingIndicator) loadingIndicator.style.display = "flex"; // Display the loading indicator
        //Can add a printout of the search time to check
        //console.log(`fetch startTime:${startTime}, endTime: ${endTime}`)
        const response = await fetch(`http://localhost:8000/api/news?keyword=${keyword}&start_time=${startTime}&end_time=${endTime}&page=${page}`);
        const result = await response.json();
        // 判斷是否還有下一頁資料
        if (result.nextPage === null || result.data.length === 0) {
            hasMoreData = false;
        } else {
            page = result.nextPage;
        }
        const dataList = result.data;

        const container = document.querySelector(".left-container");

        dataList.forEach(item => {
            const block = document.createElement("div");
            block.className = "block";


            // ---  News Section ---
            const newsSection = document.createElement("div");
            newsSection.className = "news-sesstion";
            // ---  News title ---
            const newsTitle = document.createElement("div");
            newsTitle.textContent = item["title"] || "";
            newsTitle.className = "news-title";
            // ---  News content ---
            const newsContent = document.createElement("div");
            newsContent.className = "news-content";
            newsContent.textContent = item["content"] || "";
            // --- News creation time ---
            const publishAtDiv = document.createElement("div");
            publishAtDiv.className = "publishAtDiv";
            const timestamp = item.publishAt; // Unix timestamp（以秒為單位）
            const date = new Date(timestamp * 1000); // 轉成毫秒
            const taiwanTime = date.toLocaleString("zh-TW", {
            timeZone: "Asia/Taipei",
            });
            publishAtDiv.textContent = taiwanTime;

            // ---  News category ---
            const newsCategory = document.createElement("span");
            let categoryContent = item["category"] || "";
            if (categoryContent === "headline"){
                categoryContent = "頭條新聞";
            }
            newsCategory.textContent = categoryContent;
            newsCategory.className = "category";

            // ---  News source ---
            const newsSource = document.createElement("div");
            let newsSourceContent = item["source"] || "";
            if (newsSourceContent === "anue"){
                newsSourceContent = "鉅亨網";
            }
            newsSource.textContent = newsSourceContent;
            newsSource.className = "source";


            // ---  News URL ---
            const newsURL = document.createElement("div");
            newsURL.textContent = item["url"] || "";
            newsURL.className = "news-url";            

            newsSection.appendChild(newsTitle);
            newsSection.appendChild(newsContent);
            newsSection.appendChild(publishAtDiv);
            newsSection.appendChild(newsSource);
            newsSection.appendChild(newsCategory);
            newsSection.appendChild(newsURL);

            block.appendChild(newsSection);
            container.appendChild(block);
        });
        isLoading = false; // Data loading is complete, set isLoading to false
        if (loadingIndicator) loadingIndicator.style.display = "none"; // Hide the loading indicator
    } catch (error) {
        console.error("Error fetching AI news:", error);
        isLoading = false; // Data loading error, set isLoading to false
        if (loadingIndicator) loadingIndicator.style.display = "none"; // Hide the loading indicator
        const container = document.querySelector(".left-container");
        const errorMessage = document.createElement("div");
        errorMessage.textContent = "Oops! 載入新聞時發生錯誤，請稍後再試。";
        errorMessage.className = "errorMessage";
        container.appendChild(errorMessage);
    }
    monitorNewsClicks();
}

function scrollingAddAIAnalysis(){
    let footer = document.querySelector(".footer");
    window.addEventListener("scroll", function () {
      const { bottom } = footer.getBoundingClientRect();
      const windowHeight = window.innerHeight || document.documentElement.clientHeight;
      if (bottom <= windowHeight) {
        if (page != null){
            loadAllNews();
        }
      }
    });
}

async function performSearch() {
    let input = document.querySelector(".search-bar");
    let container = document.querySelector(".left-container");

    endTime = Math.floor(Date.now() / 1000); // 確保每次搜尋都更新為當前時間
    const startDateInput = document.querySelector('.start-time-calendar');
    const startDateValue = startDateInput.value; // 格式是 "YYYY-MM-DD"
    const endDateInput = document.querySelector('.end-time-calendar');
    const endDateValue = endDateInput.value; // 格式是 "YYYY-MM-DD"

    if (startDateValue !== "") {
        startTime = Math.floor(new Date(startDateValue).getTime() / 1000);
    } else {
        startTime = Math.floor(new Date("2020-01-01T00:00:00Z").getTime() / 1000);
    }
    
    if (endDateValue !== "") {
        endTime = Math.floor(new Date(endDateValue).getTime() / 1000);
    } else {
        endTime = Math.floor(Date.now() / 1000); // If the user clears the date input box, reset it to the current time
    }

    page = 1; // 搜尋時重置頁碼
    hasMoreData = true; // 搜尋時重置是否有更多資料
    keyword = input.value; // 更新關鍵字
    
    // 清空現有的新聞內容
    while(container.firstChild){
        container.removeChild(container.firstChild);
    }
    
    updateURLParams(); // 更新 URL 參數
    await loadAllNews(); // 重新載入新聞
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

function monitorNewsClicks(){
    let listItems = document.querySelectorAll(".news-sesstion");
    listItems.forEach(item => {
        item.addEventListener("click", () => {
            let objectURLElement = item.querySelector(".news-url");
            if (objectURLElement) {
                let objectURL = objectURLElement.textContent.trim();
                window.open(objectURL, '_blank');

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


async function excute(){
    initSearchParamsFromURL();
    setSearchBarValue();      // Set the value of the search box 
    await loadAllNews();
    scrollingAddAIAnalysis();
    search();
    initializeHamburgerMenu();
}
window.addEventListener("DOMContentLoaded", excute);