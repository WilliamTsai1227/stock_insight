import pytest
import logging
from pymongo import MongoClient
from bson import ObjectId
from datetime import datetime

# 設定日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f"test_mongodb_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class TestAINewsAnalysisSchema:
    """測試AI_news_analysis集合中的所有文檔是否符合預期的格式"""

    @classmethod
    def setup_class(cls):
        """建立MongoDB連接和選擇集合 - 測試前執行一次"""
        logger.info("開始執行MongoDB結構驗證測試")
        cls.client = MongoClient('mongodb://localhost:27017/')
        cls.db = cls.client['stock_insight']
        cls.collection = cls.db['AI_news_analysis']
        
        # 獲取所有文檔
        cls.documents = list(cls.collection.find())
        logger.info(f"總共找到 {len(cls.documents)} 個文檔")

    @classmethod
    def teardown_class(cls):
        """關閉MongoDB連接 - 測試後執行一次"""
        cls.client.close()
        logger.info("MongoDB結構驗證測試完成")

    def test_documents_have_required_fields(self):
        """測試所有文檔是否具有所有必要欄位"""
        required_fields = [
            "_id", "analysis_batch", "is_summary", "category", 
            "publishAt", "summary", "important_news", "sentiment",
            "potential_stocks_and_industries", "stock_list", 
            "industry_list", "source_news"
        ]
        
        missing_fields = []
        for doc in self.documents:
            doc_id = str(doc.get('_id'))
            for field in required_fields:
                if field not in doc:
                    missing_fields.append(f"文檔 {doc_id} 缺少必要欄位: {field}")
        
        if missing_fields:
            for error in missing_fields:
                logger.error(error)
            pytest.fail(f"發現 {len(missing_fields)} 個欄位缺失錯誤")
        else:
            logger.info("所有文檔都包含必要欄位 ✓")

    def test_field_types(self):
        """測試所有欄位的數據類型是否正確"""
        type_errors = []
        
        for doc in self.documents:
            doc_id = str(doc.get('_id'))
            
            # 基本欄位類型檢查
            type_checks = [
                ('_id', ObjectId),
                ('analysis_batch', int),
                ('is_summary', bool),
                ('category', str),
                ('publishAt', int),
                ('summary', str),
                ('important_news', str),
                ('sentiment', str),
                ('potential_stocks_and_industries', str),
                ('stock_list', list),
                ('industry_list', list),
                ('source_news', list)
            ]
            
            for field, expected_type in type_checks:
                if not isinstance(doc.get(field), expected_type):
                    type_errors.append(f"文檔 {doc_id} 的 {field} 欄位類型錯誤: 預期 {expected_type.__name__}, 實際 {type(doc.get(field)).__name__}")
            
            # 檢查 stock_list 的結構
            for i, stock in enumerate(doc.get('stock_list', [])):
                if not isinstance(stock, list):
                    type_errors.append(f"文檔 {doc_id} 的 stock_list[{i}] 不是列表類型")
                    continue
                
                if len(stock) != 3:
                    type_errors.append(f"文檔 {doc_id} 的 stock_list[{i}] 長度應為3，實際為 {len(stock)}")
                    continue
                
                for j, item in enumerate(stock):
                    if not isinstance(item, str):
                        type_errors.append(f"文檔 {doc_id} 的 stock_list[{i}][{j}] 不是字串類型")
            
            # 檢查 industry_list 的結構
            for i, industry in enumerate(doc.get('industry_list', [])):
                if not isinstance(industry, str):
                    type_errors.append(f"文檔 {doc_id} 的 industry_list[{i}] 不是字串類型")
            
            # 檢查 source_news 的結構
            for i, news in enumerate(doc.get('source_news', [])):
                if not isinstance(news, dict):
                    type_errors.append(f"文檔 {doc_id} 的 source_news[{i}] 不是字典類型")
                    continue
                
                if 'title' not in news:
                    type_errors.append(f"文檔 {doc_id} 的 source_news[{i}] 缺少 title 欄位")
                elif not isinstance(news['title'], str):
                    type_errors.append(f"文檔 {doc_id} 的 source_news[{i}]['title'] 不是字串類型")
                
                if '_id' not in news:
                    type_errors.append(f"文檔 {doc_id} 的 source_news[{i}] 缺少 _id 欄位")
                elif not isinstance(news['_id'], str):
                    type_errors.append(f"文檔 {doc_id} 的 source_news[{i}]['_id'] 不是字串類型")
        
        if type_errors:
            for error in type_errors:
                logger.error(error)
            pytest.fail(f"發現 {len(type_errors)} 個類型錯誤")
        else:
            logger.info("所有欄位類型均符合預期 ✓")

    def test_summary_and_batch_relationship(self):
        """測試 is_summary 和 analysis_batch 之間的關係
        1. 如果 is_summary 為 true, analysis_batch 應該為 -1
        2. 如果 is_summary 為 false, analysis_batch 不能為 -1
        """
        relationship_errors = []
        
        for doc in self.documents:
            doc_id = str(doc.get('_id'))
            
            if doc['is_summary'] == True and doc['analysis_batch'] != -1:
                relationship_errors.append(
                    f"文檔 {doc_id} 是摘要文檔 (is_summary=true)，但 analysis_batch={doc['analysis_batch']} 不是 -1"
                )
            elif doc['is_summary'] == False and doc['analysis_batch'] == -1:
                relationship_errors.append(
                    f"文檔 {doc_id} 不是摘要文檔 (is_summary=false)，但 analysis_batch 是 -1"
                )
        
        if relationship_errors:
            for error in relationship_errors:
                logger.error(error)
            pytest.fail(f"發現 {len(relationship_errors)} 個 is_summary 和 analysis_batch 關係錯誤")
        else:
            logger.info("所有文檔的 is_summary 和 analysis_batch 關係正確 ✓")

    def test_no_extra_fields(self):
        """測試文檔中是否有多餘的欄位"""
        expected_fields = [
            "_id", "analysis_batch", "is_summary", "category", 
            "publishAt", "summary", "important_news", "sentiment",
            "potential_stocks_and_industries", "stock_list", 
            "industry_list", "source_news"
        ]
        
        extra_fields = []
        for doc in self.documents:
            doc_id = str(doc.get('_id'))
            for field in doc:
                if field not in expected_fields:
                    extra_fields.append(f"文檔 {doc_id} 包含未定義的欄位: {field}")
        
        if extra_fields:
            for error in extra_fields:
                logger.error(error)
            pytest.fail(f"發現 {len(extra_fields)} 個多餘欄位")
        else:
            logger.info("所有文檔都沒有多餘欄位 ✓")

    def test_schema_summary(self):
        """提供整體測試結果摘要"""
        logger.info("已檢查以下項目:")
        logger.info("1. 所有文檔的必要欄位")
        logger.info("2. 所有欄位的數據類型")
        logger.info("3. is_summary 和 analysis_batch 的關係")
        logger.info("4. 是否存在多餘欄位")
        
        # 這個測試總是通過，主要是用來輸出摘要信息
        assert True


if __name__ == '__main__':
    pytest.main(["-v"])