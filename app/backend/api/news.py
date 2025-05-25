from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from pymongo import MongoClient
from dotenv import load_dotenv
import os
from bson import ObjectId

load_dotenv()

# MongoDB 連線
db_user = os.getenv('mongodb_user')
db_password = os.getenv('mongodb_password')
uri = f"mongodb+srv://{db_user}:{db_password}@stock-main.kbyokcd.mongodb.net/?retryWrites=true&w=majority&appName=stock-main"
client = MongoClient(uri)
db = client["stock_insight"]
collection = db["news"]

router = APIRouter()

@router.get("/api/news/{object_id}")
async def get_single_news(object_id: str):
    try:
        obj_id = ObjectId(object_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid ObjectId")

    result = collection.find_one({"_id": obj_id})
    
    if not result:
        raise HTTPException(status_code=404, detail="News not found")

    result["_id"] = str(result["_id"])
    return JSONResponse(content={"data": result})


