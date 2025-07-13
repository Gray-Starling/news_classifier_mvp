from tqdm import tqdm
import tensorflow as tf
import pandas as pd
import pymorphy3
import re
from nltk.corpus import stopwords
from sklearn.preprocessing import LabelEncoder
import json

def del_duplicates(df):
    df = df.drop_duplicates(subset=["article_link"])
    return df

def del_columns(df):
    df = df.drop(["news_source_name", "news_source_link", "category_link", "article_date", "article_link"], axis=1)
    return df

def to_lower_str(df):
    df = df.map(lambda x: x.lower() if isinstance(x, str) else x)
    return df

def mapping_category(df):
    category_mapping = {
        'политика': 'политика',
        'силовые структуры': 'политика',
        'бывший ссср': 'политика',
        'армия': 'политика',
        'россия': 'политика',

        'экономика': 'экономика и бизнес',
        'бизнес': 'экономика и бизнес',
        'финансы': 'экономика и бизнес',

        'религия': 'общество и культура',
        'общество': 'общество и культура',
        'культура': 'общество и культура',
        'спорт': 'общество и культура',
        'путешествия': 'разное',
        'ценности': 'разное',
        
        'технологии и медиа': 'технологии и наука',
        'наука и техника': 'технологии и наука',
        'интернет и сми': 'технологии и наука',
        'наука': 'технологии и наука',
        'технологии': 'технологии и наука',
        'авто': 'технологии и наука',

        'среда обитания': 'разное',
        'происшествия': 'разное',
        'база знаний': 'разное',
        'мир': 'разное',
        'забота о себе': 'разное',
        'в мире': 'разное',
        'стиль': 'разное',
        'из жизни': 'разное',
    }

    df["category_name"] = df["category_name"].map(category_mapping)
    df["category_name"] = df["category_name"].fillna('разное')

    return df

def del_empty_text(df):
    df = df.dropna(subset=['article_text'])
    return df

def text_gluing(df):
    df['article_title'] = df.apply(lambda row: '' if row['article_title'] in row['article_text'] else row['article_title'], axis=1)
    df['text'] = df['article_title'] + " " + df['article_text']
    df.drop(columns=['article_title', 'article_text'], inplace=True)
    return df

def preprocess_text(df):
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
    
    df["text"] = df["text"].progress_apply(process_text)

    return df

def cleaning_custom_stopwords(df):
    custom_stopwords = [
        "год", "риа", "это",
        "также", "изз", "тот",
        "очень", "сам", "этот",
        "наш",
    ]

    def process_text(text):
        tokens = []
        for token in text.split():
            if token and token not in custom_stopwords:
                tokens.append(token)
        return " ".join(tokens)  

    df["text"] = df["text"].apply(process_text)

    return df

def balancing_data(df):
    balanced_df = pd.DataFrame(columns=df.columns)

    df['word_count'] = df['text'].apply(lambda x: len(str(x).split()))
    avg_word_count = df['word_count'].mean()

    min_samples = df['category_name'].value_counts().min()

    def balancing_samples(category_data):
        category_avg_word_count = category_data['word_count'].mean()

        while len(category_data) > min_samples:
            if category_avg_word_count > avg_word_count:
                category_data = category_data.drop(category_data['word_count'].idxmax())
            else:
                category_data = category_data.drop(category_data['word_count'].idxmin())

            category_avg_word_count = category_data['word_count'].mean()

        return category_data.reset_index(drop=True)
    
    for category in df["category_name"].unique():
        category_data = df[df["category_name"] == category].copy()
        balanced_category_data = balancing_samples(category_data)
        balanced_df = pd.concat([balanced_df, balanced_category_data], ignore_index=True)

    return balanced_df

def del_big_text(df):
    df['text_length'] = df['text'].str.len()

    final_df = df.copy()

    for index, row in df.iterrows():
        if row['text_length'] < 200 or row['text_length'] > 10000:
            final_df.drop(index, inplace=True)

    return final_df

def category_encoding(df):
    try:
        label_encoder = LabelEncoder()
        df["category_encoded"] = label_encoder.fit_transform(df["category_name"])
        category_mapping = {index: label for index, label in enumerate(label_encoder.classes_)}

        with open('./category_mapping.json', 'w', encoding='utf-8') as f:
            json.dump(category_mapping, f, ensure_ascii=False)
    except Exception as e:
        print(f"An error occurred: {e}")

    return df

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