# log_handler.py
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
from datetime import datetime, timezone
import os
from enum import Enum
import time

class LogType(str, Enum):
    CRAWLER_ERROR = "crawler_error"
    SYSTEM_ERROR = "system_error"


if os.getenv("AWS_EXECUTION_ENV") is None:
    from dotenv import load_dotenv
    load_dotenv()

db_user = os.getenv('mongodb_user')
db_password = os.getenv('mongodb_password')

# MongoDB Connection URI
uri = f"mongodb+srv://{db_user}:{db_password}@stock-main.kbyokcd.mongodb.net/?retryWrites=true&w=majority&appName=stock-main"

# Create a new client and connect to the server
client = MongoClient(uri, server_api=ServerApi('1'))

# Log error to MongoDB
def log_error(log_type: LogType, error_message: str, additional_info: dict = None, source: str = None, db:str = None, collection:str = None):
    try:
        # Get current time
        current_time = datetime.now(timezone.utc)  # datetime UTC+0 with timezone=UTC
        current_time = int(time.time())
        # Prepare log entry
        log_entry = {
            "log_type": log_type.value,
            "error_message": error_message,
            "timestamp": current_time,
            "additional_info": additional_info or {},
            "source":source,
            "db":db,
            "collection":collection
        }
        # Insert log entry into MongoDB
        db = client.log_data
        collection = db[log_type.value]
        collection.insert_one(log_entry)
        print(f"Log inserted into {log_type.value} collection.")
    except Exception as e:
        print(f"Error logging to MongoDB: {e}")
        raise e
    
# Log success to MongoDB
def log_success(log_type: str,successful_inserts:int , additional_info: dict = None, source:str =None, db:str = None, collection:str = None):

    try:
        # Get current time
        current_time = datetime.now(timezone.utc)  # datetime UTC+0 with timezone=UTC
        current_time = int(time.time())
        # Prepare log entry
        log_entry = {
            "log_type": log_type,
            "source":source,
            "successful_inserts": successful_inserts,
            "timestamp": current_time,
            "additional_info": additional_info or {},
            "db":db,
            "collection":collection
        }

        # Determine collection based on error type
        if log_type == 'crawler_insert_success':
            collection_name = 'crawler_insert_success'
        else:
            raise ValueError("Unsupported log type")

        # Insert log entry into MongoDB
        db = client.log_data
        collection = db[collection_name]
        collection.insert_one(log_entry)
        
    except Exception as e:
        raise e
