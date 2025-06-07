function initializeHamburgerMenu() {
    const hamburgerMenu = document.querySelector('.hamburger-menu');
    const navDropdown = document.querySelector('.nav-dropdown');
    const hamburgerClose = document.querySelector('.hamburger-menu-close');

    if (!hamburgerMenu || !navDropdown) {
        console.warn('漢堡選單或導覽下拉選單元素不存在。');
        return;
    }

    hamburgerMenu.addEventListener('click', () => {
        hamburgerMenu.classList.toggle('active');
        navDropdown.classList.toggle('active');
    });

    if (hamburgerClose) {
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
    handleResize();
}

function initializeSearch() {
    const searchBar = document.querySelector('.search-bar');
    const startTimeCalendar = document.querySelector('.start-time-calendar');
    const endTimeCalendar = document.querySelector('.end-time-calendar');
    const searchIcon = document.querySelector('.search_icon');
    const loadingIndicator = document.getElementById('loading-indicator');
    const container = document.querySelector('.container');

    if (!searchBar || !startTimeCalendar || !endTimeCalendar || !searchIcon || !loadingIndicator || !container) {
        console.warn('搜索相關元素不存在。');
        return;
    }

    function performSearch() {
        const searchTerm = searchBar.value.trim();
        const startTime = startTimeCalendar.value;
        const endTime = endTimeCalendar.value;

        if (!searchTerm) {
            alert('請輸入搜索關鍵字');
            return;
        }

        loadingIndicator.style.display = 'block';
        container.innerHTML = '';

        // 這裡添加實際的搜索邏輯
        fetch(`http://localhost:8000/analysis_search?keyword=${encodeURIComponent(searchTerm)}&start_time=${encodeURIComponent(startTime)}&end_time=${encodeURIComponent(endTime)}`)
            .then(response => {
                if (!response.ok) {
                    throw new Error('搜索請求失敗');
                }
                return response.json();
            })
            .then(data => {
                // 處理搜索結果
                if (data.length === 0) {
                    container.innerHTML = '<p>沒有找到相關結果</p>';
                } else {
                    // 這裡添加結果顯示邏輯
                    container.innerHTML = '<p>搜索結果將在這裡顯示</p>';
                }
            })
            .catch(error => {
                console.error('搜索錯誤:', error);
                container.innerHTML = `<p class="error">搜索時發生錯誤: ${error.message}</p>`;
            })
            .finally(() => {
                loadingIndicator.style.display = 'none';
            });
    }

    searchIcon.addEventListener('click', performSearch);
    searchBar.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            performSearch();
        }
    });
}

function initialize() {
    initializeHamburgerMenu();
    initializeSearch();
}

window.addEventListener('DOMContentLoaded', initialize); 