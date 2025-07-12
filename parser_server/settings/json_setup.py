import json
import os
from settings.paths import JSON_DIR_PATH

def initialize_json_file():
    """Создает JSON-файл с пустыми значениями, если он не существует."""
    try:
        if not os.path.exists(JSON_DIR_PATH):
            initial_data = {
                "dataset_size": "",
                "dataset_last_update": "",
            }
            with open(JSON_DIR_PATH, 'w') as f:
                json.dump(initial_data, f, indent=4)
        return True
    except:
        return False

def update_json_file(key, value):
    """Обновляет значение по заданному ключу в JSON-файле."""
    with open(JSON_DIR_PATH, 'r') as f:
        json_info = json.load(f)

    json_info[key] = value

    with open(JSON_DIR_PATH, 'w', encoding='utf-8') as f:
        json.dump(json_info, f, indent=4, ensure_ascii=False)