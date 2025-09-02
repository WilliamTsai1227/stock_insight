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
function monitorFeatureCardClicks() {
    const featureCards = document.querySelectorAll('.feature-card');

    featureCards.forEach(card => {
        card.addEventListener("click", () => {
            const cardId = card.id; 
            let targetUrl = ''; 

            switch (cardId) {
                case 'feature-card-news':
                    targetUrl = '/news';
                    break;
                case 'feature-card-insight':
                    targetUrl = '/insight';
                    break;
                case 'feature-card-stock':
                    targetUrl = '/stock/2330/tw'; 
                    break;
                case 'feature-card-advanced-search':
                    targetUrl = '/advanced_search';
                    break;
                default:
                    console.warn(`未知的卡片 ID: ${cardId}`);
                    break;
            }

            if (targetUrl) {
                window.location.href = targetUrl; 
            }
        });
    });
}

function monitorUserIconClicks() {
    const userIcon = document.querySelector(".profile-image");
    if (userIcon) {
        userIcon.addEventListener('click', function() {
            window.location.href = '/login';
        });
    }
}



function excute(){
    monitorFeatureCardClicks();
    initializeHamburgerMenu();
    initializeFooterLinks();
    monitorUserIconClicks()
}
window.addEventListener("DOMContentLoaded", excute);