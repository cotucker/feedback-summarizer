from dotenv import load_dotenv
import numpy as np
import pandas as pd
import requests
from sentence_transformers import SentenceTransformer
from umap import UMAP
from sklearn.manifold import TSNE
from hdbscan import HDBSCAN
import optuna
from sklearn.cluster import SpectralClustering, KMeans, BisectingKMeans
from sklearn.metrics import silhouette_score, davies_bouldin_score, calinski_harabasz_score
from sklearn.metrics.pairwise import cosine_distances
import plotly.express as px
import matplotlib.pyplot as plt
from services.nlp_service import predict_sentiment, extract_cluster_keywords
from services.llm_service import generate_cluster_name
from services.file_handler_service import create_dataset_from_sentiment_response_list
from models.models import SentimentResponse, Subtext

REDUCED_EMBEDDINGS: list = []
EMBEDDINGS: list = []
START: int = 2
END: int = 10
BEST_N: int = 0

def objective(trial):
    num_clusters = trial.suggest_int('num_clusters', START, END)
    score = spectral_clustering(num_clusters)[0]
    return score

def spectral_clustering(num_clusters: int):
    score = -1.0
    db_score = float('inf')
    if num_clusters < 2:
        print("Silhouette Score not calculated: num_clusters must be >= 2.")
        return score
    clustering = SpectralClustering(
            n_clusters=num_clusters,
            assign_labels='discretize',
            gamma=1.0,
            affinity='rbf',
            n_jobs=1,
            random_state=67).fit(REDUCED_EMBEDDINGS)

    spectral_clusters = clustering.labels_

    print(f"Number of unique labels: {len(np.unique(spectral_clusters))}")


    if num_clusters > 1:
        try:
            score = silhouette_score(REDUCED_EMBEDDINGS, spectral_clusters, metric='euclidean')
            print(f"Cluster Quality (Silhouette Score): {score:.4f}")

            db_score = davies_bouldin_score(REDUCED_EMBEDDINGS, spectral_clusters)
            print(f"Cluster Quality (Davies-Bouldin Index): {db_score:.4f}")

            ch_score = calinski_harabasz_score(REDUCED_EMBEDDINGS, spectral_clusters)
            print(f"Cluster Quality (Calinski-Harabasz Index): {ch_score:.4f}")

            intra = np.mean([cosine_distances(EMBEDDINGS[spectral_clusters==i]).mean()
                             for i in range(num_clusters)])
            inter = np.mean([cosine_distances(
                EMBEDDINGS[spectral_clusters==i].mean(axis=0).reshape(1,-1),
                EMBEDDINGS[spectral_clusters==j].mean(axis=0).reshape(1,-1)
            ) for i in range(num_clusters) for j in range(i+1, num_clusters)])

            ratio = intra / inter
            print(f"Cluster Quality (Intra/Inter Ratio): {ratio:.4f}")

        except ValueError as e:
            print(f"Could not calculate Silhouette Score: {e}")

    return db_score + 1/score, spectral_clusters

def cluster_texts(sentiment_responses: list[Subtext]) -> tuple[list[dict], list[SentimentResponse]]:
    global EMBEDDINGS, REDUCED_EMBEDDINGS

    if not sentiment_responses:
        return ([], [])

    data_size = len(sentiment_responses)

    texts_list = [response.text for response in sentiment_responses]
    sentiments = predict_sentiment(texts_list)

    abstracts = texts_list

    model = SentenceTransformer('all-MiniLM-L12-v2')
    EMBEDDINGS = model.encode(texts_list, device='cuda')

    umap_model = UMAP(
        n_components=25,
        min_dist=0.1,
        metric='cosine',
        random_state=67
    )

    REDUCED_EMBEDDINGS = umap_model.fit_transform(EMBEDDINGS)

    print(f"Shape of reduced embeddings: {REDUCED_EMBEDDINGS.shape}")

    n = len(REDUCED_EMBEDDINGS)

    silhouette_scores = []
    range_n_clusters = range(2, int(np.sqrt(n)))

    max_silhouette_score = -1.0
    min_silhouette_score = 1.0
    best_n_clusters = -1
    worst_n_clusters = -1

    for n_clusters in range_n_clusters:
        kmeans = KMeans(n_clusters=n_clusters, init='k-means++', random_state=67)
        cluster_labels = kmeans.fit_predict(REDUCED_EMBEDDINGS)
        silhouette_avg = silhouette_score(REDUCED_EMBEDDINGS, cluster_labels, metric='cosine') #+ 1/davies_bouldin_score(REDUCED_EMBEDDINGS, cluster_labels)
        silhouette_scores.append(silhouette_avg)
        print(f"For n_clusters = {n_clusters}, the average silhouette_score is : {silhouette_avg}")

        if silhouette_avg > max_silhouette_score:
            max_silhouette_score = silhouette_avg
            best_n_clusters = n_clusters
        if silhouette_avg < min_silhouette_score:
            min_silhouette_score = silhouette_avg
            worst_n_clusters = n_clusters

    print(f"\nMaximum Silhouette Score: {max_silhouette_score:.4f} for n_clusters = {best_n_clusters}")
    print(f"Minimum Silhouette Score: {min_silhouette_score:.4f} for n_clusters = {worst_n_clusters}")

    tuple = sorted((best_n_clusters, worst_n_clusters))

    global BEST_N
    BEST_N = best_n_clusters


    global START, END

    START = tuple[0]
    END = tuple[1]

    # study = optuna.create_study(direction='minimize')
    # study.optimize(objective, n_trials=100, n_jobs=2)

    # best_trial = study.best_trial
    # print(f"Best trial value: {best_trial.value}")
    # print(f"Best trial parameters: {best_trial.params}")

    clusters = spectral_clustering(BEST_N)[1]

    cluster_keywords, cluster_names_list, texts = extract_cluster_keywords(texts = texts_list, labels = clusters, top_n = 10)

    tsne = TSNE(n_components=2, perplexity=30, random_state=42)
    reduced_tsne = tsne.fit_transform(REDUCED_EMBEDDINGS)

    phrase_clusters = []
    sentiments_list: list[SentimentResponse] = []

    for i, text in enumerate(texts_list):
        sentiment = sentiments[i]
        phrase_clusters.append({
            "x": float(reduced_tsne[i][0]),
            "y": float(reduced_tsne[i][1]),
            "cluster": cluster_names_list[i],
            "phrase": text,
        })
        sentiments_list.append(SentimentResponse(text = text, sentiment = sentiment, topic = cluster_names_list[i]))


    create_dataset_from_sentiment_response_list(sentiments_list)
    print("Dataset created successfully")
    print()
    print("Clusters List:")
    print(phrase_clusters)
    print()
    print("Sentiment Response List:")
    print(sentiments_list)
    return phrase_clusters, sentiments_list
