from settings.logger_setup import system_logger
from settings.paths import DATA_DIR_PATH
from settings.json_setup import initialize_json_file
import os

def prelaunch_check():
    system_logger.debug("⚠️⚠️⚠️ Running in dev mode ⚠️⚠️⚠️")

    if not os.path.exists(DATA_DIR_PATH):
        try:
            os.makedirs(DATA_DIR_PATH)
            system_logger.debug(f"Directory {DATA_DIR_PATH} has been created.")
        except Exception as e:
            system_logger.debug(f"Failed to create directory {DATA_DIR_PATH}: {e}")
            return False
    else:
        system_logger.debug(f"Directory {DATA_DIR_PATH} already exists.")

    if not initialize_json_file():
        system_logger.debug("Failed to initialize info.json file.")
        return False
    else:
        system_logger.debug("info.json file has been initialized.")


    return True



        
    