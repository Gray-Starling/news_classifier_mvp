from aiohttp import ClientSession
from typing import Callable, List, Dict
from settings.logger_setup import parser_logger

async def fetch_news_from_source(session: ClientSession, scrapper_name: str, scrapper_function: Callable[[ClientSession], List[Dict]]) -> List[Dict]:
    try:
        parser_logger.debug(f"Start scraping {scrapper_name}")
        news = await scrapper_function(session)
        parser_logger.debug(f"Fetched {len(news)} articles from {scrapper_name}.")
        return news
    except Exception as e:
        parser_logger.error(f"Error fetching {scrapper_name} news: {e}", exc_info=True)
        return []