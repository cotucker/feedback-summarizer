import numpy as np
from sklearn.decomposition import PCA
from models.models import SentimentResponse
from services.llm_service import get_embedding

def cluster_texts(sentiment_responses: list[SentimentResponse]) -> list[dict]:
    if not sentiment_responses:
        return []

    texts_list = [response.text for response in sentiment_responses]
    topics = [response.topic for response in sentiment_responses]

    embeddings = np.array(get_embedding(texts_list))

    if len(sentiment_responses) < 2:
        return [{
            "x": 0,
            "y": 0,
            "cluster": sentiment_responses[0].topic,
            "phrase": sentiment_responses[0].text
        }]

    pca = PCA(n_components=2)
    reduced_data = pca.fit_transform(embeddings)

    unique_topics = sorted(list(set(topics)))
    topic_map = {topic: i for i, topic in enumerate(unique_topics)}

    y_coords = reduced_data[:, 1]
    y_range = np.max(y_coords) - np.min(y_coords)
    spread_factor = y_range * 2.0 if y_range > 0 else 1.0

    phrase_clusters: list[dict] = []
    for i, response in enumerate(sentiment_responses):
        x = reduced_data[i, 0]
        y = reduced_data[i, 1]
        topic_offset = topic_map[response.topic] * spread_factor

        phrase_clusters.append({
            "x": x,
            "y": y + topic_offset,
            "cluster": response.topic,
            "phrase": response.text
        })

    return phrase_clusters
