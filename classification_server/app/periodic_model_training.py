from settings.logger_setup import model_logger, system_logger
from settings.paths import JSON_DIR_PATH, MODEL_PATH
import json
from datetime import datetime, timedelta
import os
import asyncio
from app.train_model import train_model

async def periodic_model_training():

    def load_json_data(json_path):
        with open(json_path, 'r') as json_file:
            return json.load(json_file)

    n = 10

    while True:
        if not os.path.exists(MODEL_PATH):
            data = load_json_data(JSON_DIR_PATH)
            dataset_size_str = data['dataset_size']
            dataset_size = float(dataset_size_str.split()[0])

            if dataset_size < n:
                system_logger.debug(f"Dataset size is less than {n} MB. Waiting for more data...")
            else:
                await train_model()
        else:
            data = load_json_data(JSON_DIR_PATH)
            last_update_str = data['dataset_last_update']
            last_update_date = datetime.strptime(last_update_str, '%Y-%m-%d %H:%M:%S')

            if last_update_date < datetime.now() - timedelta(days=30):
                system_logger.debug("Dataset was last updated more than a month ago. Retraining the model...")
                await train_model()
            else:
                system_logger.debug("Model is up to date.")

        await asyncio.sleep(6000)