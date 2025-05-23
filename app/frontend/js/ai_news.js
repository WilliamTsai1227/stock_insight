function scrollingAddAttractions(){
    let footer = document.querySelector(".footer");
    window.addEventListener("scroll", function () {
      const { bottom } = footer.getBoundingClientRect();
      const windowHeight = window.innerHeight || document.documentElement.clientHeight;
      if (bottom <= windowHeight) {
        if (page != null){
            fetchAttractions();
        }
      }
    });
}


function search(){
    let button = document.querySelector(".hero_section_search_icon");
    let input = document.querySelector(".hero_section_search input");
    let attractions = document.querySelector(".attractions");
    button.addEventListener("click",async () => {
        page = 0;
        keyword = input.value;
        while(attractions.firstChild){
            attractions.removeChild(attractions.firstChild);
        }
        await fetchAttractions();
    })
}

function monitorMrtClick(){
    let listItems = document.querySelectorAll(".list_item");
    let input = document.querySelector(".hero_section_search input");
    let attractions = document.querySelector(".attractions");
    listItems.forEach(item => {
        item.addEventListener("click",() => {
            let searchInput = item.textContent;
            input.value = searchInput;
            page = 0;
            keyword = input.value;
            while(attractions.firstChild){
                attractions.removeChild(attractions.firstChild);
            }
            fetchAttractions();
        })
    })    
}

function monitorAttractionClicks(){
    let listItems = document.querySelectorAll(".attraction_content");
    let id = 0;
    listItems.forEach(item => {
        item.addEventListener("click", () =>{
            id = item.querySelector(".attraction_id").textContent;
            window.location.href = `https://taipeitrips.com/attraction/${id}`;
        })
    })
}


document.addEventListener("DOMContentLoaded", async () => {
    try {
        const response = await fetch("http://0.0.0.0:8000/api/ai_news");
        const result = await response.json();
        const dataList = result.data;

        const container = document.querySelector(".container");

        dataList.forEach(item => {
            const block = document.createElement("div");
            block.className = "block";

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

            block.appendChild(listSection);

            // --- 2. Potential Stocks and Industries ---
            const potentialSection = document.createElement("div");
            potentialSection.className = "section potential-stocks";

            const potentialBigTitle = document.createElement("div");
            potentialBigTitle.textContent = "股票＆產業分析";
            potentialBigTitle.className = "section-title";
            potentialSection.appendChild(potentialBigTitle);

            const p = document.createElement("p");
            p.textContent = item.potential_stocks_and_industries;
            potentialSection.appendChild(p);

            const arrowPotential = document.createElementNS("http://www.w3.org/2000/svg", "svg");
            arrowPotential.classList.add("arrow-left");
            arrowPotential.setAttribute("viewBox", "0 0 20 20");

            const polygonPotential = document.createElementNS("http://www.w3.org/2000/svg", "polygon");
            polygonPotential.setAttribute("points", "15,5 5,10 15,15");
            polygonPotential.setAttribute("fill", "#000");

            arrowPotential.appendChild(polygonPotential);
            potentialSection.appendChild(arrowPotential);

            block.appendChild(potentialSection);


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
            keyNewsContent.textContent = item.important_news;
            keyNewsContent.className = "key-news-content";
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
            polygonAI.setAttribute("points", "15,5 5,10 15,15");
            polygonAI.setAttribute("fill", "#000");

            arrowAI.appendChild(polygonAI);
            aiSection.appendChild(arrowAI);

            block.appendChild(aiSection);


            // --- 4. source_news - news items ---
            const newsSection = document.createElement("div");
            newsSection.className = "section news-section";
            const newsBigTitle = document.createElement("div");
            newsBigTitle.textContent = "News";
            newsBigTitle.className = "section-title"
            newsSection.appendChild(newsBigTitle);

            item.source_news.forEach(news => {
                const newsDiv = document.createElement("div");
                newsDiv.className = "news-item";
                newsDiv.textContent = news.title;

                // hidden _id span
                const idSpan = document.createElement("span");
                idSpan.textContent = item._id;
                idSpan.style.display = "none";
                newsDiv.appendChild(idSpan);

                // arrow
                const arrow = document.createElementNS("http://www.w3.org/2000/svg", "svg");
                arrow.classList.add("arrow-left");
                arrow.setAttribute("viewBox", "0 0 20 20");

                const polygon = document.createElementNS("http://www.w3.org/2000/svg", "polygon");
                polygon.setAttribute("points", "15,5 5,10 15,15");
                polygon.setAttribute("fill", "#000");

                arrow.appendChild(polygon);
                newsDiv.appendChild(arrow);
                newsSection.appendChild(newsDiv);
                block.appendChild(newsSection);
            });

            // 將整個 block 加入 container
            container.appendChild(block);
        });
    } catch (error) {
        console.error("Error fetching AI news:", error);
    }
});






async function excute(){

}
excute();