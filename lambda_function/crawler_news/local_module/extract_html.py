import html
from bs4 import BeautifulSoup


class Extract:

    @staticmethod
    def extract_text_from_html(raw_html):
        if raw_html == None:
            return None
        else:
            decoded_html = html.unescape(raw_html)  # turn &lt; to <
            soup = BeautifulSoup(decoded_html, 'html.parser')
            return soup.get_text()


