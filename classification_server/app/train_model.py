from settings.paths import DATA_FILE_PATH
from app.helpers.preprocess_functions import preprocess_data
import os
from navec import Navec
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from joblib import dump
import aiohttp

def text_to_vector(text, model):
    words = text.split()
    word_vectors = []

    for word in words:
        try:
            word_vectors.append(model[word])
        except KeyError:
            continue

    if word_vectors:
        return np.mean(word_vectors, axis=0)
    else:
        return np.zeros(model.vector_size)
    
async def download_file(url, dest):
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            if response.status == 200:
                total_size = int(response.headers.get('Content-Length', 0))
                downloaded_size = 0

                with open(dest, 'wb') as f:
                    while True:
                        chunk = await response.content.read(1024)
                        if not chunk:
                            break
                        f.write(chunk)
                        downloaded_size += len(chunk)

                        if total_size > 0:
                            print(
                                f"Downloaded {downloaded_size} of {total_size} bytes", end='\r')
                print(f"File downloaded: {dest}")
            else:
                print(f"Error while downloading: {response.status}")
    
async def train_model():
    data_path = DATA_FILE_PATH
    print(data_path)

    df = preprocess_data(data_path)

    print("done")

    file_path = "navec/navec_hudlit_v1_12B_500K_300d_100q.tar"
    url = "https://storage.yandexcloud.net/natasha-navec/packs/navec_hudlit_v1_12B_500K_300d_100q.tar"

    temp_dir = "navec"
    if not os.path.exists(temp_dir):
        os.makedirs(temp_dir)

    if not os.path.exists(file_path):
        print("File not found, starting download...")
        await download_file(url, file_path)
    else:
        print("The file has already been downloaded.")

    navec = Navec.load(file_path)

    X = np.array([text_to_vector(text, navec) for text in df['text']])
    y = df['category_encoded'].astype(int)

    classifier = RandomForestClassifier(
        n_estimators=100, criterion='entropy', random_state=0).fit(X, y)

    dump(classifier, 'model.joblib')

    print("The model is trained and ready for use.")