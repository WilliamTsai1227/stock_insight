

let page = 1;
let isLoading = false; // Create a label to indicate whether data is loading
let keyword = "";
let industry = "";
let is_summary = false
let startTime = Math.floor(Date.now() / 1000);//現在時間轉換為 Unix timestamp（秒）
let endTime = Math.floor(new Date("2020-01-01T00:00:00Z").getTime() / 1000);// "2020-01-01 00:00:00" 轉換為 Unix timestamp（秒）

async function loadAllAIAnalysis(){
    try {
        if (isLoading) return; // If data is being loaded, the load operation is not triggered
        isLoading = true; // Start loading data, set isLoading to true
        console.log(`fetch startTime:${startTime}, endTime: ${endTime}`)
        const response = await fetch(`http://0.0.0.0:8000/api/ai_news?keyword=${keyword}&industry=${industry}&is_summary=${is_summary}&startTime=${startTime}&endTime=${endTime}&page=${page}`);
        const result = await response.json();
        page = result.nextPage;
        const dataList = result.data;

        const container = document.querySelector(".container");

        dataList.forEach(item => {
            const block = document.createElement("div");
            block.className = "block";

            //Establish a creation time block
            const publishAtDiv = document.createElement("div");
            publishAtDiv.className = "publishAtDiv";
            const timestamp = item.publishAt; // Unix timestamp（以秒為單位）
            const date = new Date(timestamp * 1000); // 轉成毫秒

            const taiwanTime = date.toLocaleString("zh-TW", {
            timeZone: "Asia/Taipei",
            });
            publishAtDiv.textContent = taiwanTime;
            block.appendChild(publishAtDiv);

            // --- 包裹後面四個區塊的容器 ---
            const blockContent = document.createElement("div");
            blockContent.className = "block-content";


            // --- 1. Stock List Section ---
            const listSection = document.createElement("div");
            listSection.className = "section list-section";

            const stockListBigTitle = document.createElement("div");
            stockListBigTitle.textContent = "潛力股票";
            stockListBigTitle.className = "section-title";
            listSection.appendChild(stockListBigTitle);

            item.stock_list.forEach(stock => {
                const div = document.createElement("div");
                div.className = "stock-list-item";
                div.textContent = stock[2];
                const span = document.createElement("span");
                span.className = "stock-list-item-code";
                const firstTwo = stock.slice(0, 2); // 取第 0 和第 1 個元素
                span.textContent = firstTwo.join(",");  // 例如："2330,TSMC"
                div.appendChild(span);
                const [market, number] = firstTwo;
                const tooltip = document.createElement('div');
                tooltip.className = 'stock-tooltip';
                tooltip.textContent = `股票代碼：${market} ${number}`;
                div.appendChild(tooltip);
                listSection.appendChild(div);
            });

            const industryListBigTitle = document.createElement("div");
            industryListBigTitle.textContent = "潛力產業";
            industryListBigTitle.className = "section-title";
            listSection.appendChild(industryListBigTitle);

            item.industry_list.forEach(ind => {
                const div = document.createElement("div");
                div.className = "industry-list-item";
                div.textContent = ind;
                listSection.appendChild(div);
            });

            blockContent.appendChild(listSection);

            // --- 2. Potential Stocks and Industries ---
            const potentialSection = document.createElement("div");
            potentialSection.className = "section potential-stocks";

            const potentialBigTitle = document.createElement("div");
            potentialBigTitle.textContent = "股票＆產業分析";
            potentialBigTitle.className = "section-title";
            potentialSection.appendChild(potentialBigTitle);

            const potentialContentDiv= document.createElement("div");
            potentialContentDiv.className = "potential-content";
                        
            const lines = item.potential_stocks_and_industries.split('\n');// 使用 \n 拆分文字

            // 每一行都創建文字節點和 <br>
            lines.forEach((line, index) => {
                potentialContentDiv.appendChild(document.createTextNode(line));
                if (index < lines.length - 1) {
                    potentialContentDiv.appendChild(document.createElement("br"));
                    potentialContentDiv.appendChild(document.createElement("br"));
                }
            });
            potentialSection.appendChild(potentialContentDiv);

            const arrowPotential = document.createElementNS("http://www.w3.org/2000/svg", "svg");
            arrowPotential.classList.add("arrow-left");
            arrowPotential.setAttribute("viewBox", "0 0 20 20");
            

            const polygonPotential = document.createElementNS("http://www.w3.org/2000/svg", "polygon");
            polygonPotential.setAttribute("points", "19,9 9,14 19,19");
            polygonPotential.setAttribute("fill", "#000");

            arrowPotential.appendChild(polygonPotential);
            potentialSection.appendChild(arrowPotential);

            blockContent.appendChild(potentialSection);


            // --- 3. AI Summary Section ---
            const aiSection = document.createElement("div");
            aiSection.className = "section ai-summary";

            const aiBigTitle = document.createElement("div");
            aiBigTitle.textContent = "AI 重點整理";
            aiBigTitle.className = "section-title";
            aiSection.appendChild(aiBigTitle);

            const aiSectionDiv = document.createElement("div"); 

            const summaryTitle = document.createElement("div");
            summaryTitle.textContent = "新聞重點: ";
            summaryTitle.className = "news-summary";
            const summaryContent = document.createElement("div");
            summaryContent.textContent = item.summary;
            summaryContent.className = "news-summary-content";
            aiSectionDiv.appendChild(summaryTitle);
            aiSectionDiv.appendChild(summaryContent);
            
            const keyNewsTitle = document.createElement("div");
            keyNewsTitle.textContent = "重點新聞: ";
            keyNewsTitle.className = "key-news";
            const keyNewsContent = document.createElement("div");
            keyNewsContent.className = "key-news-content";
            const importantNewsLines = item.important_news.split('\n');// 使用 \n 拆分文字

            // 每一行都創建文字節點和 <br>
            lines.forEach((importantNewsLines, index) => {
                keyNewsContent.appendChild(document.createTextNode(importantNewsLines));
                if (index < lines.length - 1) {
                    keyNewsContent.appendChild(document.createElement("br"));
                    keyNewsContent.appendChild(document.createElement("br"));
                }
            });
            aiSectionDiv.appendChild(keyNewsTitle);
            aiSectionDiv.appendChild(keyNewsContent);

            const sentimentTitle = document.createElement("div");
            sentimentTitle.textContent = "情緒分析: " ;
            sentimentTitle.className = "sentiment-analysis";
            const sentimentContent = document.createElement("div");
            sentimentContent.textContent = item.sentiment;
            sentimentContent.className = "sentiment-analysis-content";
            aiSectionDiv.appendChild(sentimentTitle);
            aiSectionDiv.appendChild(sentimentContent);

            aiSection.appendChild(aiSectionDiv);

            const arrowAI = document.createElementNS("http://www.w3.org/2000/svg", "svg");
            arrowAI.classList.add("arrow-left");
            arrowAI.setAttribute("viewBox", "0 0 20 20");

            const polygonAI = document.createElementNS("http://www.w3.org/2000/svg", "polygon");
            polygonAI.setAttribute("points", "18,8 8,13 18,18");
            polygonAI.setAttribute("fill", "#000");

            arrowAI.appendChild(polygonAI);
            aiSection.appendChild(arrowAI);

            blockContent.appendChild(aiSection);


            // --- 4. source_news - news items ---
            const newsSection = document.createElement("div");
            newsSection.className = "section news-section";
            const newsBigTitle = document.createElement("div");
            newsBigTitle.textContent = "原始新聞";
            newsBigTitle.className = "section-title"
            newsSection.appendChild(newsBigTitle);

            item.source_news.forEach(news => {
                const newsDiv = document.createElement("div");
                newsDiv.className = "news-item";
                newsDiv.textContent = news.title;

                // hidden _id span
                const idSpan = document.createElement("span");
                idSpan.textContent = item._id;
                idSpan.className = "news-item-id";
                newsDiv.appendChild(idSpan);

                // arrow
                const arrow = document.createElementNS("http://www.w3.org/2000/svg", "svg");
                arrow.classList.add("arrow-left");
                arrow.setAttribute("viewBox", "0 0 20 20");

                const polygon = document.createElementNS("http://www.w3.org/2000/svg", "polygon");
                polygon.setAttribute("points", "18,8 8,13 18,18");
                polygon.setAttribute("fill", "#000");

                arrow.appendChild(polygon);
                newsDiv.appendChild(arrow);
                newsSection.appendChild(newsDiv);
                blockContent.appendChild(newsSection);
            });
            block.appendChild(blockContent);
            // 將整個 block 加入 container
            container.appendChild(block);
        });
        isLoading = false; // Data loading is complete, set isLoading to false
    } catch (error) {
        console.error("Error fetching AI news:", error);
        isLoading = false; // Data loading error, set isLoading to false
    }
}

function scrollingAddAIAnalysis(){
    let footer = document.querySelector(".footer");
    window.addEventListener("scroll", function () {
      const { bottom } = footer.getBoundingClientRect();
      const windowHeight = window.innerHeight || document.documentElement.clientHeight;
      if (bottom <= windowHeight) {
        if (page != null){
            loadAllAIAnalysis();
        }
      }
    });
}

function search(){
    let button = document.querySelector(".search_icon");
    let input = document.querySelector(".search-bar");
    let container = document.querySelector(".container");


    button.addEventListener("click",async () => {
        const startDateInput = document.querySelector('.start-time-calendar');
        const startDateValue = startDateInput.value; // 格式是 "YYYY-MM-DD"
        const endDateInput = document.querySelector('.end-time-calendar');
        const endDateValue = endDateInput.value; // 格式是 "YYYY-MM-DD"
        if (startDateValue !== "") {
            startTime = Math.floor(new Date(startDateValue).getTime() / 1000);
        }
        
        if (endDateValue !== "") {
            endTime = Math.floor(new Date(endDateValue).getTime() / 1000);
        }
        console.log(startTime,endTime)
        page = 1;
        keyword = input.value;
        while(container.firstChild){
            container.removeChild(container.firstChild);
        }
        await loadAllAIAnalysis();
    })
}

// function monitorStockClicks(){
//     let listItems = document.querySelectorAll(".stock-list-item");
//     let id = 0;
//     listItems.forEach(item => {
//         item.addEventListener("click", () =>{
//             id = item.querySelector(".attraction_id").textContent;
//             window.location.href = `https://taipeitrips.com/attraction/${id}`;
//         })
//     })
// }





async function excute(){
    loadAllAIAnalysis();
    scrollingAddAIAnalysis();
    search()
}
excute();