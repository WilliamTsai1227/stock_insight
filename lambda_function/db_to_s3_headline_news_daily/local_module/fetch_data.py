from pymongo import MongoClient
import os
if os.getenv("AWS_EXECUTION_ENV") is None:
    from dotenv import load_dotenv
    load_dotenv()
db_user = os.getenv('mongodb_user')
db_password = os.getenv('mongodb_password')

def get_news(start_time, end_time, db_name, collection_name):

    uri = f"mongodb+srv://{db_user}:{db_password }@stock-main.kbyokcd.mongodb.net/?retryWrites=true&w=majority&appName=stock-main"
    client = MongoClient(uri)
    db = client[db_name]
    collection = db[collection_name]

    query = {
        "publishAt": {
            "$gte": start_time,
            "$lt": end_time
        },
        "category": "headline",
        "source":"anue"
    }
    return list(collection.find(query))
