let loadedCount = 0; // 已載入的資料數量
const limit = 20;
const sortOrder = -1; // 想從最新的log開始，尚未使用次參數，可之後再前端設立按鈕決定要最新的log看或從最舊的log看起，請參照對應後端API

// 取得今天本地時間的 00:00
const now = new Date();
const localMidnight = new Date(now.getFullYear(), now.getMonth(), now.getDate());
// 轉成 UNIX timestamp（秒）
const dateTs = Math.floor(localMidnight.getTime() / 1000);

function loadAIHeadlineNewsError() {
  fetch(`/api/log/ai_headline_news_error?date_ts=${dateTs}&skip=${loadedCount}&limit=${limit}`)
    .then(res => res.json())
    .then(data => {
      if (data.length > 0) {
        console.log("本次取得", data.length, "筆資料");
        loadedCount += data.length; // 更新 skip 計數器
        // 將資料加到畫面上
        appendToUI(data);
      } else {
        console.log("已經沒有更多資料了");
        // 可選：禁用載入按鈕或停止 infinite scroll
      }
    });
}

