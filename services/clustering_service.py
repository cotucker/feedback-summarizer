import numpy as np
import pandas as pd
import requests
from sklearn.decomposition import PCA
from sklearn.cluster import KMeans
from models.models import SentimentResponse
from services.llm_service import get_embedding

def cluster_texts(sentiment_responses: list[SentimentResponse], n_clusters=5) -> list[dict]:


    texts_list = [response.text for response in sentiment_responses]

    embeddings = get_embedding(texts_list)

    pca = PCA(n_components=2)
    reduced_data = pca.fit_transform(embeddings)

    reduced_data_list: list[list] = reduced_data.tolist()
    print(reduced_data_list[0][0])

    kmeans = KMeans(n_clusters=n_clusters, n_init=5, max_iter=500, random_state=42)
    kmeans.fit(embeddings)

    results = pd.DataFrame()

    if kmeans.labels_ is not None:
        clusters_list = kmeans.labels_.tolist()
    else:
        raise ValueError("KMeans failed to converge")

    # assert (len(texts_list) == len(reduced_data_list))

    phrase_clusters: list[dict] = [
        {
            "x": x[0],
            "y": x[1],
            "cluster": sentiment_responses[i].sentiment,
            "phrase": texts_list[i]
        }

        for i, x in enumerate(reduced_data_list)
    ]

    return phrase_clusters
