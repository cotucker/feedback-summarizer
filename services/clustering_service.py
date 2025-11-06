from dotenv import load_dotenv
import numpy as np
import pandas as pd
import requests
from sentence_transformers import SentenceTransformer
from umap import UMAP
from hdbscan import HDBSCAN
import plotly.express as px
import matplotlib.pyplot as plt
from services.nlp_service import filter_text_final_version
from services.llm_service import generate_cluster_name
from services.file_handler_service import create_dataset_from_sentiment_response_list
from models.models import SentimentResponse
from fastopic import FASTopic
from topmost import Preprocess

def cluster_texts(sentiment_responses: list[SentimentResponse]) -> (list[dict], list[SentimentResponse]):

    if not sentiment_responses:
        return []

    data_size = len(sentiment_responses)

    df = pd.read_csv('data/data.csv')

    texts_list = [response.text for response in sentiment_responses]
    sentiments = [response.sentiment for response in sentiment_responses]
    texts_list.extend(df['Phrase'].tolist())

    abstracts = texts_list
    processed_texts_list = [filter_text_final_version(text) for text in texts_list]

    model = SentenceTransformer('all-MiniLM-L12-v2')
    embeddings = model.encode(processed_texts_list, device='cuda')

    umap_model = UMAP(
        n_components=12,
        min_dist=0.0,
        metric='cosine',
        random_state=67
    )

    reduced_embeddings = umap_model.fit_transform(embeddings)

    print(f"Shape of reduced embeddings: {reduced_embeddings.shape}")

    hdbscan_model = HDBSCAN(
        min_cluster_size=70,
        metric='euclidean',
        cluster_selection_method='eom'
    ).fit(reduced_embeddings)
    clusters = hdbscan_model.labels_

    print(f"Number of clusters: {len(set(clusters))}")

    map = {}

    for i, cluster in enumerate(clusters):
        if i == data_size:
            break
        if cluster not in map:
            map[cluster] = []
        map[cluster].append(processed_texts_list[i])

    for cluster, texts in map.items():
        test = get_topics_of_cluster(texts)
        print(f"test: {test}")
        map[cluster] = generate_cluster_name(test)
        print(f"Topics of cluster {cluster}: {map[cluster]}")



    reduced_embeddings_3d = UMAP(
    n_components=3,
    min_dist=0.0,
    metric='cosine',
    random_state=67
    ).fit_transform(embeddings)

    phrase_clusters = []
    sentiments_list: list[SentimentResponse] = []

    for i, text in enumerate(texts_list[:data_size]):
        sentiment = sentiments[i]
        phrase_clusters.append({
            "x": float(reduced_embeddings_3d[i][0]),
            "y": float(reduced_embeddings_3d[i][1]),
            "z": float(reduced_embeddings_3d[i][2]),
            "cluster": map[clusters[i]],
            "phrase": text,
            "sentiment": sentiment.value
        })
        sentiments_list.append(SentimentResponse(text = text, sentiment = sentiment, topic = map[clusters[i]]))


    create_dataset_from_sentiment_response_list(sentiments_list)
    return phrase_clusters, sentiments_list


def get_topics_of_cluster(texts: list[str]) -> str:
    preprocess = Preprocess()

    model = FASTopic(1, preprocess, verbose=False)
    top_words, doc_topic_dist = model.fit_transform(texts)
    return ''.join(top_words)
