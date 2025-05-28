document.addEventListener('DOMContentLoaded', () => {


    const hamburgerMenu = document.querySelector('.hamburger-menu');
    const navDropdown = document.querySelector('.nav-dropdown');
    const hamburgerClose = document.querySelector('.hamburger-menu-close'); // 獲取關閉按鈕

    hamburgerMenu.addEventListener('click', () => {
        hamburgerMenu.classList.toggle('active');
        navDropdown.classList.toggle('active');
    });

    // 監聽關閉按鈕點擊事件
    hamburgerClose.addEventListener('click', () => {
        hamburgerMenu.classList.remove('active');
        navDropdown.classList.remove('active');
    });

    // 點擊下拉選單中的連結後，收起選單
    navDropdown.querySelectorAll('a').forEach(link => {
        link.addEventListener('click', () => {
            hamburgerMenu.classList.remove('active');
            navDropdown.classList.remove('active');
        });
    });

    // 處理視窗大小改變時的導覽列顯示/隱藏
    const handleResize = () => {
        if (window.innerWidth > 768) {
            // 如果是桌面版，確保漢堡選單和下拉選單是隱藏的
            hamburgerMenu.classList.remove('active');
            navDropdown.classList.remove('active');
        }
    };

    window.addEventListener('resize', handleResize);
    // 首次載入時執行一次，以確保狀態正確
    handleResize();
});