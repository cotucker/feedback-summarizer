from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from nltk.tokenize.treebank import TreebankWordDetokenizer
from transformers import AutoTokenizer, AutoModelForSequenceClassification
from sklearn.feature_extraction.text import TfidfVectorizer
import torch
from models.models import Sentiment
import numpy as np
import pandas as pd
from typing import List, Dict
from services.llm_service import get_cluster_name
from nltk.corpus import stopwords
import nltk

model_name = "tabularisai/multilingual-sentiment-analysis"
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForSequenceClassification.from_pretrained(model_name)

def predict_sentiment(texts):
    inputs = tokenizer(texts, return_tensors="pt", truncation=True, padding=True, max_length=512)
    with torch.no_grad():
        outputs = model(**inputs)
    probabilities = torch.nn.functional.softmax(outputs.logits, dim=-1)
    sentiment_map = {0: "Negative", 1: "Negative", 2: "Neutral", 3: "Positive", 4: "Positive"}
    return [sentiment_map[p] for p in torch.argmax(probabilities, dim=-1).tolist()]

def extract_cluster_keywords(texts, labels, top_n=10):
    nltk.download('stopwords', quiet=True)
    cluster_keywords = {}
    stop_words = stopwords.words('english')
    texts = np.array(texts)
    print(f"Number of unique labels: {len(np.unique(labels))}")

    for cluster_id in np.unique(labels):
        if cluster_id == -1:  # шум
            cluster_keywords[cluster_id] = [("NOISE", 1.0)]
            continue

        cluster_texts = texts[labels == cluster_id]
        vectorizer = TfidfVectorizer(
            max_features=1000,
            stop_words=stop_words,
            ngram_range=(1, 2),
            min_df=2,
            max_df=0.8
        )
        tfidf_matrix = vectorizer.fit_transform(cluster_texts)

        if tfidf_matrix.shape[1] == 0:
            cluster_keywords[cluster_id] = []
            continue
        scores = np.array(tfidf_matrix.sum(axis=0)).flatten()
        terms = vectorizer.get_feature_names_out()
        top_indices = np.argsort(scores)[-top_n:][::-1]
        cluster_keywords[cluster_id] = [
            (terms[i], round(scores[i], 3)) for i in top_indices
        ]
    cluster_name_map = {}
    for cluster_id, keywords in cluster_keywords.items():
        if cluster_id == -1:
            cluster_name_map[cluster_id] = "NOISE"
            continue

        keyword_prompt = " ".join([word for word, score in keywords[:3]])

        if keyword_prompt:
            cluster_name_map[cluster_id] = get_cluster_name(keyword_prompt)
        else:
            cluster_name_map[cluster_id] = f"Cluster {cluster_id}"

    print(cluster_name_map)

    cluster_names_list = [cluster_name_map[label] for label in labels]
    return cluster_keywords, cluster_names_list, texts

if __name__ == "__main__":
    texts = [
        "We went over a budget.", "The customer service was disappointing.", "The weather is fine, nothing special.",
        "I like final product."
    ]
    for text, sentiment in zip(texts, predict_sentiment(texts)):
        print(f"Text: {text}\nSentiment: {sentiment}\n")
