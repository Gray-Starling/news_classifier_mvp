from joblib import load
import pymorphy3
from nltk.corpus import stopwords
import re
import numpy as np
from navec import Navec
import json



async def get_predict(text):
    
    classifier = load('model/model.joblib')
    navec_path = "navec/navec_hudlit_v1_12B_500K_300d_100q.tar"
    categories_path = 'model/category_mapping.json'

    navec = Navec.load(navec_path)

    morph = pymorphy3.MorphAnalyzer()
    stopwords_ru = stopwords.words("russian")
    custom_stopwords = []

    def deEmojify(text):
        regrex_pattern = re.compile(pattern = "["
                                    u"\U00000000-\U00000009"
                                    u"\U0000000B-\U0000001F"
                                    u"\U00000080-\U00000400"
                                    u"\U00000402-\U0000040F"
                                    u"\U00000450-\U00000450"
                                    u"\U00000452-\U0010FFFF"
                                    "]+", flags = re.UNICODE)
        return regrex_pattern.sub(r'',text)

    def process_text(text):
        tokens = []
        cleaned_text = re.sub(r'\d+', '', text)
        cleaned_text = re.sub(r'[!"#$%&\'()*+,\-./:;<=>?\[@\\\]^_`{|}~]', '', cleaned_text)
        cleaned_text = deEmojify(cleaned_text)
        for token in cleaned_text.split():
            if token and token not in stopwords_ru:
                token = token.strip()
                token = morph.parse(token)[0].normal_form  
                if token not in custom_stopwords:
                    tokens.append(token)          
        return " ".join(tokens)
    
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
    
    text = text.lower()
    text = process_text(text)
    text = text_to_vector(text, navec)
    yy = classifier.predict(np.array([text]))

    with open(categories_path, 'r', encoding='utf-8') as f:
        category_mapping = json.load(f)

    predict = category_mapping[str(yy[0])]

    result = {
        "status": "predicted",
        "predict": predict
    }

    return result