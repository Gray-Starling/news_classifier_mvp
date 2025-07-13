import os
from tools.download_data import download_data
from tools.preprocess_functions import del_duplicates, del_columns, to_lower_str, mapping_category, del_empty_text, text_gluing, preprocess_text, cleaning_custom_stopwords, balancing_data, del_big_text, category_encoding

import tensorflow as tf
import pandas as pd
from tqdm import tqdm
import aiohttp
from navec import Navec
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from joblib import dump
import shutil


def preprocess_data(file_path):
    tqdm.pandas()

    is_cuda = tf.test.is_built_with_cuda()
    if is_cuda and len(tf.config.list_physical_devices('GPU')) >= 0:
        print(f"GPU is available.")
    else:
        print("GPU not available, CPU used")

    print("Reading csv file...")
    df = pd.read_csv(file_path)

    print("Removing duplicates...")
    df = del_duplicates(df)

    print("Removing unnecessary columns...")
    df = del_columns(df)

    print("Convert text to lowercase...")
    df = to_lower_str(df)

    print("Transforming categories...")
    df = mapping_category(df)

    print("Removing empty lines of text...")
    df = del_empty_text(df)

    print("Text gluing...")
    df = text_gluing(df)

    print("Text preprocessing...")
    df = preprocess_text(df)

    print("Cleaning up custom stopwords...")
    df = cleaning_custom_stopwords(df)

    print("Data Balancing...")
    df = balancing_data(df)

    print("Balancing text length...")
    df = del_big_text(df)

    print("Convert categories to numeric value...")
    df = category_encoding(df)

    return df


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


async def train(df):
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

    dump(classifier, 'model/model.joblib')

    print("The model is trained and ready for use.")


async def train_model():
    data_path = 'data/data.csv'

    if not os.path.exists(data_path):
        print("Data not found")
        print("Starting data loading")
        try:
            await download_data(data_path)
            print("Starting the model training process")
        except Exception as e:
            print(e)

    df = preprocess_data(data_path)

    await train(df)
