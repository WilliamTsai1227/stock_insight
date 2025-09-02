const loginForm = document.querySelector(".login-form");
const loginArea = document.querySelector(".login-container");
const usernameInput = document.querySelector("#email");
const passwordInput = document.querySelector("#password");
const loginButton = document.querySelector(".login-button");
const logoutButton = document.querySelector(".logout-button");
const errorMessage = document.querySelector("#login-error");
const passwordLittleTitle = document.querySelector("#password-l-title")


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

function monitorUserIconClicks() {
    const userIcon = document.querySelector(".profile-image");
    if (userIcon) {
        userIcon.addEventListener('click', function() {
            window.location.href = '/login';
        });
    }
}


// ======= Input validation function =======
function checkAccountFormat(account) {
    const accountPattern = /\w[-\w.+]*@([A-Za-z0-9][-A-Za-z0-9]+\.)+[A-Za-z]{2,14}/;
    return accountPattern.test(account);
}

function checkPasswordFormat(password) {
    const passwordPattern = /^[A-Za-z0-9]{8,}$/;
    return passwordPattern.test(password);
}

// ======= Verify user identity =======
async function getUserData() {
    try {
        const response = await fetch("/api/user/auth", {
            method: "GET",
            credentials: "include" // 自動帶 cookie
        });
        const data = await response.json();

        if (!response.ok) {
            console.log("取得使用者資料失敗:", data.message);
            return false;
        }else{
            console.log(data)
            useremail=data.data.email;
            usernameInput.value = useremail;
            passwordLittleTitle.style.display = "none";
            passwordInput.style.display = "none";
            loginButton.style.display = "none";
            logoutButton.style.display = "block";
        }    
        
        return data.data;
    } catch (err) {
        console.error("取得使用者資料錯誤:", err);
        return false;
    }
}
// ======= Login function =======
async function login(){ 
    loginButton.addEventListener("click", async () => {
        errorMessage.style.display = "none";
        const email = usernameInput.value.trim();
        const password = passwordInput.value.trim();

        // 驗證輸入
        if (!email) {
            errorMessage.textContent = "帳號不得空白";
            errorMessage.style.display = "block";
            return;
        }
        if (!password) {
            errorMessage.textContent = "密碼不得空白";
            errorMessage.style.display = "block";
            return;
        }
        if (!checkAccountFormat(email)) {
            errorMessage.textContent = "帳號Email格式錯誤";
            errorMessage.style.display = "block";
            return;
        }
        if (!checkPasswordFormat(password)) {
            errorMessage.textContent = "密碼格式錯誤，數字或字母，至少八個字";
            errorMessage.style.display = "block";
            return;
        }

        try {
            const response = await fetch("/api/user/auth", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ email, password }),
                credentials: "include"
            });

            const data = await response.json();

            if (!response.ok) {
                errorMessage.textContent = "登入失敗，請輸入正確帳號密碼";
                errorMessage.style.display = "block";
                passwordInput.value = "";
                console.error(response.status, data.message);
                return;
            }


            
            const user = await getUserData();
            if (user) {
                loginButton.style.display = "none";
                logoutButton.style.display = "block";
                
            }

        } catch (err) {
            console.error("登入請求錯誤:", err);
            errorMessage.textContent = "登入發生錯誤，請稍後再試";
            errorMessage.style.display = "block";
        }
    });
}


// ======= Logout function =======
async function logout() {
    if (logoutButton) {
        logoutButton.addEventListener("click", async () => {
            try {
                errorMessage.style.display = "none";
                await fetch("/api/user/logout", {
                    method: "POST",
                    credentials: "include"
                });
            } catch (err) {
                console.error("登出失敗:", err);
            } finally {
                window.location.reload();
            }
        });
    }
}





async function excute(){
    getUserData()
    login();
    logout();
    monitorUserIconClicks();
    initializeHamburgerMenu();
    initializeFooterLinks();
}
window.addEventListener("DOMContentLoaded", excute);