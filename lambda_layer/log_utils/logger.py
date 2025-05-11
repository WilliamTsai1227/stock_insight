# log_handler.py
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
import os
import time

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
def log_error(log_collection:str = None,log_type: str = None, error_message: str = None, additional_info: dict = None, source: str = None, error_db:str = None, error_collection:str = None):
    try:
        # Get current time
        current_time = int(time.time())
        # Prepare log entry
        log_entry = {
            "log_type": log_type,
            "error_message": error_message,
            "timestamp": current_time,
            "additional_info": additional_info,
            "source":source,
            "error_db":error_db,
            "error_collection":error_collection
        }
        # Insert log entry into MongoDB
        db = client.log_data
        collection = db[log_collection]
        collection.insert_one(log_entry)
    except Exception as e:
        print(f"Error logging to MongoDB: {e}")
        raise e
    
# Log success to MongoDB
def log_success(log_collection:str = None,log_type: str = None,successful_message:str = None , additional_info: dict = None, source:str =None, success_db:str = None, success_collection:str = None):

    try:
        # Get current time
        current_time = int(time.time())
        # Prepare log entry
        log_entry = {
            "log_type": log_type,
            "source":source,
            "success_message":successful_message,
            "timestamp": current_time,
            "additional_info": additional_info,
            "success_db":success_db,
            "success_collection":success_collection
        }
        # Insert log entry into MongoDB
        db = client.log_data
        collection = db[log_collection]
        collection.insert_one(log_entry)
        
    except Exception as e:
        raise e
