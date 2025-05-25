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
      document.getElementById("summary").textContent = news.summary;
      document.getElementById("content").textContent = news.content;
      document.getElementById("publishAt").textContent = formatTimestamp(news.publishAt);
      document.getElementById("source").textContent = news.source;
      document.getElementById("newsUrl").href = news.url;
      document.getElementById("newsUrl").textContent = "查看原文";
  
      // 顯示相關股票（如果有）
      const marketList = document.getElementById("market");
      if (news.market && news.market.length > 0) {
        news.market.forEach(stock => {
          const li = document.createElement("li");
          li.textContent = `${stock.name} (${stock.code})`;
          marketList.appendChild(li);
        });
      }
  
    } catch (error) {
      console.error("錯誤：", error);
      document.body.innerHTML = "<h2>無法載入新聞內容。</h2>";
    }
  };
  
  function formatTimestamp(unixTime) {
    const date = new Date(unixTime * 1000);
    return date.toLocaleString("zh-TW", { timeZone: "Asia/Taipei" });
  }
  
async function excute(){
    loadNews();
}
excute();