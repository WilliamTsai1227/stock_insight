async function loadNews(){
    // 從網址中取得 news_id（例如 /news/5992746）
    const pathParts = window.location.pathname.split("/");
    const newsId = pathParts[pathParts.length - 1];
  
    try {
      const response = await fetch(`/api/news/${newsId}`);
      if (!response.ok) {
        throw new Error("無法取得新聞資料");
      }
  
      const data = await response.json();
      const news = data.data;

      document.title = news.title; //動態改變html <head> 裡面 title

      // 動態填入網頁內容
      document.getElementById("title").textContent = news.title;
      document.getElementById("publish-time").textContent = formatTimestamp(news.publishAt);
      document.getElementById("source-content").textContent = news.source;
      document.getElementById("source-news-url").href = news.url;
      document.getElementById("source-news-url").textContent = "查看原文";

      //Process summary line breaks and insert 
      const summaryContent = news.summary || '';
      const summaryLines = summaryContent.split('。');
      
      const summaryDiv = document.getElementById("summary-content");
      summaryDiv.textContent = ''; // Clear original content
      
      summaryLines.forEach((line, index) => {
          if (line.trim() !== '') {
              summaryDiv.appendChild(document.createTextNode(line + '。'));
              summaryDiv.appendChild(document.createElement("br")); // Add a line break to each sentence
          }
      });
      

      //Process news content line breaks and insert 
      const newsContent = news.content || ''; // Make sure it is a string
      const lines = newsContent.split('\n');  // Use \n to separate lines
      
      const newsContentDiv = document.getElementById("news-content");
      
      newsContentDiv.textContent = '';// Clear original content
      
      // Insert each line of text and line break
      lines.forEach((line, index) => {
          newsContentDiv.appendChild(document.createTextNode(line));
          if (index < lines.length - 1) {
              newsContentDiv.appendChild(document.createElement("br"));
              newsContentDiv.appendChild(document.createElement("br")); //Double line break
          }
      });
  
      // 顯示相關股票（如果有）
      const marketList = document.getElementById("market");
      if (news.market && news.market.length > 0) {
        news.market.forEach(stock => {
          const li = document.createElement("li");
          li.textContent = `${stock.name} (${stock.code})`;
          li.className = "related-stocks";
          marketList.appendChild(li);
        });
      }
  
    } catch (error) {
      console.error("錯誤：", error);
      // 安全地顯示錯誤訊息
      while (document.body.firstChild) document.body.removeChild(document.body.firstChild);
      const h2 = document.createElement('h2');
      h2.textContent = '無法載入新聞內容。';
      document.body.appendChild(h2);
    }
  };
  
function formatTimestamp(unixTime) {
  const date = new Date(unixTime * 1000);
  return date.toLocaleString("zh-TW", { timeZone: "Asia/Taipei" });
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
    loadNews();
    initializeHamburgerMenu()
}
excute();