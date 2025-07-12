from bs4 import BeautifulSoup
from aiohttp import ClientSession
from typing import List, Dict, Optional
from app.helpers.fetch_html import async_fetch_html
from app.helpers.pars_time_text import parse_time_text
from app.helpers.existing_articles import read_existing_articles
from settings.logger_setup import parser_logger
from settings.paths import DATA_FILE_PATH

async def parse_categories(session: ClientSession, url: str) -> List[Dict[str, str]]:
    try:
        html = await async_fetch_html(session, url)
        soup = BeautifulSoup(html, "html.parser")

        categories_ul = soup.find_all("ul", class_="menu__nav-list")

        categories = []

        for ul in categories_ul:
            for li in ul.find_all("li", class_="menu__nav-item"):
                a_tag = li.find("a", class_="menu__nav-link _is-extra")

                if a_tag:

                    if a_tag.get_text(strip=True) == "Главное":
                        continue

                    relative_link = a_tag["href"].lstrip("/")
                    category = {
                        "name": a_tag.get_text(strip=True),
                        "link": (
                            a_tag["href"]
                            if a_tag["href"].startswith("https")
                            else url + relative_link
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
        article_blocks = soup.find_all("div", class_="rubric-page__container")

        for block in article_blocks:
            first_block = block.find_all("div", class_="longgrid-feature-list")
            other_blocks = block.find_all("div", class_="longgrid-list")

            for element in first_block:
                links = element.find_all("a")
                for link in links:
                    relative_link = link["href"].lstrip("/")
                    article = {}
                    link_href = (
                            link["href"]
                            if link["href"].startswith("https")
                            else "https://lenta.ru/" + relative_link
                        )
                    if link_href not in existing_articles:
                        article["link"] = link_href
                        articles.append(article)
            for element in other_blocks:
                links = element.find_all("a")
                for link in links:
                    relative_link = link["href"].lstrip("/")
                    article = {}
                    link_href = (
                            link["href"]
                            if link["href"].startswith("https")
                            else "https://lenta.ru/" + relative_link
                        )
                    if link_href not in existing_articles:
                        article["link"] = link_href
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

        article_container = soup.find_all("div", class_="topic-page__container")
        article = {}
        for container in article_container:
            time_a_premium = container.find_all("a", class_="premium-header__time")
            time_a_regular = container.find_all("a", class_="topic-header__time")

            if time_a_premium:
                article["date"] = parse_time_text(
                    time_a_premium[0].get_text(strip=True),
                    "lenta"
                )
            if time_a_regular:
                article["date"] = parse_time_text(
                    time_a_regular[0].get_text(strip=True),
                    "lenta"
                )

            article["title"] = container.find("h1").get_text(separator=" ", strip=True)

            article_content_div = container.find_all("div", class_="topic-body")
            
            for incut in article_content_div[0].find_all("a", class_="topic-body__origin"):
                incut.decompose()
                
            for incut in article_content_div[0].find_all("div", class_="topic-body__title-image"):
                incut.decompose()
                
            for incut in article_content_div[0].find_all("div", class_="js-scroll-to-site-container"):
                incut.decompose()
                
            for incut in article_content_div[0].find_all("div", class_="box-inline-topic"):
                incut.decompose()
                
            for incut in article_content_div[0].find_all("div", class_="box-gallery"):
                incut.decompose()
                
            for incut in article_content_div[0].find_all("figure", class_="picture"):
                incut.decompose()
                
            article["text"] = article_content_div[0].get_text(separator=" ", strip=True)

            return article

    except Exception as e:
        parser_logger.error(f"Error parsing article {url}: {e}", exc_info=False)
        pass
    return {}


async def async_lenta_news_scrapper(session: ClientSession) -> List[Dict[str, str]]:
    main_url = "https://lenta.ru/"
    lenta_news = []

    categories = await parse_categories(session, main_url)
    if not categories:
        parser_logger.warning("No categories found, aborting scraping.")
        return lenta_news

    for category in categories:
        articles = await parse_articles_in_category(session, category["link"])
        for element in articles:
            full_article = await parse_articles(session, element["link"])
            if full_article:
                single_article = {
                    "news_source_name": "lenta",
                    "news_source_link": main_url,
                    "category_name": category["name"],
                    "category_link": category["link"],
                    "article_date": full_article.get("date", ""),
                    "article_link": element["link"],
                    "article_title": full_article.get("title", ""),
                    "article_text": full_article.get("text", ""),
                }
                lenta_news.append(single_article)
            

    return lenta_news
