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

        categories_block = soup.find_all("div", class_="b_control")

        nav_categories_list = categories_block[0].find_all(
            "a", class_="b_nav-item")
        link = nav_categories_list[1]
        relative_link = link["href"].lstrip("/")
        categories.append(
            {
                "name": link.get_text(strip=True),
                "link": (
                    link["href"]
                    if link["href"].startswith("https")
                    else url + relative_link
                ),
            }
        )

        all_categories = categories_block[0].find_all(
            "div", class_="b_menu-item")

        stop_categories = [
            "Цивилизация",
            "Спецпроекты",
            "Редакция",
            "Тесты",
            "Эксклюзивы",
            "Инфографика",
            "Фото",
            "Мнения",
        ]

        for element in all_categories:
            link = element.find("a")

            if link.get_text(strip=True) in stop_categories:
                continue

            if link["href"] == "/lifestyle/":
                link["href"] = link["href"].replace("/lifestyle", "/style")

            relative_link = link["href"].lstrip("/")
            category = {
                "name": link.get_text(strip=True),
                "link": (
                    link["href"]
                    if link["href"].startswith("https")
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

        articles_blocks = soup.find_all("div", class_="w_col4")

        for index, block in enumerate(articles_blocks):
            if len(articles_blocks) > 1 and index == 0:
                continue

            rows = block.find_all("div", class_="row", recursive=False)

            for row in rows:
                links = row.find_all("a")
                for link in links:
                    if "m_simple" not in link.get(
                        "class", []
                    ) and "b_newslist-showmorebtn" not in link.get("class", []):
                        href = link["href"]

                        if href and href.startswith("/"):
                            href_parts = href.split("/", 2)
                            if len(href_parts) > 2:
                                href = "/" + href_parts[2]
                            else:
                                href = "/"

                        link_href = (
                            href if href.startswith(
                                "https") else url.rstrip("/") + href
                        )

                        if link_href not in existing_articles:
                            article = {}

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

        article_title_h1 = soup.find_all("h1", class_="headline")
        article_title_h2 = soup.find_all("h2", class_="headline")
        article_title = article_title_h1 if article_title_h1 else article_title_h2
        article_title = article_title[0].get_text(strip=True)

        breadcrumbs = soup.find_all("div", class_="breadcrumb")
        article_date = breadcrumbs[0].find("time").get_text(strip=True)
        article_date = parse_time_text(article_date, "gazeta")

        all_text = []

        content_intro_div = soup.find_all("div", class_="b_article-intro")
        content_text_div = soup.find_all("div", class_="b_article-text")

        if content_intro_div:
            content_intro_div = content_intro_div[0].get_text(
                separator=" ", strip=True)
            all_text.append(content_intro_div)
        if content_text_div:
            for incut in content_text_div[0].find_all("div", class_="b_article-incut"):
                incut.decompose()
            for incut in content_text_div[0].find_all("aside", class_="b_article-incut"):
                incut.decompose()
            content_text_div = content_text_div[0].get_text(
                separator=" ", strip=True)
            all_text.append(content_text_div)

        full_text = " ".join(all_text)

        article = {"date": article_date,
                   "text": full_text, "title": article_title}
        return article

    except Exception as e:
        parser_logger.error(f"Error parsing article {url}: {e}", exc_info=False)
        pass
    return {}


async def async_gazeta_news_scrapper(session: ClientSession) -> List[Dict[str, str]]:
    main_url = "https://www.gazeta.ru/"
    gazeta_news = []

    categories = await parse_categories(session, main_url)
    if not categories:
        parser_logger.warning("No categories found, aborting scraping.")
        return gazeta_news
    for category in categories:
        articles = await parse_articles_in_category(session, category["link"])

        for element in articles:
            full_article = await parse_articles(session, element["link"])
            if full_article:
                single_article = {
                    "news_source_name": "gazeta",
                    "news_source_link": main_url,
                    "category_name": category["name"],
                    "category_link": category["link"],
                    "article_date": full_article.get("date", ""),
                    "article_link": element["link"],
                    "article_title": full_article.get("title", ""),
                    "article_text": full_article.get("text", ""),
                }

                gazeta_news.append(single_article)

    return gazeta_news
