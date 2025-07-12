from aiohttp import ClientSession
from typing import List, Dict, Optional
from app.helpers.existing_articles import read_existing_articles
from app.helpers.pars_time_text import parse_time_text
from app.helpers.fetch_html import async_fetch_html
from bs4 import BeautifulSoup
from settings.logger_setup import parser_logger
from settings.paths import DATA_FILE_PATH

async def parse_categories(session: ClientSession, url: str) -> List[Dict[str, str]]:
    try:
        html = await async_fetch_html(session, url)
        soup = BeautifulSoup(html, "html.parser")
        categories = []

        title_divs = soup.find_all("div", class_="cell-extension__table")
        a_tags = title_divs[0].find_all("a")
        for a in a_tags:
            relative_link = a["href"].lstrip("/")
            category = {
                "name": a.get_text(strip=True),
                "link": (
                    a["href"] if a["href"].startswith(
                        "https") else url + relative_link
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
        article_blocks = soup.find_all("div", class_="list-item__content")

        for block in article_blocks:

            a_tags = block.find_all("a", class_="list-item__title")

            for a in a_tags:
                if a["href"] not in existing_articles:
                    article = {}
                    article_title = a.get_text(strip=True)
                    relative_link = a["href"].lstrip("/")
                    link_href = (
                        a["href"]
                        if a["href"].startswith("https")
                        else url + relative_link
                    )
                    article["link"] = link_href
                    article["title"] = article_title
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

        article_date_block = soup.find_all("div", class_="article__info-date")

        article_date = article_date_block[0].find("a").get_text(strip=True)
        article_date = parse_time_text(article_date, "ria")

        content_div = soup.find_all("div", class_="article__body")

        all_text = []

        for div in content_div:
            blocks = div.find_all("div", class_="article__block")
            for block in blocks:
                if block.get("data-type") != "article" and block.get("data-type") != "photolenta":
                    all_text.append(block.get_text(separator=" ", strip=True))

        full_text = " ".join(all_text)

        article = {"date": article_date, "text": full_text}
        return article

    except Exception as e:
        parser_logger.error(f"Error parsing article {url}: {e}", exc_info=False)
        pass
    return {}


async def async_ria_news_scrapper(session: ClientSession) -> List[Dict[str, str]]:
    main_url = "https://ria.ru/"
    ria_news = []

    categories = await parse_categories(session, main_url)
    if not categories:
        parser_logger.warning("No categories found, aborting scraping.")
        return ria_news

    for category in categories: 
        articles = await parse_articles_in_category(session, category["link"])

        for element in articles:
            full_article = await parse_articles(session, element["link"])
            if full_article:
                single_article = {
                    "news_source_name": "ria",
                    "news_source_link": main_url,
                    "category_name": category["name"],
                    "category_link": category["link"],
                    "article_date": full_article.get("date", ""),
                    "article_link": element["link"],
                    "article_title": element["title"],
                    "article_text": full_article.get("text", ""),
                }

                ria_news.append(single_article)

    return ria_news
