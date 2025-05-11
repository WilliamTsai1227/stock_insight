from .extract_html import Extract

class Tidy :
    @staticmethod
    def news_items(news_items: list) -> list:
        parsed = []

        for item in news_items:
            if not item.get("newsId"):
                continue

            news_id = item.get("newsId")
            title = item.get("title") or None
            publishAt = item.get("publishAt") 
            news_url = f"https://news.cnyes.com/news/id/{news_id}"
            summary = item.get("summary") or None
            keyword = item.get("keyword") or []
            category_name = item.get("categoryName") or None
            stock = item.get("stock") or []
            market = item.get("market") or []
            content = item.get("content") or None
            content = Extract.extract_text_from_html(content)
            news_dict = {
                "news_id": news_id,
                "title": title,
                "publishAt": publishAt,
                "url": news_url,
                "summary": summary,
                "keyword": keyword,
                "category": category_name,
                "stock": stock,
                "market": market,
                "content": content
            }

            parsed.append(news_dict)
        return parsed

    @staticmethod
    def db_news_items(news_items: list) -> list:
        db_parsed = []

        for item in news_items:
            if not item.get("newsId"):
                continue

            news_id = item.get("newsId")
            title = item.get("title") or None
            publishAt = item.get("publishAt") 
            news_url = f"https://news.cnyes.com/news/id/{news_id}"
            summary = item.get("summary") or None
            keyword = item.get("keyword") or []
            category_name = item.get("categoryName") or None
            stock = item.get("stock") or []
            market = item.get("market") or []
            content = item.get("content") or None
            content = Extract.extract_text_from_html(content)
            news_dict = {
                "news_id": news_id,
                "title": title,
                "publishAt": publishAt,
                "url": news_url,
                "source":"anue",      #add source but is Hardcoding
                "type":"headline",    #add type but is Hardcoding
                "summary": summary,
                "keyword": keyword,
                "category": category_name,
                "stock": stock,
                "market": market,
                "content": content
            }

            db_parsed.append(news_dict)
        return db_parsed
