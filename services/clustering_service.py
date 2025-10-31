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
from models.models import SentimentResponse

def cluster_texts(sentiment_responses: list[SentimentResponse]) -> list[dict]:

        # phrase_clusters.append({
        #     "x": point_x,
        #     "y": point_y,
        #     "z": 0,
        #     "cluster": closest_topic,
        #     "phrase": texts_list[i] + " " + topics_list[i]
        # })
    if not sentiment_responses:
        return []

    df = pd.read_csv('data/data.csv')

    texts_list = [response.text for response in sentiment_responses]
    texts_list.extend(df['Phrase'].tolist())

    abstracts = texts_list
    processed_texts_list = [filter_text_final_version(text) for text in texts_list]

    model = SentenceTransformer('all-MiniLM-L12-v2')
    embeddings = model.encode(processed_texts_list, device='cuda')

    umap_model = UMAP(
        n_components=10, # Reduces dimensionality while preserving essential structure
        min_dist=0.0, # Controls how tightly points cluster together
        metric='cosine', # Measures similarity between embeddings using cosine distance
        random_state=42
    )

    reduced_embeddings = umap_model.fit_transform(embeddings)

    print(f"Shape of reduced embeddings: {reduced_embeddings.shape}")

    # We fit the model and extract the clusters
    hdbscan_model = HDBSCAN(
        min_cluster_size=60, # Ensures statistically significant groupings
        metric='euclidean', # Measures distance in reduced space
        cluster_selection_method='eom' # Optimizes cluster boundary detection
    ).fit(reduced_embeddings)
    clusters = hdbscan_model.labels_

    # How many clusters did we generate?
    print(f"Number of clusters: {len(set(clusters))}")


    # # Print first three documents in cluster 0
    # cluster = 2
    # for index in np.where(clusters==cluster)[0]:
    #     print(abstracts[index][:300] + "... \n")


    # Reduce 384-dimensional embeddings to 3 dimensions
    reduced_embeddings_3d = UMAP(
    n_components=3,
    min_dist=0.0,
    metric='cosine',
    random_state=42
    ).fit_transform(embeddings)

    phrase_clusters = []

    for i, text in enumerate(texts_list):
        phrase_clusters.append({
            "x": float(reduced_embeddings_3d[i][0]),
            "y": float(reduced_embeddings_3d[i][1]),
            "z": float(reduced_embeddings_3d[i][2]),
            "cluster": str(clusters[i]),
            "phrase": text
        })

    return phrase_clusters
