
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
from pymongo.errors import BulkWriteError
from .logger import log_error,log_success,LogType
import os

if os.getenv("AWS_EXECUTION_ENV") is None:
    from dotenv import load_dotenv
    load_dotenv()


db_user = os.getenv('mongodb_user')
db_password = os.getenv('mongodb_password')

uri = f"mongodb+srv://{db_user}:{db_password }@stock-main.kbyokcd.mongodb.net/?retryWrites=true&w=majority&appName=stock-main"

# Create a new client and connect to the server
client = MongoClient(uri, server_api=ServerApi('1'))


def insert_data_mongodb(items: list[dict],insert_db:str,insert_collection:str ,source:str):
    if not insert_db or not insert_collection:
        error_message = "No db and collection parameters were provided to the insert_data_mongodb() module"
        log_error(LogType.CRAWLER_ERROR, error_message,db=insert_db,collection=insert_collection)
        return
    if not isinstance(insert_db,str) or not isinstance(insert_collection,str):
        error_message = "The insert_db or insert_collection parameter passed to insert_data_mongodb() is not str data type"
        log_error(LogType.CRAWLER_ERROR, error_message,db=insert_db,collection=insert_collection)
        return
    try:
        db = client[insert_db]
        collection = db[insert_collection]
        if items:
            try:
                result = collection.insert_many(items, ordered=False)
                inserted_count = len(result.inserted_ids)  #The number of entries that were actually successfully inserted   
            except BulkWriteError as bwe:
                inserted_count = bwe.details.get('nInserted', 0)
                error_message = f"Bulk write warning: {bwe.details}"
            # Regardless of whether there is a unique key conflict, there will be correct log records
            log_success('ai_summary_insert_success', successful_inserts=inserted_count, source=source,db=insert_db,collection=insert_collection) 
    except Exception as e:
        error_message = f"Insert mongodb fail: {e}"
        log_error(LogType.CRAWLER_ERROR, error_message,db=insert_db,collection=insert_collection)
        raise e