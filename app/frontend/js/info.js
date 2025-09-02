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

// Footer 三個標籤導向 info.html hash
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

// 自動滾動到 hash 區塊
function scrollToHashBlock() {
    if (window.location.hash) {
        var el = document.getElementById(window.location.hash.replace('#',''));
        if (el) el.scrollIntoView({behavior:'smooth', block:'start'});
    }
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
    initializeHamburgerMenu();
    initializeFooterLinks();
    scrollToHashBlock();
    monitorUserIconClicks();
}
window.addEventListener("DOMContentLoaded", excute); 