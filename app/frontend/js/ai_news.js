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

            // --- 1. source_news - news items ---
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

                block.appendChild(newsDiv);
            });

            // --- 2. AI Summary Section ---
            const aiSection = document.createElement("div");
            aiSection.className = "section ai-summary";

            const h3AI = document.createElement("h3");
            h3AI.textContent = "AI Summary";
            aiSection.appendChild(h3AI);

            const ol = document.createElement("ol");

            const li1 = document.createElement("li");
            li1.textContent = "News Summary: " + item.summary;
            ol.appendChild(li1);

            const li2 = document.createElement("li");
            li2.textContent = "Key News Highlights: " + item.important_news;
            ol.appendChild(li2);

            const li3 = document.createElement("li");
            li3.textContent = "Sentiment Analysis: " + item.sentiment;
            ol.appendChild(li3);

            aiSection.appendChild(ol);

            const arrowAI = document.createElementNS("http://www.w3.org/2000/svg", "svg");
            arrowAI.classList.add("arrow-left");
            arrowAI.setAttribute("viewBox", "0 0 20 20");

            const polygonAI = document.createElementNS("http://www.w3.org/2000/svg", "polygon");
            polygonAI.setAttribute("points", "15,5 5,10 15,15");
            polygonAI.setAttribute("fill", "#000");

            arrowAI.appendChild(polygonAI);
            aiSection.appendChild(arrowAI);

            block.appendChild(aiSection);

            // --- 3. Potential Stocks and Industries ---
            const potentialSection = document.createElement("div");
            potentialSection.className = "section potential-stocks";

            const h3Potential = document.createElement("h3");
            h3Potential.textContent = "Potential Stocks and Industry Details";
            potentialSection.appendChild(h3Potential);

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

            // --- 4. List Section ---
            const listSection = document.createElement("div");
            listSection.className = "section list-section";

            const h3Stock = document.createElement("h3");
            h3Stock.textContent = "Stock List";
            listSection.appendChild(h3Stock);

            item.stock_list.forEach(stock => {
                const div = document.createElement("div");
                div.className = "list-item";
                div.textContent = stock;
                listSection.appendChild(div);
            });

            const h3Industry = document.createElement("h3");
            h3Industry.textContent = "Industry List";
            listSection.appendChild(h3Industry);

            item.industry_list.forEach(ind => {
                const div = document.createElement("div");
                div.className = "list-item";
                div.textContent = ind;
                listSection.appendChild(div);
            });

            block.appendChild(listSection);

            // 將整個 block 加入 container
            container.appendChild(block);
        });
    } catch (error) {
        console.error("Error fetching AI news:", error);
    }
});






async function excute(){
    scrollingAddAttractions();
    search();
    monitorMrtClick();
    monitorAttractionClicks();
}
excute();