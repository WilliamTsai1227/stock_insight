from fastapi import FastAPI
from api import log, ai_news

app = FastAPI()
app.include_router(log.router)
app.include_router(ai_news.router)
