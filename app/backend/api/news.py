from fastapi import APIRouter

router = APIRouter()


@router.get("news/{news_id}"):
def get_news():