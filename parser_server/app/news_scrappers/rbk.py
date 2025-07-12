from aiohttp import ClientSession
from typing import List, Dict, Optional
from app.helpers.existing_articles import read_existing_articles
from app.helpers.fetch_html import async_fetch_html
from bs4 import BeautifulSoup
from settings.logger_setup import parser_logger
from settings.paths import DATA_FILE_PATH

async def parse_categories(session: ClientSession, url: str) -> List[Dict[str, str]]:
    try:
        html = await async_fetch_html(session, url)
        soup = BeautifulSoup(html, "html.parser")

        footer_title_divs = soup.find_all("div", class_="footer__title")
        for div in footer_title_divs:
            if div.get_text(strip=True) == "Рубрики":
                ul = div.find_next("ul")
                if ul:
                    categories = []
                    for li in ul.find_all("li"):
                        a = li.find("a")
                        if a:
                            if a.get_text(strip=True) == "Биографии":
                                continue
                            category = {
                                "name": a.get_text(strip=True),
                                "link": (
                                    a["href"]
                                    if a["href"].startswith("https")
                                    else url + a["href"]
                                ),
                            }
                            categories.append(category)
                    return categories
    except Exception as e:
        parser_logger.error(f"Error parsing categories: {e}", exc_info=False)
        pass
    return []


async def parse_articles_in_category(session: ClientSession, url: str) -> List[Dict[str, str]]:
    file_path = DATA_FILE_PATH

    existing_articles = read_existing_articles(file_path)

    try:
        html = await async_fetch_html(session, url)
        soup = BeautifulSoup(html, "html.parser")

        articles = []
        article_elements = soup.find_all(
            "div", class_="item__wrap l-col-center")

        for element in article_elements:
            article = {}
            article_link = element.find("a")

            if article_link["href"] not in existing_articles:
                article["link"] = article_link["href"]

                articles.append(article)
        return articles
    except Exception as e:
        parser_logger.error(f"Error parsing articles in category {url}: {e}", exc_info=False)
        pass
    return []


async def parse_articles(session: ClientSession, url: str) -> Optional[Dict[str, str]]:
    try:
        html = await async_fetch_html(session, url)
        soup = BeautifulSoup(html, "html.parser")

        time_span = soup.find("time")['datetime']
        
        article_title = soup.find("h1").get_text(strip=True)
        article_text_div = soup.find_all(
            "div", class_="article__text article__text_free"
        )

        if not article_text_div:
            parser_logger.warning(f"No article text found in {url}")
            return {}

        for incut_class in [
            "article__main-image",
            "article__inline-item",
            "banner__container__color",
            "thg",
            "article__ticker",
        ]:
            for incut in article_text_div[0].find_all("div", class_=incut_class):
                incut.decompose()
            for incut in article_text_div[0].find_all("span", class_=incut_class):
                incut.decompose()

        article_text = article_text_div[0].get_text(separator=" ", strip=True)

        return {"title": article_title, "text": article_text, "date": time_span}
    except Exception as e:
        parser_logger.error(f"Error parsing article {url}: {e}", exc_info=False)
        pass
    return {}


async def async_rbk_news_scrapper(session: ClientSession) -> List[Dict[str, str]]:
    main_url = "https://www.rbc.ru/"
    rbk_news = []
    categories = await parse_categories(session, main_url)
    if not categories:
        parser_logger.warning("No categories found, aborting scraping.")
        return rbk_news
    
    for category in categories:
        articles = await parse_articles_in_category(session, category["link"])

        for element in articles:
            full_article = await parse_articles(session, element["link"])
            if full_article:
                single_article = {
                    "news_source_name": "rbk",
                    "news_source_link": main_url,
                    "category_name": category["name"],
                    "category_link": category["link"],
                    "article_date": full_article.get("date", ""),
                    "article_link": element["link"],
                    "article_title": full_article.get("title", ""),
                    "article_text": full_article.get("text", ""),
                }

                rbk_news.append(single_article)
            
    return rbk_news
