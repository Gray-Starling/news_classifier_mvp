import asyncio
import aiohttp

from settings.constants import SLEEPING_TIME
from settings.logger_setup import parser_logger
from settings.paths import DATA_FILE_PATH
from app.fetch_news_from_source import fetch_news_from_source
from app.write_news_to_csv import write_news_to_csv
from app.news_scrappers.rbk import async_rbk_news_scrapper
from app.news_scrappers.lenta import async_lenta_news_scrapper
from app.news_scrappers.ria import async_ria_news_scrapper
from app.news_scrappers.gazeta import async_gazeta_news_scrapper

SCRAPPERS = {
    "RBK": async_rbk_news_scrapper,
    "Lenta": async_lenta_news_scrapper,
    "RIA": async_ria_news_scrapper,
    "Gazeta": async_gazeta_news_scrapper,
}


async def run_scrapper_periodically(sleep_seconds: int = SLEEPING_TIME, data_path: str = DATA_FILE_PATH):
    parser_logger.info("🟢 Scrapper process started")

    while True:
        try:
            parser_logger.info("🚀 Starting the scrapper...")
            async with aiohttp.ClientSession() as session:
                tasks = [
                    asyncio.create_task(fetch_news_from_source(session, source_name, scrapper_function))
                    for source_name, scrapper_function in SCRAPPERS.items()
                ]
                
                with open(data_path, 'a', newline='', encoding='utf-8') as csvfile:
                    for task in asyncio.as_completed(tasks):
                        news = await task
                        write_news_to_csv(DATA_FILE_PATH, news)

            parser_logger.info("✅ Scraping completed")
            parser_logger.info(f"🕒 Waiting for {sleep_seconds // 60} minutes until the next run...\n")
            await asyncio.sleep(sleep_seconds)

        except Exception as e:
            parser_logger.exception(f"❌ Error during scrapper execution: {e}")
            parser_logger.info("🔄 Restarting the scrapper in 10 seconds...")
            await asyncio.sleep(10)


