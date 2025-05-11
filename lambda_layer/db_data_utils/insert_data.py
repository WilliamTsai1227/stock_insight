
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
from pymongo.errors import BulkWriteError
from lambda_layer.log_utils.logger import log_error,log_success
import os


if os.getenv("AWS_EXECUTION_ENV") is None:
    from dotenv import load_dotenv
    load_dotenv()


db_user = os.getenv('mongodb_user')
db_password = os.getenv('mongodb_password')

uri = f"mongodb+srv://{db_user}:{db_password }@stock-main.kbyokcd.mongodb.net/?retryWrites=true&w=majority&appName=stock-main"

# Create a new client and connect to the server
client = MongoClient(uri, server_api=ServerApi('1'))

# Items can either bring in multiple data entries wrapped in a list, or a single data entry wrapped in a dictionary.
def insert_data_mongodb(items, insert_db: str, insert_collection: str,log_success_collection:str,log_error_collection:str,source: str = None):
    if not insert_db or not insert_collection:
        error_message = "No db and collection parameters were provided to the insert_data_mongodb() module"
        log_error(log_error_collection,"insert",error_message, error_db=insert_db, error_collection=insert_collection)
        return False

    if not isinstance(insert_db, str) or not isinstance(insert_collection, str):
        error_message = "The insert_db or insert_collection parameter passed to insert_data_mongodb() is not str data type"
        log_error(log_error_collection,"insert",error_message, error_db=insert_db, error_collection=insert_collection)
        return False

    # Connect to MongoDB
    try:
        db = client[insert_db]
        collection = db[insert_collection]

        # 如果 `items` 不是列表，將它包裝成列表
        if isinstance(items, dict):
            data_to_insert = [items]  # 直接將字典轉為列表形式
        elif isinstance(items, list):
            # 如果是列表，檢查每個項目是否是字典
            if not all(isinstance(item, dict) for item in items):
                error_message = "All items in the list must be dictionaries"
                log_error(log_error_collection,"insert",error_message, error_db=insert_db, error_collection=insert_collection)
                return False
            data_to_insert = items
        else:
            data_to_insert = [{"data": items}]     

        # 使用 `insert_many` 插入數據，insert many 只能insert list，但list內部每一條都必須是字典，然後他會一條條字典(document)寫入
        try:
            result = collection.insert_many(data_to_insert, ordered=False)
            inserted_count = len(result.inserted_ids)
            if inserted_count > 0:
                log_success(log_success_collection,"insert", successful_inserts=inserted_count, source=source, success_db=insert_db, success_collection=insert_collection)
                return True
            else:
                error_message = "No documents were inserted."
                log_error(log_error_collection,"insert", error_message, error_db=insert_db, error_collection=insert_collection)
                return False
        except BulkWriteError as bwe:
            inserted_count = bwe.details.get('nInserted', 0)
            error_message = f"Bulk write warning: {bwe.details}"
            log_error(log_error_collection,"insert", error_message, error_db=insert_db, error_collection=insert_collection)
            return False

    except Exception as e:
        error_message = f"Insert mongodb fail: {e}"
        log_error(log_error_collection,"insert", error_message, error_db=insert_db, error_collection=insert_collection)
        return False
