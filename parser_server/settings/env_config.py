# from dotenv import load_dotenv
from pathlib import Path
import os

# load_dotenv()

# DEPLOY_MODE = os.getenv("DEPLOY_MODE", "dev")
DEPLOY_MODE = os.environ.get("DEPLOY_MODE", "dev").lower()

# SLEEPING_TIME = 600

# # Называем директории
# DATA_DIR_PATH = "shared_data"

# # Называем файлы
# DATA_FILE_NAME = "news_data.csv"
# # NEWS_DATA_PATH = "./news_data.csv"

# BASE_PROJECT_DIR = Path(__file__).resolve().parent.parent.parent
# BASE_DIR = BASE_PROJECT_DIR / "parser_server"
# DATA_DIR = BASE_PROJECT_DIR / DATA_DIR_PATH
# DATA_FILE_PATH = DATA_DIR / DATA_FILE_NAME

# LOGS_DIR_PATH = BASE_PROJECT_DIR / "logs"
