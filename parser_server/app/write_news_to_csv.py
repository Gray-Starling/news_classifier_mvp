import os, csv
from settings.logger_setup import parser_logger, system_logger
from settings.paths import DATA_FILE_PATH
from app.helpers.existing_articles import read_existing_articles
from app.helpers.formats import human_readable_size
from settings.json_setup import update_json_file
from datetime import datetime

def write_news_to_csv(file_path = DATA_FILE_PATH, total_news_list = []):

    if not total_news_list:
        parser_logger.debug(f"No news articles to write. Exiting function.")
        return
    
    existing_articles = read_existing_articles(file_path)

    file_exists = os.path.exists(file_path)
    new_articles_count = 0

    try:
        parser_logger.debug(f"Start writing news to CSV: {file_path}")
        with open(file_path, mode="a", encoding="utf-8", newline="") as file:
            writer = csv.writer(file)
            if not file_exists or os.path.getsize(file_path) == 0:
                writer.writerow([
                    "news_source_name",
                    "news_source_link",
                    "category_name",
                    "category_link",
                    "article_date",
                    "article_link",
                    "article_title",
                    "article_text",
                ])

            for article in total_news_list:
                if article["article_link"] not in existing_articles:
                    writer.writerow([
                        article.get("news_source_name", ""),
                        article.get("news_source_link", ""),
                        article.get("category_name", ""),
                        article.get("category_link", ""),
                        article.get("article_date", ""),
                        article.get("article_link", ""),
                        article.get("article_title", ""),
                        article.get("article_text", ""),
                    ])
                    existing_articles.add(article["article_link"])
                    new_articles_count += 1
        
        parser_logger.debug(f"Finished writing to CSV. New articles added: {new_articles_count}")

        if os.path.exists(file_path):
                file_size = os.path.getsize(file_path)
                readable_size = human_readable_size(file_size)
                system_logger.info(f"📦 CSV файл обновлён — размер: {readable_size}")
                update_json_file("dataset_size", readable_size)
                update_json_file("dataset_last_update", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        else:
                system_logger.warning("⚠️ CSV файл не найден после выполнения скраппера")
    except Exception as e:
        parser_logger.error(f"Error writing to CSV file: {e}", exc_info=True)