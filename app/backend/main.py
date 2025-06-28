from fastapi import FastAPI, Request
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pathlib import Path
import os
from fastapi.middleware.cors import CORSMiddleware
from api import log, ai_news, news, stock

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 可改為你的前端網址，例如 http://localhost:5500 或 http://messageboards.life
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Dynamically obtain the root directory (that is, the app/ folder)
BASE_DIR = Path(__file__).resolve().parent.parent

# Get the html/css/js path
HTML_DIR = BASE_DIR / "frontend" / "html"
CSS_DIR = BASE_DIR / "frontend" / "css"
JS_DIR = BASE_DIR / "frontend" / "js"

# 掛載靜態檔案目錄
app.mount("/css", StaticFiles(directory=str(CSS_DIR), html=True), name="css")
app.mount("/js", StaticFiles(directory=str(JS_DIR), html=True), name="js")

# 回傳 HTML 頁面
@app.get("/", include_in_schema=False)
async def index(request: Request):
    return FileResponse(HTML_DIR / "index.html", media_type="text/html")

@app.get("/home", include_in_schema=False)
async def home(request: Request):
    return FileResponse(HTML_DIR / "index.html", media_type="text/html")

@app.get("/ai_news", include_in_schema=False)
async def ai_news_page(request: Request):
    return FileResponse(HTML_DIR / "ai_news.html", media_type="text/html")

@app.get("/news", include_in_schema=False)
async def news_page(request: Request):
    return FileResponse(HTML_DIR / "news.html", media_type="text/html")

@app.get("/news/{id}", include_in_schema=False)
async def news_detail(request: Request, id: str):
    return FileResponse(HTML_DIR / "detail_news.html", media_type="text/html")

@app.get("/stock/{symbol}/{country}", include_in_schema=False)
async def stock_page(request: Request, symbol: str, country: str):
    return FileResponse(HTML_DIR / "stock.html", media_type="text/html")

@app.get("/insight", include_in_schema=False)
async def home(request: Request):
    return FileResponse(HTML_DIR / "insight.html", media_type="text/html")

# 加入 API router
app.include_router(log.router)
app.include_router(ai_news.router)
app.include_router(news.router)
app.include_router(stock.router)