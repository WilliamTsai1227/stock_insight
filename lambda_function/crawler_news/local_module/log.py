import datetime
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
import os
from datetime import datetime, timezone
import time



db_user = os.getenv('mongodb_user')
db_password = os.getenv('mongodb_password')

uri = f"mongodb+srv://{db_user}:{db_password }@stock-main.kbyokcd.mongodb.net/?retryWrites=true&w=2&appName=stock-main"

# Create a new client and connect to the server
client = MongoClient(uri, server_api=ServerApi('1'))

# Log error to MongoDB
def log_error(log_type:str, message: str, additional_info: dict = None, source: str = None, db:str = None, collection:str = None):
    try:
        # Get current time
        current_time = datetime.now(timezone.utc)  # datetime UTC+0 with timezone=UTC
        current_time = int(time.time())
        # Prepare log entry
        log_entry = {
            "log_type": log_type,
            "message": message,
            "timestamp": current_time,
            "additional_info": additional_info or {},
            "source":source,
            "db":db,
            "collection":collection
        }
        # Insert log entry into MongoDB
        db = client["stock_insight"]
        collection = db["log"]
        collection.insert_one(log_entry)
        print(f"Error Log inserted into mongodb db:{db.name}/collection:{collection.name}")
    except Exception as e:
        print(f"Error logging to MongoDB an unexpected error occurred: {e}")
        raise e
    
# Log success to MongoDB
def log_success(log_type: str, message: str , additional_info: dict = None, source:str =None, db:str = None, collection:str = None):

    try:
        # Get current time
        current_time = datetime.now(timezone.utc)  # datetime UTC+0 with timezone=UTC
        current_time = int(time.time())
        # Prepare log entry
        log_entry = {
            "log_type": log_type,
            "source":source,
            "message": message,
            "timestamp": current_time,
            "additional_info": additional_info or None,
            "db":db,
            "collection":collection
        }
        
        # Insert log entry into MongoDB
        db = client["stock_insight"]
        collection = db["log"]
        collection.insert_one(log_entry)
        print(f"Success Log inserted into mongodb db:{db.name}/collection:{collection.name}")
    except Exception as e:
        print(f"Success logging to MongoDB an unexpected error occurred: {e}")
        raise e