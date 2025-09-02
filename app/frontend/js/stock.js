let myChart = null; // 全域唯一 Chart 實例
let loadingIndicator = document.getElementById("loading-indicator");
let stockSymbol = "";
let country = "tw";

// 定義財報欄位的中文名稱、顯示順序和固定顏色
const REPORT_FIELD_MAP = {
    cash_flow: {
        title: '現金流量表',
        fields: [
            { key: 'operating_cash_flow', label: '營業活動之現金流量 (營業現金流)', color: '#4CAF50' }, // Green
            { key: 'investing_cash_flow', label: '投資活動之現金流量 (投資現金流)', color: '#FFC107' }, // Amber
            { key: 'financing_cash_flow', label: '籌資活動之現金流量 (融資現金流)', color: '#2196F3' }, // Blue
            { key: 'free_cash_flow', label: '自由現金流量', color: '#9C27B0' }, // Purple
            { key: 'net_change_in_cash', label: '現金及約當現金淨變動 (淨現金流)', color: '#FF5722' }, // Deep Orange
            { key: 'depreciation', label: '折舊', color: '#607D8B' }, // Blue Grey
            { key: 'amortization', label: '攤銷', color: '#795548' }, // Brown
            { key: 'capital_expenditures', label: '資本支出', color: '#F44336' }, // Red
            { key: 'dividends_paid', label: '股利發放 (現金股利發放)', color: '#E91E63' }  // Pink
        ]
    },
    income_statements: {
        title: '損益表',
        fields: [
            { key: 'revenue', label: '營業收入', color: '#4CAF50' },
            { key: 'gross_profit', label: '營業毛利', color: '#FFC107' },
            { key: 'sales_expenses', label: '銷售費用', color: '#FFCDD2' }, // Red Light
            { key: 'administrative_expenses', label: '管理費用', color: '#B2DFDB' }, // Teal Light
            { key: 'research_and_development_expenses', label: '研發費用', color: '#C5CAE9' }, // Indigo Light
            { key: 'operating_expenses', label: '營業費用', color: '#B3E5FC' }, // Light Blue Light
            { key: 'operating_income', label: '營業利益', color: '#2196F3' },
            { key: 'pre_tax_income', label: '稅前淨利', color: '#9C27B0' },
            { key: 'net_income', label: '稅後淨利', color: '#FF5722' },
            { key: 'net_income_attributable_to_parent', label: '母公司業主淨利', color: '#607D8B' },
            { key: 'cost_of_revenue', label: '營業成本', color: '#FFEB3B' }, // Yellow
            { key: 'basic_eps', label: '基本每股盈餘 (EPS)', color: '#795548' },
            { key: 'diluted_eps', label: '稀釋每股盈餘', color: '#F44336' },
            { key: 'revenue_pct', label: '營業收入佔營收百分比', color: '#8BC34A' }, // Light Green
            { key: 'gross_profit_pct', label: '營業毛利佔營收百分比（毛利率）', color: '#E1BEE7' }, // Purple Light
            { key: 'sales_expenses_pct', label: '銷售費用佔營收百分比', color: '#F8BBD0' }, // Pink Light
            { key: 'administrative_expenses_pct', label: '管理費用佔營收百分比', color: '#D1C4E9' }, // Deep Purple Light
            { key: 'research_and_development_expenses_pct', label: '研發費用佔營收百分比', color: '#BBDEFB' }, // Blue Light
            { key: 'operating_expenses_pct', label: '營業費用佔營收百分比', color: '#C8E6C9' }, // Green Light
            { key: 'operating_income_pct', label: '營業利益佔營收百分比', color: '#FFF9C4' }, // Yellow Light
            { key: 'pre_tax_income_pct', label: '稅前淨利佔營收百分比', color: '#FCE4EC' }, // Pink Light
            { key: 'net_income_pct', label: '稅後淨利佔營收百分比', color: '#FFECB3' }, // Amber Light
            { key: 'net_income_attributable_to_parent_pct', label: '母公司業主淨利佔營收百分比', color: '#CFD8DC' }, // Blue Grey Light
            { key: 'cost_of_revenue_pct', label: '營業成本佔營收百分比', color: '#BBF0F3' } // Cyan Light
        ]
    },
    balance_sheets: {
        title: '資產負債表',
        fields: [
            { key: 'cash_and_equivalents', label: '現金及約當現金', color: '#4CAF50' },
            { key: 'short_term_investments', label: '短期投資', color: '#2196F3' },
            { key: 'accounts_receivable_and_notes', label: ' 應收帳款及票據', color: '#FF5722' },
            { key: 'inventory', label: '存貨', color: '#795548' },
            { key: 'other_current_assets', label: '其餘流動資產', color: '#8BC34A' }, // Light Green
            { key: 'current_assets', label: '流動資產', color: '#BBF0F3' }, // Cyan Light
            { key: 'fixed_assets_total', label: '固定資產', color: '#FFCDD2' }, // Red Light
            { key: 'other_non_current_assets', label: '其餘資產', color: '#B2DFDB' }, // Teal Light
            { key: 'total_assets', label: '總資產', color: '#E91E63' }, // Pink
            { key: 'cash_and_equivalents_pct', label: '現金及約當現金佔總資產百分比', color: '#FFC107' },
            { key: 'short_term_investments_pct', label: '短期投資佔總資產百分比', color: '#9C27B0' },
            { key: 'accounts_receivable_and_notes_pct', label: '應收帳款及票據佔總資產百分比', color: '#607D8B' },
            { key: 'inventory_pct', label: '存貨佔總資產百分比', color: '#F44336' },
            { key: 'other_current_assets_pct', label: '其餘流動資產佔總資產百分比', color: '#FFEB3B' }, // Yellow
            { key: 'current_assets_pct', label: '流動資產佔總資產百分比', color: '#E1BEE7' }, // Purple Light
            { key: 'fixed_assets_total_pct', label: '固定資產佔總資產百分比', color: '#F8BBD0' }, // Pink Light
            { key: 'other_non_current_assets_pct', label: '其餘資產 (主要指其他非流動資產)佔總資產百分比', color: '#D1C4E9' }, // Deep Purple Light
            { key: 'total_assets_pct', label: '總資產佔總資產百分比', color: '#BBDEFB' } // Blue Light
        ]
    }
};

const REPORT_EXPLAIN_MAP = {
    income_statements: [
        { title:"損益表",desc:"",more:"一、營收成長性及穩定性顯示企業競爭力。\n（景氣有起有落，建議連看三年以上，並與同業比較，若不論景氣，營收與營收成長率都比同業高，代表比同業更有競爭力。）\n二、毛利率穩定性反映企業對價格或生產效能的掌控力。\n三、推銷費用的合理性反應產品市場力。\n四、管理費用的合理性反映企業管理力。\n五、研發費用金額反應企業投資未來力度。\n六、獲利來源表現本業是否具備競爭力。\n七、稅後淨利或EPS是影響股價主因之一。\n八、股東權益報酬率（ROE)比EPS更能反映經營力。"},
        { title: "營業收入", desc: "公司主要來自本業的收入。", more: "指一家公司銷售商品與提供勞務的收入總額。" },
        { title: "營業毛利", desc: "營業收入 - 營業成本", more: "毛利可衡量產品或服務的基礎獲利能力，毛利越高代表價格與成本控制良好。\n毛利穩定性反映企業對價格或生產效能的掌控力。\n公司對價格有掌握能力時，當成本上揚時，可透過調漲價格維持毛利。\n具備以下特性之企業通常比較能夠維持毛利：\n1.具有產量、通路或專利明顯優勢者。\n2.具有品牌優勢者。\n3.具有技術優勢者。\n4.行業特性或對價格有所堅持的傳產業者。\n5.致力提升生產效能者。\n*請特別注意毛利原本穩定，但突然下滑情況。*" },
        { title: "銷售費用", desc: "推廣產品與服務所花費的成本。", more: "指一家公司為了推銷商品或勞務所花的費用，包含廣告、推廣、運費、業務人員薪資等，用於吸引與維持客戶。\n舉例：\n超商：店員薪資、門市租金與水電瓦斯等。\n車商：業務員薪資、展示室租金、招待客人的咖啡等。" },
        { title: "管理費用", desc: "企業日常行政與營運支出。", more: "指企業的行政管理部門為管理和組織經營所發生的各項費用。\n如管理部門、會計部門、人事部門、資訊部門等部門開支，反映經營效率與規模。\n還包括服務費用、訴訟費用等等。\n評估管理費用的合理性：\n1.跟規模相當的同業公司比較。2.跟本身公司過去年度的管理費用比較。" },
        { title: "研發費用", desc: "為投入於技術與產品創新的成本。\n*對於資本與技術密集產業需特別注意研發費用是否突增突減。*", more: "指企業為了投資未來，投入在新技術、新製程、新專利、新產品的研發支出。\n高研發費用通常出現在科技、製藥等創新導向產業。\n研發費用過高，會讓現階段無法獲利。研發費用過低，會影響未來成長與利潤。保持佔營收一定比例會是比較常見穩健做法。" },
        { title: "營業費用", desc: "營運間接成本的總和。", more: "營業費用包括三個主要項目：\n推銷費用、管理費用、研發費用。\n是營運成本控管的綜合指標。\n舉例：便利商店賣出一個便當，營業成本＝成產這個便當的成本。\n營業費用＝店員薪資、店租、水電費、總公司會計費用、人事費用、IT、總務等費用。" },
        { title: "營業利益", desc: "公司本業獲利能力的指標。", more: "等於營業毛利減營業費用，反映主營業務是否真正賺錢。" },
        { title: "稅前淨利", desc: "公司在繳稅前的總體獲利。", more: "包含本業與業外收入支出，是公司整體經營成果的初步反映。" },
        { title: "稅後淨利", desc: "公司最終可分配盈餘。", more: "為稅前淨利扣除所得稅後的淨收入，是投資人最關注的指標之一。" },
        { title: "母公司業主淨利", desc: "歸屬於母公司股東的稅後淨利。", more: "若公司擁有子公司，須扣除少數股東權益後才是母公司真正的盈餘。" },
        { title: "營業成本", desc: "公司為提供產品或服務所發生的直接成本。", more: "指一家公司銷售存貨與提供勞務所負擔的成本，包含原料、人工、製造費用（如水電費等）等，成本越低代表效率越高。" },
        { title: "基本每股盈餘 (EPS)", desc: "每一股可分配的稅後盈餘。（每股獲利能力）", more: "公司每一股稅後賺了多少錢。\nEPS 是衡量股東每股獲利的重要指標，也是估值的常用參數。" },
        { title: "稀釋每股盈餘", desc: "考慮潛在股數後的 EPS。", more: "包含可轉債、認股權等會稀釋股數的項目，更保守評估獲利。" },
        { title: "營業收入佔營收百分比", desc: "營業收入占總營收的比例。", more: "通常為100%，作為其他比例指標的基礎。" },
        { title: "營業毛利佔營收百分比(毛利率)", desc: "毛利率。\n計算方式: 毛利率 = (營業收入 - 營業成本) / 營業收入 × 100%", more: "毛利率越高，代表產品或服務獲利空間越大。\n毛利率穩定性反映企業對價格或生產效能的掌控力。" },
        { title: "銷售費用佔營收百分比", desc: "銷售費用占營業收入的比率。", more: "可衡量行銷與銷售的投入強度與效率。" },
        { title: "管理費用佔營收百分比", desc: "管理費用占營業收入的比率。", more: "可看出企業管理規模與控管能力。" },
        { title: "研發費用佔營收百分比", desc: "研發費用占營業收入的比率。", more: "研發費用占營收的比例，應有適度配置，不該忽高忽低，長期性來說，穩定配比會是比較穩定形式。" },
        { title: "營業費用佔營收百分比", desc: "總營業費用占營業收入的比率。", more: "可評估企業間接費用的總負擔，過高可能侵蝕獲利空間。" },
        { title: "營業利益佔營收百分比", desc: "營業利益占營業收入的比率。", more: "營業利益率越高，代表本業賺錢效率越好。" },
        { title: "稅前淨利佔營收百分比", desc: "稅前淨利占營業收入的比率。", more: "可評估公司整體經營成果與業外損益狀況。" },
        { title: "稅後淨利佔營收百分比", desc: "稅後淨利占營業收入的比率。", more: "稅後淨利率越高，代表公司最終獲利能力越強。" },
        { title: "母公司業主淨利佔營收百分比", desc: "母公司業主淨利占營業收入的比率。", more: "可反映股東真正能分配的盈餘佔比。" },
        { title: "營業成本佔營收百分比", desc: "營業成本占營業收入的比率。", more: "成本率越低代表成本控管越有效，有助提高毛利率。" }
      ],
      
      balance_sheets: [
        { title: "資產負債表",desc:"",more:""},
        { title: "現金及約當現金", desc: "可隨時動用的資金與高流動資產。", more: "如銀行存款、短期票券等，代表企業即時支付能力。" },
        { title: "短期投資", desc: "一年內可變現的投資項目。\n計算方式：（透過損益按公允價值衡量之金融資產－流動） ＋（備供出售金融資產－流動淨額）", more: "如短期債券、股票等，反映資金調度與閒置資金配置。" },
        { title: "應收帳款及票據", desc: "尚未收回的客戶貨款。", more: "比率高需注意收款風險與現金流壓力。" },
        { title: "存貨", desc: "公司持有的商品、原物料與在製品。", more: "過高代表銷售壓力或庫存積壓風險。" },
        { title: "其餘流動資產", desc: "其他一年內可變現的資產。", more: "如預付款項、待收款、應退稅等。" },
        { title: "流動資產", desc: "可以在一年或一個營業週期內，變換為現金的資產。\n原始財報項目：流動資產合計。", more: "高流動資產代表公司短期償債能力佳。" },
        { title: "固定資產", desc: "長期營運使用的實體資產。", more: "如廠房、機器、建築物，反映企業生產基礎與產能。" },
        { title: "其餘資產", desc: "非流動與非固定資產項目。", more: "如無形資產、長期投資等。" },
        { title: "總資產", desc: "企業在某一時間點擁有的全部資產。", more: "總資產規模常用於衡量公司體量與成長性。" },
        { title: "現金及約當現金佔總資產百分比", desc: "現金占總資產的比率。", more: "比率高代表資金調度靈活；太高可能代表資金未妥善運用。" },
        { title: "短期投資佔總資產百分比", desc: "短期投資占總資產的比率。", more: "可反映資金運用的彈性與配置效率。" },
        { title: "應收帳款及票據佔總資產百分比", desc: "應收帳款占總資產的比率。", more: "比率過高需注意逾期風險與資金周轉。" },
        { title: "存貨佔總資產百分比", desc: "存貨占總資產的比率。", more: "高存貨可能造成資金壓力與減值風險。" },
        { title: "其餘流動資產佔總資產百分比", desc: "其他流動資產占總資產的比率。", more: "幫助了解流動資產中的其他成分比例。" },
        { title: "流動資產佔總資產百分比", desc: "流動資產占總資產的比率。", more: "比例越高，代表公司短期償債與營運安全性越高。" },
        { title: "固定資產佔總資產百分比", desc: "固定資產占總資產的比率。", more: "比率高通常見於重資本產業，代表資產密集程度。" },
        { title: "其餘資產佔總資產百分比", desc: "其他非流動資產占總資產的比率。", more: "觀察長期投資與無形資產配置是否合理。" },
        { title: "總資產佔總資產百分比", desc: "總資產占比基準。", more: "固定為100%，作為各項目占比的參考基礎。" }
      ],
      
      cash_flow: [
        {title: "現金流量表",desc:"",more:" 1.了解這家公司的獲利品質是否良好 \n2.獲利品質好的公司，可以從「營業活動之現金流量 (營業現金流)」是否能產生穩定的現金流入看出來。\n3.對於獲利品質好的公司，可以從「自由現金流量」進而預測其股利的穩定性，甚至成長性。\n4.對於獲利品質好的公司，投資人可考慮是否要加碼。反之，投資人可考慮不是減碼，就是設定較低的本益比。"},
        {title: "營業活動之現金流量 (營業現金流)",desc: "反映公司本業帶來的現金流入與流出。",more: "營業活動其實就是「賺錢活動」，分析營業活動其實就在分析，企業從賺錢活動中「賺得多少現金」。\n獲利品質好的公司，可以從「營業活動之現金流量 (營業現金流)」是否能產生穩定的現金流入看出來。\n*為正代表本業有穩定現金收入；為負可能表示營運出現問題或資金壓力。*"},
        {title: "投資活動之現金流量 (投資現金流)",desc: "顯示公司在資本支出或資產處分上的現金流動。",more: "投資活動是指公司取得或處分不動產、廠房與設備，策略性投資，或理財性投資等活動的現金流入及流出。\n如購買設備、投資資產等，通常為負；若為正，可能是出售資產所得。"},
        {title: "籌資活動之現金流量 (融資現金流)",desc: "代表公司資金來源與還款的現金流動情況。",more: "籌資活動是指企業向股東拿錢、還股東錢以及舉借或償還借款的活動。\n向股東拿錢就是現金增資，還股東錢包括現金增資、買回自家股票（即庫藏股）及支付股息給股東。\n舉債或償還借款主要包括向金融機構借錢、還錢，發行或贖回公司債以及相關的利息支付。"},
        {title: "自由現金流量",desc: "公司扣除資本支出後，可自由運用的現金。",more: "自由現金流 = 營業現金流 − 資本支出，反映企業實際可投資或發放股利的能力。\n對於獲利品質好的公司，可以從自由現金流量進而預測其股利的穩定性，甚至成長性。"},
        {title: "現金及約當現金淨變動 (淨現金流)",desc: "期末與期初現金差額，總體現金流的結果。",more: "若為正，表示公司整體現金增加；為負則表示現金淨流出。"},
        {title: "折舊",desc: "固定資產因使用而逐年攤提的成本。",more: "如廠房、設備，雖不影響現金，但會影響盈餘與稅賦。"},
        {title: "攤銷",desc: "無形資產的成本分年攤提至損益表。",more: "如商譽、專利等，也屬非現金項目，影響會計利潤。"},
        {title: "資本支出",desc: "公司投資於固定資產所花費的金額。",more: "如購買廠房、機器等，是企業成長與擴張的指標。"},
        {title: "股利發放 (現金股利發放)",desc: "公司以現金形式回饋股東的盈餘分配。",more: "顯示公司獲利與對股東報酬的態度，過高可能影響現金留存。"}
      ]
};

function renderReportExplain(reportType) {
  const explainList = REPORT_EXPLAIN_MAP[reportType] || [];
  const container = document.getElementById('report-explain-section');
  container.textContent = '';
  explainList.forEach(item => {
    const block = document.createElement('div');
    block.className = 'explain-block';

    const h3 = document.createElement('h3');
    h3.textContent = item.title;
    block.appendChild(h3);

    // 處理 desc 換行
    const descDiv = document.createElement('div');
    descDiv.className = 'explain-block-desc';
    const descLines = (item.desc || '').split('\n');
    descLines.forEach((line, idx) => {
      descDiv.appendChild(document.createTextNode(line));
      if (idx !== descLines.length - 1) {
        descDiv.appendChild(document.createElement('br'));
      }
    });
    block.appendChild(descDiv);

    if (item.more) {
      const moreDiv = document.createElement('div');
      moreDiv.className = 'explain-more';
      const moreLines = (item.more || '').split('\n');
      moreLines.forEach((line, idx) => {
        moreDiv.appendChild(document.createTextNode(line));
        if (idx !== moreLines.length - 1) {
          moreDiv.appendChild(document.createElement('br'));
        }
      });
      block.appendChild(moreDiv);
    }
    container.appendChild(block);
  });
}

function switchReportTab(tab) {
  document.getElementById('tab-detail').classList.toggle('active', tab === 'detail');
  document.getElementById('tab-explain').classList.toggle('active', tab === 'explain');
  document.getElementById('report-detail-section').style.display = (tab === 'detail') ? '' : 'none';
  document.getElementById('report-explain-section').style.display = (tab === 'explain') ? '' : 'none';
}

// 初始化搜尋參數
function initSearchParamsFromURL() {
    const pathParts = window.location.pathname.split('/');
    stockSymbol = pathParts[2] || ""; // /stock/股票代碼/國家
    country = pathParts[3] || "tw";
}

// 設定搜尋框的值
function setSearchBarValue() {
    const searchBar = document.querySelector('.search-bar');
    if (searchBar) {
        searchBar.value = stockSymbol;
    }
}

// 更新 URL 參數
function updateURLParams() {
    const newUrl = `/stock/${stockSymbol}/${country}`;
    history.replaceState({}, '', newUrl);
}

// 載入股票資訊
async function loadStockInfo() {
    try {
        if (loadingIndicator) loadingIndicator.style.display = 'flex';
        // 清除前一次的內容
        document.getElementById('stock-header').textContent = '';
        document.getElementById('stock-info').textContent = '';
        
        const response = await fetch(`/api/stock_info?stock_symbol=${stockSymbol}&country=${country}`);
        
        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.detail || '載入股票時發生錯誤，請稍後再試。');
        }

        const responseData = await response.json();
        if (!responseData.data) {
            throw new Error('回傳資料格式不正確');
        }
        
        // 隱藏載入中
        if (loadingIndicator) loadingIndicator.style.display = 'none';
        
        // 顯示股票資訊
        displayStockInfo(responseData.data);
        // 新增：取得公司簡稱查詢新聞
        const abbreviation = responseData.data.abbreviation;
        if (abbreviation) {
            window._companyNewsKeyword = abbreviation;
            fetchCompanyNews(abbreviation, 1);
        } else {
            const newsSection = document.getElementById('related-news-section');
            if (newsSection) newsSection.querySelector('.related-news-list').textContent = '無法取得公司新聞';
        }
        // 新增：取得公司簡稱查詢分析
        if (abbreviation) {
            window._companyNewsKeyword = abbreviation;
            setupAIAnalysisToggle(abbreviation);
            fetchCompanyAIAnalysis(abbreviation, false, 1);
        } else {
            const aiSection = document.getElementById('stock-ai-analysis-section');
            if (aiSection) aiSection.querySelector('.ai-analysis-list').textContent = '無法取得分析結果';
        }
    } catch (error) {
        if (loadingIndicator) loadingIndicator.style.display = 'none';
        
        // 清除所有內容
        document.getElementById('stock-header').textContent = '';
        document.getElementById('stock-info').textContent = '';
        
        // 顯示錯誤訊息
        displayError(error.message);
        // 新增：錯誤時新聞區顯示
        const newsSection = document.getElementById('related-news-section');
        if (newsSection) newsSection.querySelector('.related-news-list').textContent = '無法取得公司新聞';
        // 新增：錯誤時分析區顯示
        const aiSection = document.getElementById('stock-ai-analysis-section');
        if (aiSection) aiSection.querySelector('.ai-analysis-list').textContent = '無法取得分析結果';
    }
}

// 顯示股票資訊
function displayStockInfo(data) {
    if (!data) {
        displayError("找不到股票資料");
        return;
    }

    // 顯示標題
    const stockHeader = document.getElementById('stock-header');
    stockHeader.textContent = ""; // 先清空
    const h1 = document.createElement("h1");
    h1.className = "stock-title";
    h1.textContent = `${data.company_name || '-'} (${data.stock_symbol || '-'}.${country})`;
    stockHeader.appendChild(h1);

    // 顯示詳細資訊
    const stockInfo = document.getElementById('stock-info');
    stockInfo.textContent = ""; // 先清空
    const table = document.createElement("table");
    table.className = "stock-info-table";

    // 建立每一行
    function addRow(th1, td1, th2, td2) {
        const tr = document.createElement("tr");
        const thEl1 = document.createElement("th");
        thEl1.textContent = th1;
        tr.appendChild(thEl1);
        const tdEl1 = document.createElement("td");
        tdEl1.textContent = td1;
        tr.appendChild(tdEl1);
        const thEl2 = document.createElement("th");
        thEl2.textContent = th2;
        tr.appendChild(thEl2);
        const tdEl2 = document.createElement("td");
        tdEl2.textContent = td2;
        tr.appendChild(tdEl2);
        table.appendChild(tr);
    }
    // colspan 3 欄位
    function addRowColspan(th, td) {
        const tr = document.createElement("tr");
        const thEl = document.createElement("th");
        thEl.textContent = th;
        tr.appendChild(thEl);
        const tdEl = document.createElement("td");
        tdEl.textContent = td;
        tdEl.colSpan = 3;
        tr.appendChild(tdEl);
        table.appendChild(tr);
    }
    // 網址欄位
    function addRowWebsite(th, url) {
        const tr = document.createElement("tr");
        const thEl = document.createElement("th");
        thEl.textContent = th;
        tr.appendChild(thEl);
    
        const tdEl = document.createElement("td");
        tdEl.colSpan = 3;
    
        if (url) {
            tdEl.textContent = url; // 直接顯示網址文字
        } else {
            tdEl.textContent = "-";
        }
        tr.appendChild(tdEl);
        table.appendChild(tr);
    }
    // 依序加入所有欄位
    addRow("公司簡稱", data.abbreviation || "-", "成立日期", data.founding_date || "-");
    addRow("上市日期", data.listed_date || "-", "上櫃日期", data.otc_listed_date || "-");
    addRow("市場", data.market || "-", "產業", data.sector_name || "-");
    addRowColspan("公司地址", data.address || "-");
    addRow("董事長", data.chairman || "-", "總經理", data.general_manager || "-");
    addRow("發言人", data.spokesperson || "-", "發言人職稱", data.spokesperson_title || "-");
    addRow("已發行普通股數", data.outstanding_common_shares?.toLocaleString() || "-", "私募普通股", data.private_placement_common_shares?.toLocaleString() || "-");
    addRow("特別股", data.preferred_shares?.toLocaleString() || "-", "簽證會計師事務所", data.accounting_firm || "-");
    addRow("簽證會計師1", data.accountant_1 || "-", "簽證會計師2", data.accountant_2 || "-");
    addRowWebsite("公司網址", data.website);
    addRow("普通股盈餘分派頻率", data.common_stock_dividend_frequency || "-", "現金股息決議層級", data.common_stock_dividend_decision_level || "-");
    addRowColspan("公司簡介", data.description || "-");
    stockInfo.appendChild(table);
}

// 顯示錯誤訊息
function displayError(message) {
    const stockInfo = document.getElementById('stock-info');
    const errorMessage = document.createElement('div');
    errorMessage.className = 'error-message';
    
    // 如果是 404 錯誤，只顯示找不到股票的部分
    if (message.includes("找不到股票代碼")) {
        const match = message.match(/找不到股票代碼.*?的資料/);
        if (match) {
            errorMessage.textContent = match[0];
        } else {
            errorMessage.textContent = message;
        }
    } else {
        errorMessage.textContent = message;
    }
    
    stockInfo.appendChild(errorMessage);
}

// 包裝財報查詢/繪圖為 function
async function loadFinancialReport(stockSymbol, country) {
    const API_BASE_URL = "/api/financial_report";
    let currentFinancialData = [];
    let currentOriginalCurrency = '';

    // 全域取得財報類型/期間
    function getReportType() {
        return document.getElementById('reportType')?.value || 'cash_flow';
    }
    function getReportPeriod() {
        return document.getElementById('reportPeriod')?.value || 'annual';
    }

    // 內部 function: 畫圖
    function drawChartBasedOnSelection() {
        if (currentFinancialData.length === 0) {
            if (myChart) {
                myChart.destroy();
                myChart = null;
            }
            return;
        }

        const reportType = getReportType();
        const reportPeriod = getReportPeriod();
        
        // 根據選擇的期間調整標籤
        let labels;
        if (reportPeriod === 'annual') {
            labels = currentFinancialData.map(d => `${d.year}`);
        } else {
            labels = currentFinancialData.map(d => `${d.year} Q${d.quarter}`);
        }
        
        const allFields = REPORT_FIELD_MAP[reportType].fields;

        // 取得所有被勾選的指標鍵值
        const selectedMetricKeys = Array.from(document.querySelectorAll('input[name="chartMetric"]:checked'))
                                        .map(checkbox => checkbox.value);

        // 構建 Chart.js 的 datasets，只包含被勾選的項目
        const datasets = allFields.filter(field => {
            const isChartable = !field.key.includes('_pct') && field.key !== 'report_date';
            const isSelected = selectedMetricKeys.includes(field.key);
            return isChartable && isSelected;
        }).map(field => {
            return {
                label: field.label,
                data: currentFinancialData.map(d => d[field.key] !== null ? d[field.key] : NaN),
                borderColor: field.color,
                backgroundColor: field.color.replace('rgb', 'rgba').replace(')', ', 0.2)'),
                fill: false,
                tension: 0.1
            };
        });

        // 獲取所有「可繪製圖表」的指標，用於圖例顯示 (無論是否勾選)
        const legendDatasets = allFields.filter(field => {
            return !field.key.includes('_pct') && field.key !== 'report_date';
        }).map(field => ({
            key: field.key, // 新增 key 屬性以便在 onClick 中查找
            label: field.label,
            borderColor: field.color,
            backgroundColor: field.color.replace('rgb', 'rgba').replace(')', ', 0.2)')
        }));

        const ctx = document.getElementById('financialChart').getContext('2d');

        // 定義圖例的點擊事件處理器
        const legendOnClickHandler = function(e, legendItem, legend) {
            const datasetLabel = legendItem.text;
            const fieldKey = legendDatasets.find(d => d.label === datasetLabel)?.key;

            if (fieldKey) {
                const checkbox = document.querySelector(`input[name="chartMetric"][value="${fieldKey}"]`);
                if (checkbox) {
                    checkbox.checked = !checkbox.checked; // 反轉勾選狀態
                    // 觸發 change 事件，確保勾選框視覺更新並重新繪圖
                    checkbox.dispatchEvent(new Event('change')); 
                }
            }
        };

        // 定義圖例標籤的生成器
        const legendGenerateLabels = function(chart) {
            return legendDatasets.map((dataset, i) => {
                const hidden = !selectedMetricKeys.includes(dataset.key);
                
                return {
                    text: dataset.label,
                    fillStyle: dataset.backgroundColor,
                    strokeStyle: dataset.borderColor,
                    lineWidth: 1,
                    hidden: hidden,
                    datasetIndex: i
                };
            });
        };

        if (myChart) {
            // 如果圖表已存在，更新其數據和選項
            myChart.data.labels = labels;
            myChart.data.datasets = datasets; // 直接替換數據集為選中的
            myChart.options.plugins.title.text = `${REPORT_FIELD_MAP[reportType].title} - 指標趨勢 (${currentOriginalCurrency} 千元)`;
            myChart.options.animation.duration = 1000;
            // **核心修正：每次更新時，確保重新設定 generateLabels 函式**
            myChart.options.plugins.legend.labels.generateLabels = legendGenerateLabels;
            myChart.options.plugins.legend.labels.onClick = legendOnClickHandler; // 確保點擊處理器也更新
            myChart.update();
        } else {
            // 否則，創建一個新的圖表實例
            myChart = new Chart(ctx, {
                type: 'line',
                data: {
                    labels: labels,
                    datasets: datasets
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    animation: {
                        duration: 1000 // 1 秒動畫
                    },
                    scales: {
                        x: {
                            title: {
                                display: true,
                                text: '時間 (年/季度)'
                            }
                        },
                        y: {
                            title: {
                                display: true,
                                text: `金額 (${currentOriginalCurrency} 千元)`
                            },
                            beginAtZero: false // 根據數據調整起始點
                        }
                    },
                    plugins: {
                        tooltip: {
                            callbacks: {
                                label: function(context) {
                                    let label = context.dataset.label || '';
                                    if (label) {
                                        label += ': ';
                                    }
                                    if (context.parsed.y !== null && !isNaN(context.parsed.y)) {
                                        // 這裡假設後端提供的百分比數據就是 50 代表 50%
                                        if (context.dataset.label.includes('百分比')) { // 簡單判斷是否為百分比
                                            label += `${context.parsed.y.toFixed(2)}%`;
                                        } else {
                                            label += new Intl.NumberFormat('zh-TW', { style: 'decimal', minimumFractionDigits: 0, maximumFractionDigits: 0 }).format(context.parsed.y);
                                        }
                                    } else {
                                        label += 'N/A';
                                    }
                                    return label;
                                }
                            }
                        },
                        title: {
                            display: true,
                            text: `${REPORT_FIELD_MAP[reportType].title}${reportPeriod === 'annual' ? ' - 年報' : ' - 指標趨勢'} (${currentOriginalCurrency} 千元)`,
                            font: {
                                size: 18
                            }
                        },
                        legend: {
                            display: true,
                            position: 'top',
                            labels: {
                                generateLabels: legendGenerateLabels, // 使用定義好的生成器
                                onClick: legendOnClickHandler // 使用定義好的點擊處理器
                            }
                        }
                    }
                }
            });
        }
    }

    // 內部 function: 更新勾選框
    function updateChartOptions() {
        const reportType = getReportType();
        const checkboxContainer = document.getElementById('checkboxContainer');
        while (checkboxContainer.firstChild) {
            checkboxContainer.removeChild(checkboxContainer.firstChild);
        }
        const fields = REPORT_FIELD_MAP[reportType].fields;
        const chartableFields = fields.filter(field => {
            return !field.key.includes('_pct') && field.key !== 'report_date';
        });
        
        // 每次更新選項時，重新生成勾選框並綁定事件
        chartableFields.forEach(field => {
            const label = document.createElement('label');
            const checkbox = document.createElement('input');
            checkbox.type = 'checkbox';
            checkbox.value = field.key;
            checkbox.checked = true; // 預設全部勾選
            checkbox.name = 'chartMetric';
            // 點擊勾選框時直接更新圖表
            checkbox.onchange = drawChartBasedOnSelection; 
            
            label.appendChild(checkbox);
            label.appendChild(document.createTextNode(field.label));
            checkboxContainer.appendChild(label);
        });
    }

    // 內部 function: 建表
    function createTable(financialData, reportType, originalCurrency) {
        const tableContainer = document.getElementById('financialDataTable');
        const tableTitle = document.getElementById('tableTitle');
        const reportInfo = REPORT_FIELD_MAP[reportType];
        const reportPeriod = getReportPeriod();
        
        // 根據選擇的期間調整標題
        let periodText = '';
        if (reportPeriod === 'annual') {
            periodText = ' | 年報 (第四季累計)';
        } else if (reportPeriod === 'accumulated') {
            periodText = ' | 累計';
        } else if (reportPeriod === 'quarterly') {
            periodText = ' | 單季';
        }
        
        tableTitle.textContent = `${reportInfo.title}${periodText} | 原始幣別: ${originalCurrency} (單位: 千元)`;
        
        while (tableContainer.firstChild) {
            tableContainer.removeChild(tableContainer.firstChild);
        }
        const table = document.createElement('table');
        const thead = document.createElement('thead');
        const tbody = document.createElement('tbody');
        const headerRow = document.createElement('tr');
        headerRow.appendChild(createTextElement('th', '科目 / 時間'));
        financialData.forEach(data => {
            // 年報選項：只顯示年份，不顯示季度
            if (reportPeriod === 'annual') {
                headerRow.appendChild(createTextElement('th', `${data.year}`));
            } else {
                headerRow.appendChild(createTextElement('th', `${data.year} Q${data.quarter}`));
            }
        });
        thead.appendChild(headerRow);
        table.appendChild(thead);
        reportInfo.fields.forEach(field => {
            const row = document.createElement('tr');
            row.appendChild(createTextElement('td', field.label));
            financialData.forEach(data => {
                const cell = document.createElement('td');
                let value = data[field.key];
                if (value === null || value === undefined) {
                    cell.textContent = '-';
                } else if (field.key.includes('_pct')) {
                    // 百分比欄位：直接顯示後端傳來的數值並加上 '%'
                    // 假設後端已經是實際百分比數值 (例如 50 代表 50%)
                    cell.textContent = `${value.toFixed(2)}%`; 
                } else if (field.key.includes('eps')) {
                    // EPS 欄位，保留小數點後兩位
                    cell.textContent = value.toFixed(2);
                } else if (field.key === 'report_date') {
                    // 報告日期欄位，顯示為日期格式
                    cell.textContent = new Date(value).toLocaleDateString('zh-TW'); // 確保日期格式化
                } else {
                    // 其他數值欄位，格式化為千位分隔，不帶小數
                    cell.textContent = new Intl.NumberFormat('zh-TW', { style: 'decimal', minimumFractionDigits: 0, maximumFractionDigits: 0 }).format(value);
                }
                row.appendChild(cell);
            });
            tbody.appendChild(row);
        });
        table.appendChild(tbody);
        tableContainer.appendChild(table);
    }

    // 內部 function: 輔助
    function createTextElement(tag, textContent) {
        const element = document.createElement(tag);
        element.textContent = textContent;
        return element;
    }

    // 內部 function: 處理 reportType 變更
    // 這個函式會處理下拉選單的 disabled 狀態，並觸發數據載入和圖表更新
    function handleReportTypeChange() {
        const reportType = getReportType();
        const reportPeriodSelect = document.getElementById('reportPeriod');
        
        // 重置所有選項的 disabled 狀態
        reportPeriodSelect.options[0].disabled = false; // 累計可用
        reportPeriodSelect.options[1].disabled = false;  // 季報可用
        reportPeriodSelect.options[2].disabled = false;  // 年報可用
        
        if (reportType === 'cash_flow') {
            reportPeriodSelect.value = 'annual'; // 強制設為累計
            reportPeriodSelect.options[1].disabled = true;  // 季報禁用
        }
        else if (reportType === 'balance_sheets'){
            reportPeriodSelect.value = 'quarterly'; // 強制設為季報
            reportPeriodSelect.options[0].disabled = true; // 累計禁用
            reportPeriodSelect.options[2].disabled = true; // 年報禁用
        }
        else if (reportType === 'income_statements'){
            reportPeriodSelect.value = 'annual'; // 強制設為季報
        }

        updateChartOptions(); // 更新勾選框，因財報類型不同指標也不同
        fetchAndDrawChartAndTable(); // 重新獲取數據並繪圖/表
        // 新增：切回詳細數據分頁並載入解釋
        switchReportTab('detail');
        renderReportExplain(reportType);
    }

    // 內部 function: 查詢並畫圖/表
    // 這個函式負責向後端請求數據，並在獲取後調用繪圖和建表函式
    async function fetchAndDrawChartAndTable() {
        const reportType = getReportType();
        const reportPeriod = getReportPeriod();
        const loadingDiv = document.getElementById('loading');
        const errorDiv = document.getElementById('error');
        const financialDataTableDiv = document.getElementById('financialDataTable');
        const tableTitle = document.getElementById('tableTitle');

        loadingDiv.style.display = 'block';
        errorDiv.style.display = 'none';
        errorDiv.textContent = '';
        while (financialDataTableDiv.firstChild) {
            financialDataTableDiv.removeChild(financialDataTableDiv.firstChild);
        }
        tableTitle.textContent = '';

        try {
            // 年報選項：實際查詢累計資料，但只顯示第四季
            const actualReportPeriod = reportPeriod === 'annual' ? 'accumulated' : reportPeriod;
            
            const response = await fetch(`${API_BASE_URL}?stock_symbol=${stockSymbol}&country=${country}&report_type=${reportType}&report_period=${actualReportPeriod}`);
            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || `HTTP 錯誤：${response.status}`);
            }
            const data = await response.json();

            if (data.data && data.data.length > 0) {
                data.data.sort((a, b) => {
                    if (a.year !== b.year) return a.year - b.year;
                    return a.quarter - b.quarter;
                });
                
                // 如果是年報選項，只保留第四季的資料
                let filteredData = data.data;
                if (reportPeriod === 'annual') {
                    filteredData = data.data.filter(item => item.quarter === 4);
                }
                
                currentFinancialData = filteredData;
                currentOriginalCurrency = filteredData[0].original_currency;
                
                // 在數據載入成功後，才根據勾選狀態繪製圖表和建立表格
                drawChartBasedOnSelection(); 
                createTable(filteredData, reportType, currentOriginalCurrency);
            } else {
                errorDiv.textContent = '未找到相關財報資料。';
                errorDiv.style.display = 'block';
                if (myChart) {
                    myChart.destroy();
                    myChart = null;
                }
                currentFinancialData = [];
                currentOriginalCurrency = '';
            }
        } catch (error) {
            console.error('獲取財報資料失敗:', error);
            errorDiv.textContent = `載入資料時發生錯誤：${error.message || error}`;
            errorDiv.style.display = 'block';
            if (myChart) {
                myChart.destroy();
                myChart = null;
            }
            currentFinancialData = [];
            currentOriginalCurrency = '';
        } finally {
            loadingDiv.style.display = 'none';
        }
    }

    // 首次載入財報區塊時，先初始化下拉選單狀態
    handleReportTypeChange(); // 這會觸發 updateChartOptions 和 fetchAndDrawChartAndTable

    // 將內部函數暴露為全域以便 HTML 中呼叫
    window.handleReportTypeChange = handleReportTypeChange;
    window.fetchAndDrawChartAndTable = fetchAndDrawChartAndTable;
    window.drawChartBasedOnSelection = drawChartBasedOnSelection;
}

// 修改 performSearch 讓搜尋時同時查詢財報
async function performSearch() {
    const searchBar = document.querySelector('.search-bar');
    if (!searchBar) return;
    stockSymbol = searchBar.value.trim();
    if (stockSymbol) {
        updateURLParams();
        await loadStockInfo();
        // 每次重新搜尋股票時，都要重新載入財報圖表和數據
        await loadFinancialReport(stockSymbol, country);
    }
}

// 初始化搜尋功能
function initializeSearch() {
    const searchBar = document.querySelector('.search-bar');
    const searchIcon = document.querySelector('.search_icon');

    if (!searchBar || !searchIcon) {
        console.log('找不到搜索相關元素');
        return;
    }

    // 點擊搜索圖標時執行搜索
    searchIcon.addEventListener('click', performSearch);

    // 在搜索欄中按下 Enter 鍵時執行搜索
    searchBar.addEventListener('keypress', (event) => {
        if (event.key === 'Enter') {
            event.preventDefault();
            performSearch();
        }
    });
}

// 初始化漢堡選單功能
function initializeHamburgerMenu() {
    const hamburgerMenu = document.querySelector('.hamburger-menu');
    const navDropdown = document.querySelector('.nav-dropdown');
    const closeButton = document.querySelector('.hamburger-menu-close');

    if (!hamburgerMenu || !navDropdown) {
        console.log('找不到漢堡選單或導航下拉選單元素');
        return;
    }

    // 點擊漢堡選單時切換選單狀態
    hamburgerMenu.addEventListener('click', () => {
        navDropdown.classList.toggle('active');
    });

    // 點擊關閉按鈕時關閉選單
    if (closeButton) {
        closeButton.addEventListener('click', () => {
            navDropdown.classList.remove('active');
        });
    }

    // 點擊下拉選單中的連結時關閉選單
    const dropdownLinks = document.querySelectorAll('.nav-dropdown a');
    dropdownLinks.forEach(link => {
        link.addEventListener('click', () => {
            navDropdown.classList.remove('active');
        });
    });
}

// 頁面載入時執行初始化
document.addEventListener('DOMContentLoaded', async () => {
    initSearchParamsFromURL();
    setSearchBarValue();
    initializeHamburgerMenu();
    initializeSearch();
    if (stockSymbol) {
        await loadStockInfo();
        await loadFinancialReport(stockSymbol, country);
        await loadStockRankingSection();
    }
    // 頁面載入時預設載入損益表解釋
    renderReportExplain(getReportType());
});

// performSearch 也要載入 ranking 區塊
async function performSearch() {
    const searchBar = document.querySelector('.search-bar');
    if (!searchBar) return;
    stockSymbol = searchBar.value.trim();
    if (stockSymbol) {
        updateURLParams();
        await loadStockInfo();
        await loadFinancialReport(stockSymbol, country);
        await loadStockRankingSection();
    }
}

// ========== 股票財報排名區塊邏輯 ========== //
async function loadStockRankingSection() {
    const section = document.getElementById('stock-ranking-section');
    if (!section) return;
    while (section.firstChild) section.removeChild(section.firstChild);

    // 定義三個財報類型
    const rankingBlocks = [
        {
            key: 'cash_flow',
            title: '現金流量表',
            apiKey: 'cash_flow',
            reportTypes: [
                { value: 'annual', label: '年報' },
                { value: 'accumulated', label: '累計' }
            ],
            defaultReportType: 'annual',
            yearRange: [2016, 2025],
            defaultYear: 2024,
            quarters: [1, 2, 3, 4],
            defaultQuarter: 4
        },
        {
            key: 'income_statement',
            title: '損益表',
            apiKey: 'income_statement',
            reportTypes: [
                { value: 'annual', label: '年報' },
                { value: 'quarterly', label: '季報' },
                { value: 'accumulated', label: '累計' }
            ],
            defaultReportType: 'annual',
            yearRange: [2015, 2025],
            defaultYear: 2024,
            quarters: [1, 2, 3, 4],
            defaultQuarter: 4
        },
        {
            key: 'balance_sheet',
            title: '資產負債表',
            apiKey: 'balance_sheet',
            reportTypes: [
                { value: 'annual', label: '年報', disabled: true },
                { value: 'quarterly', label: '季報', disabled: false },
                { value: 'accumulated', label: '累計', disabled: true }
            ],
            defaultReportType: 'quarterly',
            yearRange: [2015, 2025],
            defaultYear: 2024,
            quarters: [1, 2, 3, 4],
            defaultQuarter: 4
        }
    ];

    // 指標解釋對應表（同前）
    const RANKING_EXPLAIN_MAP = {
        cash_flow: [
            { key: 'operating_cash_flow', title: '營業活動之現金流量 (營業現金流)', desc: '反映公司本業帶來的現金流入與流出。' },
            { key: 'free_cash_flow', title: '自由現金流量', desc: '公司扣除資本支出後，可自由運用的現金。' },
            { key: 'net_change_in_cash', title: '現金及約當現金淨變動 (淨現金流)', desc: '期末與期初現金差額，總體現金流的結果。' }
        ],
        income_statement: [
            { key: 'revenue', title: '營業收入', desc: '公司主要來自本業的收入。' },
            { key: 'gross_profit', title: '營業毛利', desc: '營業收入 - 營業成本' },
            { key: 'operating_expenses', title: '營業費用', desc: '營運間接成本的總和。' },
            { key: 'operating_income', title: '營業利益', desc: '公司本業獲利能力的指標。' },
            { key: 'net_income', title: '稅後淨利', desc: '公司最終可分配盈餘。' },
            { key: 'gross_profit_pct', title: '營業毛利佔營業收入百分比', desc: '毛利率。' },
            { key: 'sales_expenses_pct', title: '銷售費用佔營業收入百分比', desc: '行銷與銷售的投入強度。' },
            { key: 'administrative_expenses_pct', title: '管理費用佔營業收入百分比', desc: '企業管理規模與控管能力。' },
            { key: 'research_and_development_expenses_pct', title: '研發費用佔營業收入百分比', desc: '研發費用占營收的比例。' },
            { key: 'operating_expenses_pct', title: '營業費用佔營業收入百分比', desc: '企業間接費用的總負擔。' },
            { key: 'operating_income_pct', title: '營業利益佔營業收入百分比', desc: '本業賺錢效率。' },
            { key: 'net_income_pct', title: '稅後淨利佔營業收入百分比', desc: '公司最終獲利能力。' },
            { key: 'cost_of_revenue_pct', title: '營業成本佔營業收入百分比', desc: '成本控管效率。' },
            { key: 'basic_eps', title: '基本每股盈餘 (EPS)', desc: '每一股可分配的稅後盈餘。' },
            { key: 'diluted_eps', title: '稀釋每股盈餘', desc: '考慮潛在股數後的 EPS。' }
        ],
        balance_sheet: [
            { key: 'cash_and_equivalents', title: '現金及約當現金', desc: '可隨時動用的資金與高流動資產。' },
            { key: 'short_term_investments', title: '短期投資', desc: '一年內可變現的投資項目。' },
            { key: 'accounts_receivable_and_notes', title: '應收帳款及票據', desc: '尚未收回的客戶貨款。' },
            { key: 'inventory', title: '存貨', desc: '公司持有的商品、原物料與在製品。' },
            { key: 'current_assets', title: '流動資產', desc: '一年內可變現的資產。' },
            { key: 'fixed_assets_total', title: '固定資產', desc: '長期營運使用的實體資產。' },
            { key: 'total_assets', title: '總資產', desc: '企業在某一時間點擁有的全部資產。' },
            { key: 'cash_and_equivalents_pct', title: '現金及約當現金佔總資產百分比', desc: '現金占總資產的比率。' },
            { key: 'short_term_investments_pct', title: '短期投資佔總資產百分比', desc: '短期投資占總資產的比率。' },
            { key: 'accounts_receivable_and_notes_pct', title: '應收帳款及票據佔總資產百分比', desc: '應收帳款占總資產的比率。' },
            { key: 'inventory_pct', title: '存貨佔總資產百分比', desc: '存貨占總資產的比率。' },
            { key: 'current_assets_pct', title: '流動資產佔總資產百分比', desc: '流動資產占總資產的比率。' },
            { key: 'fixed_assets_total_pct', title: '固定資產佔總資產百分比', desc: '固定資產占總資產的比率。' },
            { key: 'other_non_current_assets_pct', title: '其餘資產佔總資產百分比', desc: '其他非流動資產占總資產的比率。' }
        ]
    };

    for (const block of rankingBlocks) {
        const blockDiv = document.createElement('div');
        blockDiv.className = 'ranking-block';
        // 標題
        const title = document.createElement('h2');
        title.className = 'ranking-block-title';
        title.textContent = '財報項目排名';
        blockDiv.appendChild(title);
        // 小標題
        const subtitle = document.createElement('div');
        subtitle.className = 'ranking-block-subtitle';
        subtitle.textContent = block.title;
        blockDiv.appendChild(subtitle);
        // tab bar
        const tabBar = document.createElement('div');
        tabBar.className = 'report-tab-bar';
        const tabDetail = document.createElement('button');
        tabDetail.className = 'report-tab-btn active';
        tabDetail.type = 'button';
        tabDetail.textContent = '指標排名';
        const tabExplain = document.createElement('button');
        tabExplain.className = 'report-tab-btn';
        tabExplain.type = 'button';
        tabExplain.textContent = '指標解釋';
        tabBar.appendChild(tabDetail);
        tabBar.appendChild(tabExplain);
        blockDiv.appendChild(tabBar);
        // 內容區
        const detailSection = document.createElement('div');
        detailSection.className = 'ranking-detail-section';
        const explainSection = document.createElement('div');
        explainSection.className = 'ranking-explain-section';
        explainSection.style.display = 'none';
        blockDiv.appendChild(detailSection);
        blockDiv.appendChild(explainSection);
        section.appendChild(blockDiv);

        // tab 切換
        tabDetail.onclick = () => {
            tabDetail.classList.add('active');
            tabExplain.classList.remove('active');
            detailSection.style.display = '';
            explainSection.style.display = 'none';
        };
        tabExplain.onclick = () => {
            tabExplain.classList.add('active');
            tabDetail.classList.remove('active');
            detailSection.style.display = 'none';
            explainSection.style.display = '';
        };

        // 製作互動選單（年份、期間）
        const controls = document.createElement('div');
        controls.className = 'ranking-controls';
        // 年份（遞減排序，預設2024在最上）
        const yearLabel = document.createElement('label');
        yearLabel.textContent = '年份';
        const yearSelect = document.createElement('select');
        for (let y = block.yearRange[1]; y >= block.yearRange[0]; y--) {
            const opt = document.createElement('option');
            opt.value = y;
            opt.textContent = y;
            if (y === block.defaultYear) opt.selected = true;
            yearSelect.appendChild(opt);
        }
        // 期間
        const periodLabel = document.createElement('label');
        periodLabel.textContent = '期間';
        const periodSelect = document.createElement('select');
        block.reportTypes.forEach(rt => {
            const opt = document.createElement('option');
            opt.value = rt.value;
            opt.textContent = rt.label;
            if (rt.disabled) opt.disabled = true;
            if (rt.value === block.defaultReportType) opt.selected = true;
            periodSelect.appendChild(opt);
        });
        // 季別
        const quarterLabel = document.createElement('label');
        quarterLabel.textContent = '季別';
        const quarterSelect = document.createElement('select');
        block.quarters.forEach(q => {
            const opt = document.createElement('option');
            opt.value = q;
            opt.textContent = 'Q' + q;
            if (q === block.defaultQuarter) opt.selected = true;
            quarterSelect.appendChild(opt);
        });
        controls.appendChild(yearLabel);
        controls.appendChild(yearSelect);
        controls.appendChild(periodLabel);
        controls.appendChild(periodSelect);
        controls.appendChild(quarterLabel);
        controls.appendChild(quarterSelect);
        blockDiv.insertBefore(controls, tabBar);

        // 根據規則動態禁用季別/期間
        function updateDropdownStatus() {
            const year = parseInt(yearSelect.value);
            const period = periodSelect.value;
            // 現金流量表
            if (block.key === 'cash_flow') {
                // 年報時，季別全部 disabled，查詢時自動帶入 Q4
                if (period === 'annual') {
                    Array.from(quarterSelect.options).forEach(opt => { opt.disabled = true; });
                    quarterSelect.value = 4;
                    // 2025 禁用（不論 value 型別）
                    Array.from(yearSelect.options).forEach(opt => {
                        opt.disabled = (String(opt.value) === '2025');
                    });
                } else if (period === 'accumulated') {
                    quarterSelect.disabled = false;
                    Array.from(quarterSelect.options).forEach(opt => {
                        if (year === 2025) {
                            opt.disabled = opt.value !== '1';
                            if (opt.value === '1') quarterSelect.value = 1;
                        } else {
                            opt.disabled = !['1','2','3'].includes(opt.value);
                            if (!['1','2','3'].includes(quarterSelect.value)) quarterSelect.value = '1';
                        }
                    });
                    // 2025 禁用
                    Array.from(yearSelect.options).forEach(opt => {
                        opt.disabled = false;
                    });
                }
            }
            // 損益表
            else if (block.key === 'income_statement') {
                if (period === 'annual') {
                    Array.from(quarterSelect.options).forEach(opt => { opt.disabled = true; });
                    quarterSelect.value = 4;
                    // 2025 禁用
                    Array.from(yearSelect.options).forEach(opt => {
                        opt.disabled = (opt.value === '2025');
                    });
                } else if (period === 'accumulated') {
                    quarterSelect.disabled = false;
                    Array.from(quarterSelect.options).forEach(opt => {
                        if (year === 2025) {
                            opt.disabled = opt.value !== '1';
                            if (opt.value === '1') quarterSelect.value = 1;
                        } else {
                            opt.disabled = !['1','2','3'].includes(opt.value);
                            if (!['1','2','3'].includes(quarterSelect.value)) quarterSelect.value = '1';
                        }
                    });
                    // 2025 禁用
                    Array.from(yearSelect.options).forEach(opt => {
                        opt.disabled = false;
                    });
                } else if (period === 'quarterly') {
                    quarterSelect.disabled = false;
                    Array.from(quarterSelect.options).forEach(opt => {
                        if (year === 2025) {
                            opt.disabled = opt.value !== '1';
                            if (opt.value === '1') quarterSelect.value = 1;
                        } else {
                            opt.disabled = false;
                        }
                    });
                    // 2025 禁用
                    Array.from(yearSelect.options).forEach(opt => {
                        opt.disabled = false;
                    });
                }
                // 期間下拉允許全部
                Array.from(periodSelect.options).forEach(opt => {
                    opt.disabled = false;
                });
            }
            // 資產負債表
            else if (block.key === 'balance_sheet') {
                // 只允許季報
                periodSelect.value = 'quarterly';
                periodSelect.disabled = false;
                Array.from(periodSelect.options).forEach(opt => {
                    opt.disabled = opt.value !== 'quarterly';
                });
                quarterSelect.disabled = false;
                Array.from(quarterSelect.options).forEach(opt => {
                    if (year === 2025) {
                        opt.disabled = opt.value !== '1';
                        if (opt.value === '1') quarterSelect.value = 1;
                    } else {
                        opt.disabled = false;
                    }
                });
            }
        }
        yearSelect.onchange = () => { updateDropdownStatus(); updateBlock(); };
        periodSelect.onchange = () => { updateDropdownStatus(); updateBlock(); };
        quarterSelect.onchange = () => { updateBlock(); };

        // 渲染排名內容
        const updateBlock = async () => {
            if (window.loadingIndicator) window.loadingIndicator.style.display = 'flex';
            detailSection.textContent = '載入中...';
            explainSection.textContent = '';
            const year = parseInt(yearSelect.value);
            const period = periodSelect.value;
            const quarter = parseInt(quarterSelect.value);
            let apiPeriod = period;
            let apiQuarter = quarter;
            // API 查詢參數組合正確
            if (block.key === 'cash_flow') {
                if (period === 'annual') {
                    apiPeriod = 'annual';
                    apiQuarter = 4;
                } else if (period === 'accumulated') {
                    apiPeriod = 'accumulated';
                }
            } else if (block.key === 'income_statement') {
                if (period === 'annual') {
                    apiPeriod = 'annual';
                    apiQuarter = 4;
                } else if (period === 'accumulated') {
                    apiPeriod = 'accumulated';
                } else if (period === 'quarterly') {
                    apiPeriod = 'quarterly';
                }
            } else if (block.key === 'balance_sheet') {
                apiPeriod = 'quarterly';
            }
            try {
                const res = await fetch(`/api/advanced_search/stock_ranking?stock_symbol=${stockSymbol}&country=${country}&statement_type=${block.key}&report_type=${apiPeriod}&year=${year}&quarter=${apiQuarter}`);
                if (!res.ok) throw new Error('查詢失敗');
                const rankingData = await res.json();
                if (!rankingData.data || !rankingData.data.rankings) throw new Error('無資料');
                // 渲染排名
                detailSection.textContent = '';
                // 產業/幣別/總數
                const sectorDiv = document.createElement('div');
                sectorDiv.className = 'ranking-sector';
                
                const span1 = document.createElement('span');
                span1.textContent = '產業：';
                sectorDiv.appendChild(span1);
                sectorDiv.appendChild(document.createTextNode(rankingData.data.stock_info.sector || '-'));
                const span2 = document.createElement('span');
                span2.className = 'ranking-currency';
                span2.textContent = '幣別：TWD (單位: 千元)';
                sectorDiv.appendChild(span2);
                const firstKey = Object.keys(rankingData.data.rankings).find(
                  k => rankingData.data.rankings[k] && rankingData.data.rankings[k].total_count
                );
                const totalCount = firstKey ? rankingData.data.rankings[firstKey].total_count : '-';
                const span3 = document.createElement('span');
                span3.className = 'ranking-label';
                span3.textContent = `同產業公司總數：${totalCount}`;
                sectorDiv.appendChild(span3);
                detailSection.appendChild(sectorDiv);
                // 條列
                const ul = document.createElement('ul');
                ul.className = 'ranking-list';
                // 取得季度資訊
                const queryParams = rankingData.data.query_params;
                let quarterText = '';
                if (queryParams.report_type === 'annual') {
                    quarterText = '季度：年報';
                } else if (queryParams.report_type === 'accumulated') {
                    quarterText = `季度：Q${queryParams.quarter}累計`;
                } else if (queryParams.report_type === 'quarterly') {
                    quarterText = `季度：Q${queryParams.quarter}`;
                }
                Object.entries(rankingData.data.rankings).forEach(([key, item]) => {
                    const li = document.createElement('li');
                    li.className = 'ranking-item';
                    // 指標名稱
                    const metric = document.createElement('span');
                    metric.className = 'ranking-metric';
                    metric.textContent = item.description || '-';
                    // 值
                    const value = document.createElement('span');
                    value.className = 'ranking-value';
                    if (item.value === null || item.value === undefined) value.textContent = '-';
                    else if (typeof item.value === 'number' && metric.textContent.includes('EPS')) value.textContent = item.value.toFixed(2);
                    else if (typeof item.value === 'number' && metric.textContent.includes('百分比')) value.textContent = item.value.toFixed(2) + '%';
                    else if (typeof item.value === 'number') value.textContent = new Intl.NumberFormat('zh-TW').format(item.value);
                    else value.textContent = item.value;
                    // 排名
                    const rank = document.createElement('span');
                    rank.className = 'ranking-rank';
                    rank.textContent = (item.rank === null || item.rank === undefined) ? '排名：-' : `排名：${item.rank}`;
                    // 總數
                    const total = document.createElement('span');
                    total.className = 'ranking-total';
                    total.textContent = `/ ${item.total_count || '-'} 名`;
                    // 季度資訊
                    const quarterSpan = document.createElement('span');
                    quarterSpan.className = 'ranking-quarter';
                    quarterSpan.textContent = quarterText;
                    li.appendChild(metric);
                    li.appendChild(value);
                    li.appendChild(rank);
                    li.appendChild(total);
                    li.appendChild(quarterSpan);
                    ul.appendChild(li);
                });
                detailSection.appendChild(ul);
                // 渲染指標解釋
                explainSection.textContent = '';
                const explainList = RANKING_EXPLAIN_MAP[block.key];
                const rankingKeys = Object.keys(rankingData.data.rankings);
                rankingKeys.forEach(key => {
                    const explain = explainList.find(e => e.key === key);
                    if (explain) {
                        const div = document.createElement('div');
                        div.className = 'explain-block ranking-explain-block';
                        const h3 = document.createElement('h3');
                        h3.textContent = explain.title;
                        div.appendChild(h3);
                        const desc = document.createElement('div');
                        desc.className = 'explain-block-desc';
                        desc.textContent = explain.desc;
                        div.appendChild(desc);
                        explainSection.appendChild(div);
                    }
                });
            } catch (e) {
                detailSection.textContent = '查詢失敗或無資料';
                explainSection.textContent = '';
            } finally {
                if (window.loadingIndicator) window.loadingIndicator.style.display = 'none';
            }
        };
        updateDropdownStatus();
        updateBlock();
    }
}

// ========== 相關新聞功能 ========== //
async function fetchCompanyNews(keyword, page = 1) {
    const section = document.getElementById('related-news-section');
    const list = section.querySelector('.related-news-list');
    const pagination = section.querySelector('.related-news-pagination');
    if (loadingIndicator) loadingIndicator.style.display = "flex";
    // 清空內容
    while (list.firstChild) list.removeChild(list.firstChild);
    while (pagination.firstChild) pagination.removeChild(pagination.firstChild);

    try {
        const response = await fetch(`/api/news?keyword=${encodeURIComponent(keyword)}&page=${page}`);
        const result = await response.json();
        // 清空 loading
        while (list.firstChild) list.removeChild(list.firstChild);
        if (!result.data || result.data.length === 0) {
            const empty = document.createElement('div');
            empty.textContent = '查無相關新聞';
            list.appendChild(empty);
            if (loadingIndicator) loadingIndicator.style.display = 'none';
            return;
        }
        renderCompanyNews(result, page, result.nextPage);
    } catch (e) {
        while (list.firstChild) list.removeChild(list.firstChild);
        const fail = document.createElement('div');
        fail.textContent = '載入新聞失敗';
        list.appendChild(fail);
    } finally {
        if (loadingIndicator) loadingIndicator.style.display = 'none';
    }
}
function renderCompanyNews(newsData, page, nextPage) {
    const section = document.getElementById('related-news-section');
    const list = section.querySelector('.related-news-list');
    const pagination = section.querySelector('.related-news-pagination');
    // 清空內容
    while (list.firstChild) list.removeChild(list.firstChild);
    while (pagination.firstChild) pagination.removeChild(pagination.firstChild);
    newsData.data.forEach(item => {
        const block = document.createElement('div');
        block.className = 'related-news-block';
        const newsSection = document.createElement('div');
        newsSection.className = 'related-news-session';
        const newsTitle = document.createElement('div');
        newsTitle.textContent = item.title || '';
        newsTitle.className = 'related-news-title-text';
        const newsContent = document.createElement('div');
        newsContent.className = 'related-news-content';
        newsContent.textContent = item.content || '';
        const publishAtDiv = document.createElement('div');
        publishAtDiv.className = 'related-news-publishAt';
        const date = new Date(item.publishAt * 1000);
        publishAtDiv.textContent = date.toLocaleString('zh-TW', { timeZone: 'Asia/Taipei' });
        const newsCategory = document.createElement('span');
        let categoryContent = item.category || '';
        if (categoryContent === 'headline') categoryContent = '頭條新聞';
        newsCategory.textContent = categoryContent;
        newsCategory.className = 'related-news-category';
        const newsSource = document.createElement('div');
        let newsSourceContent = item.source || '';
        if (newsSourceContent === 'anue') newsSourceContent = '鉅亨網';
        newsSource.textContent = newsSourceContent;
        newsSource.className = 'related-news-source';
        const newsURL = document.createElement('div');
        newsURL.textContent = item.url || '';
        newsURL.className = 'related-news-url';
        newsURL.style.display = 'none';
        newsSection.appendChild(newsTitle);
        newsSection.appendChild(newsContent);
        newsSection.appendChild(publishAtDiv);
        newsSection.appendChild(newsSource);
        newsSection.appendChild(newsCategory);
        newsSection.appendChild(newsURL);
        block.appendChild(newsSection);
        list.appendChild(block);
    });
    // 分頁按鈕
    if (page > 1) {
        const prevBtn = document.createElement('button');
        prevBtn.textContent = '上一頁';
        prevBtn.className = 'related-news-btn';
        prevBtn.onclick = () => fetchCompanyNews(window._companyNewsKeyword, page - 1);
        pagination.appendChild(prevBtn);
    }
    if (nextPage) {
        const nextBtn = document.createElement('button');
        nextBtn.textContent = '下一頁';
        nextBtn.className = 'related-news-btn';
        nextBtn.onclick = () => fetchCompanyNews(window._companyNewsKeyword, nextPage);
        pagination.appendChild(nextBtn);
    }
    monitorCompanyNewsClicks();
}
function monitorCompanyNewsClicks() {
    let listItems = document.querySelectorAll('.related-news-session');
    listItems.forEach(item => {
        item.addEventListener('click', () => {
            let urlEl = item.querySelector('.related-news-url');
            if (urlEl) {
                let url = urlEl.textContent.trim();
                window.open(url, '_blank');
            }
        });
    });
}

// ========== 個股 AI 分析功能 ========== //
let _aiAnalysisSummary = false;
let _aiAnalysisPage = 1;
function setupAIAnalysisToggle(keyword) {
    const section = document.getElementById('stock-ai-analysis-section');
    if (!section) return;
    const btns = section.querySelectorAll('.ai-analysis-btn');
    btns.forEach(btn => {
        btn.onclick = () => {
            const isSummary = btn.getAttribute('data-summary') === 'true';
            _aiAnalysisSummary = isSummary;
            _aiAnalysisPage = 1;
            fetchCompanyAIAnalysis(keyword, isSummary, 1);
            btns.forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
        };
    });
    // 預設啟用逐條分析
    btns.forEach(b => b.classList.remove('active'));
    section.querySelector('.ai-analysis-btn[data-summary="false"]').classList.add('active');
}
async function fetchCompanyAIAnalysis(keyword, is_summary = false, page = 1) {
    const section = document.getElementById('stock-ai-analysis-section');
    const list = section.querySelector('.ai-analysis-list');
    const pagination = section.querySelector('.ai-analysis-pagination');
    if (window.loadingIndicator) window.loadingIndicator.style.display = 'flex';
    while (list.firstChild) list.removeChild(list.firstChild);
    while (pagination.firstChild) pagination.removeChild(pagination.firstChild);
    const endTime = Math.floor(Date.now() / 1000);
    const startTime = Math.floor(new Date('2020-01-01T00:00:00Z').getTime() / 1000);
    try {
        const response = await fetch(`/api/ai_news?keyword=${encodeURIComponent(keyword)}&is_summary=${is_summary}&start_time=${startTime}&end_time=${endTime}&page=${page}`);
        const result = await response.json();
        if (!result.data || result.data.length === 0) {
            const empty = document.createElement('div');
            empty.textContent = '查無分析結果';
            list.appendChild(empty);
            if (window.loadingIndicator) window.loadingIndicator.style.display = 'none';
            return;
        }
        renderCompanyAIAnalysis(result, page, result.nextPage);
    } catch (e) {
        const fail = document.createElement('div');
        fail.textContent = '載入分析失敗';
        list.appendChild(fail);
    } finally {
        if (window.loadingIndicator) window.loadingIndicator.style.display = 'none';
    }
}
function renderCompanyAIAnalysis(data, page, nextPage) {
    const section = document.getElementById('stock-ai-analysis-section');
    const list = section.querySelector('.ai-analysis-list');
    const pagination = section.querySelector('.ai-analysis-pagination');
    while (list.firstChild) list.removeChild(list.firstChild);
    while (pagination.firstChild) pagination.removeChild(pagination.firstChild);
    data.data.forEach(item => {
        const block = document.createElement('div');
        block.className = 'ai-analysis-block';
        // 標題
        const title = document.createElement('div');
        title.className = 'ai-analysis-article-title';
        title.textContent = item.article_title || '';
        block.appendChild(title);
        // 洞察結果
        const summaryTitle = document.createElement('div');
        summaryTitle.className = 'ai-analysis-section-title';
        summaryTitle.textContent = '洞察結果：';
        block.appendChild(summaryTitle);
        const summaryContent = document.createElement('div');
        summaryContent.className = 'ai-analysis-summary';
        summaryContent.textContent = item.summary || '';
        block.appendChild(summaryContent);
        // 重點新聞
        const newsTitle = document.createElement('div');
        newsTitle.className = 'ai-analysis-section-title';
        newsTitle.textContent = '重點新聞：';
        block.appendChild(newsTitle);
        const newsContent = document.createElement('div');
        newsContent.className = 'ai-analysis-important-news';
        newsContent.textContent = item.important_news || '';
        block.appendChild(newsContent);
        // 情緒分析
        const sentimentTitle = document.createElement('div');
        sentimentTitle.className = 'ai-analysis-section-title';
        sentimentTitle.textContent = '情緒分析：';
        block.appendChild(sentimentTitle);
        const sentimentContent = document.createElement('div');
        sentimentContent.className = 'ai-analysis-sentiment';
        sentimentContent.textContent = item.sentiment || '';
        block.appendChild(sentimentContent);
        // 產業分析
        const potentialTitle = document.createElement('div');
        potentialTitle.className = 'ai-analysis-section-title';
        potentialTitle.textContent = '產業分析：';
        block.appendChild(potentialTitle);
        const potentialContent = document.createElement('div');
        potentialContent.className = 'ai-analysis-potential';
        potentialContent.textContent = item.potential_stocks_and_industries || '';
        block.appendChild(potentialContent);
        // 相關股票
        const stockTitle = document.createElement('div');
        stockTitle.className = 'ai-analysis-section-title';
        stockTitle.textContent = '潛力股票：';
        block.appendChild(stockTitle);
        const stockList = document.createElement('div');
        stockList.className = 'ai-analysis-stock-list';
        (item.stock_list || []).forEach(stock => {
            const btn = document.createElement('button');
            btn.className = 'ai-analysis-stock-btn';
            btn.textContent = stock[2];
            btn.onclick = () => {
                if (stock[0] === 'tw') {
                    window.open(`/stock/${stock[1]}/tw`, '_blank');
                } else {
                    window.open(`https://www.google.com/search?q=${stock[2]}`, '_blank');
                }
            };
            stockList.appendChild(btn);
        });
        block.appendChild(stockList);
        // 相關產業
        const industryTitle = document.createElement('div');
        industryTitle.className = 'ai-analysis-section-title';
        industryTitle.textContent = '潛力產業：';
        block.appendChild(industryTitle);
        const industryList = document.createElement('div');
        industryList.className = 'ai-analysis-industry-list';
        (item.industry_list || []).forEach(ind => {
            const span = document.createElement('span');
            span.className = 'ai-analysis-industry-item';
            span.textContent = ind;
            industryList.appendChild(span);
        });
        block.appendChild(industryList);
        // ========== 新增 相關新聞 source_news ========== //
        if (item.source_news && Array.isArray(item.source_news) && item.source_news.length > 0) {
            const sourceNewsTitle = document.createElement('div');
            sourceNewsTitle.className = 'ai-analysis-section-title';
            sourceNewsTitle.textContent = '相關新聞：';
            block.appendChild(sourceNewsTitle);
            const sourceNewsList = document.createElement('div');
            sourceNewsList.className = 'ai-analysis-source-news-list';
            item.source_news.forEach(news => {
                const btn = document.createElement('button');
                btn.className = 'ai-analysis-source-news-btn';
                btn.textContent = news.title || '';
                btn.setAttribute('data-news-id', news._id || '');
                sourceNewsList.appendChild(btn);
            });
            block.appendChild(sourceNewsList);
        }
        // 新增 publishAt 顯示
        if (item.publishAt) {
            const publishAtDiv = document.createElement("div");
            publishAtDiv.className = "publishAtDiv"; // 可以為此 class 設定 CSS 樣式來控制位置和外觀
            const timestamp = item.publishAt; // Unix timestamp（以秒為單位）
            const date = new Date(timestamp * 1000); // 轉成毫秒

            const taiwanTime = date.toLocaleString("zh-TW", {
                timeZone: "Asia/Taipei",
                year: 'numeric', // 顯示年份
                month: '2-digit', // 顯示月份，兩位數
                day: '2-digit', // 顯示日期，兩位數
                hour: '2-digit', // 顯示小時，兩位數
                minute: '2-digit', // 顯示分鐘，兩位數
                second: '2-digit', // 顯示秒數，兩位數
                hour12: false // 使用24小時制
            });
            publishAtDiv.textContent = taiwanTime;
            block.appendChild(publishAtDiv);
        }
        list.appendChild(block);
    });
    // 分頁按鈕
    if (page > 1) {
        const prevBtn = document.createElement('button');
        prevBtn.textContent = '上一頁';
        prevBtn.className = 'ai-analysis-btn-page';
        prevBtn.onclick = () => fetchCompanyAIAnalysis(window._companyNewsKeyword, _aiAnalysisSummary, page - 1);
        pagination.appendChild(prevBtn);
    }
    if (nextPage) {
        const nextBtn = document.createElement('button');
        nextBtn.textContent = '下一頁';
        nextBtn.className = 'ai-analysis-btn-page';
        nextBtn.onclick = () => fetchCompanyAIAnalysis(window._companyNewsKeyword, _aiAnalysisSummary, nextPage);
        pagination.appendChild(nextBtn);
    }
    monitorCompanyAINewsClicks();
}

// 新增：監聽 AI 相關新聞按鈕點擊，參考 ai_news.js monitorNewsClicks
function monitorCompanyAINewsClicks() {
    const newsBtns = document.querySelectorAll('.ai-analysis-source-news-btn');
    newsBtns.forEach(btn => {
        btn.addEventListener('click', async () => {
            const newsId = btn.getAttribute('data-news-id');
            if (newsId) {
                try {
                    const response = await fetch(`/api/news/${newsId}`);
                    if (!response.ok) throw new Error(`HTTP 錯誤狀態碼: ${response.status}`);
                    const data = await response.json();
                    const news = data.data;
                    const sourceURL = news.url.trim();
                    window.open(sourceURL, '_blank');
                } catch (error) {
                    console.error('無法載入原始網站，請至搜尋引擎搜尋標題關鍵字，觀看原始網站文章', error);
                    alert('無法載入原始網站，請至搜尋引擎搜尋標題關鍵字，觀看原始網站文章');
                }
            }
        });
    });
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
async function getUserData() {
    try {
        const response = await fetch("/api/user/auth", {
            method: "GET",
            credentials: "include" // 自動帶 cookie
        });
        const data = await response.json();

        if (!response.ok) {
            console.log("取得使用者資料失敗:", data.message);
            window.location.href = '/login';
            return false;
        }else{
            return true;
        }

    } catch (err) {
        console.error("取得使用者資料錯誤:", err);
        return false;
    }
}

function excute(){
    getUserData();
    initializeFooterLinks();
    monitorUserIconClicks();
}
window.addEventListener("DOMContentLoaded", excute);