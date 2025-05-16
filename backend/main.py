from fastapi import FastAPI
from api import log

app = FastAPI()
app.include_router(log.router)
