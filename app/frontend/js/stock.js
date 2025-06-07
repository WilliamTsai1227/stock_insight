// 初始化漢堡選單功能
function initializeHamburgerMenu() {
    const hamburgerMenu = document.querySelector('.hamburger-menu');
    const navDropdown = document.querySelector('.nav-dropdown');
    const closeButton = document.querySelector('.hamburger-menu-close');
    const dropdownLinks = document.querySelectorAll('.nav-dropdown a');

    if (!hamburgerMenu || !navDropdown) {
        console.log('找不到漢堡選單或導航下拉選單元素');
        return;
    }

    // 點擊漢堡選單時切換選單狀態
    hamburgerMenu.addEventListener('click', () => {
        hamburgerMenu.classList.toggle('active');
        navDropdown.classList.toggle('active');
        if (closeButton) {
            closeButton.style.display = navDropdown.classList.contains('active') ? 'block' : 'none';
        }
    });

    // 點擊關閉按鈕時關閉選單
    if (closeButton) {
        closeButton.addEventListener('click', () => {
            hamburgerMenu.classList.remove('active');
            navDropdown.classList.remove('active');
            closeButton.style.display = 'none';
        });
    }

    // 點擊下拉選單中的連結時關閉選單
    dropdownLinks.forEach(link => {
        link.addEventListener('click', () => {
            hamburgerMenu.classList.remove('active');
            navDropdown.classList.remove('active');
            if (closeButton) {
                closeButton.style.display = 'none';
            }
        });
    });

    // 當視窗寬度大於 768px 時關閉選單
    window.addEventListener('resize', () => {
        if (window.innerWidth > 768) {
            hamburgerMenu.classList.remove('active');
            navDropdown.classList.remove('active');
            if (closeButton) {
                closeButton.style.display = 'none';
            }
        }
    });
}

// 初始化搜索功能
function initializeSearch() {
    const searchBar = document.querySelector('.search-bar');
    const startTimeCalendar = document.querySelector('.start-time-calendar');
    const endTimeCalendar = document.querySelector('.end-time-calendar');
    const searchIcon = document.querySelector('.search_icon');
    const loadingIndicator = document.getElementById('loading-indicator');
    const container = document.querySelector('.container');

    if (!searchBar || !searchIcon || !loadingIndicator || !container) {
        console.log('找不到搜索相關元素');
        return;
    }

    // 執行搜索
    async function performSearch() {
        const searchTerm = searchBar.value.trim();
        const startTime = startTimeCalendar ? startTimeCalendar.value : '';
        const endTime = endTimeCalendar ? endTimeCalendar.value : '';

        // 顯示載入中指示器
        loadingIndicator.style.display = 'block';

        try {
            // 構建 API URL
            const apiUrl = `/api/stock/search?term=${encodeURIComponent(searchTerm)}`;
            const response = await fetch(apiUrl);

            if (!response.ok) {
                throw new Error('搜索請求失敗');
            }

            const data = await response.json();

            // 清空容器
            container.innerHTML = '';

            if (data.length === 0) {
                container.innerHTML = '<p>沒有找到相關結果</p>';
                return;
            }

            // 顯示搜索結果
            data.forEach(item => {
                const resultElement = document.createElement('div');
                resultElement.className = 'search-result';
                resultElement.innerHTML = `
                    <h3>${item.title}</h3>
                    <p>${item.description}</p>
                    <div class="result-meta">
                        <span>${item.date}</span>
                        <span>${item.source}</span>
                    </div>
                `;
                container.appendChild(resultElement);
            });

        } catch (error) {
            console.error('搜索過程中發生錯誤:', error);
            container.innerHTML = '<p>搜索過程中發生錯誤，請稍後再試</p>';
        } finally {
            // 隱藏載入中指示器
            loadingIndicator.style.display = 'none';
        }
    }

    // 點擊搜索圖標時執行搜索
    searchIcon.addEventListener('click', performSearch);

    // 在搜索欄中按下 Enter 鍵時執行搜索
    searchBar.addEventListener('keypress', (event) => {
        if (event.key === 'Enter') {
            performSearch();
        }
    });
}

// 初始化所有功能
function initialize() {
    initializeHamburgerMenu();
    initializeSearch();
}

// 當 DOM 內容載入完成時初始化
document.addEventListener('DOMContentLoaded', initialize); 