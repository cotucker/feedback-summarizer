import numpy as np
from models.models import SentimentResponse
from services.llm_service import get_embedding
from scipy.spatial.distance import cosine

def cluster_texts(sentiment_responses: list[SentimentResponse]) -> list[dict]:
    if not sentiment_responses:
        return []

    texts_list = [response.text for response in sentiment_responses]
    topics_list = [response.topic for response in sentiment_responses]

    unique_topics = sorted(list(set(response.topic for response in sentiment_responses)))
    n_topics = len(unique_topics)

    if n_topics == 0:
        return []

    combined_list_for_embedding = unique_topics + texts_list
    all_embeddings = np.array(get_embedding(combined_list_for_embedding))

    topic_embeddings = all_embeddings[:n_topics]
    text_embeddings = all_embeddings[n_topics:]

    topic_embedding_map = {topic: emb for topic, emb in zip(unique_topics, topic_embeddings)}

    radius = 1.0
    topic_positions = {}
    for i, topic in enumerate(unique_topics):
        angle = 2 * np.pi * i / n_topics
        topic_x = radius * np.cos(angle)
        topic_y = radius * np.sin(angle)
        topic_positions[topic] = (topic_x, topic_y)

    phrase_clusters = []
    for i, text_emb in enumerate(text_embeddings):
        distances = {
            topic: cosine(text_emb, topic_emb)
            for topic, topic_emb in topic_embedding_map.items()
            if np.any(topic_emb)
        }
        if not distances:
            continue

        closest_topic = min(distances, key=distances.get)
        semantic_distance = distances[closest_topic]

        center_x, center_y = topic_positions[closest_topic]

        visual_radius_scale = 0.7
        offset_radius = semantic_distance * visual_radius_scale
        offset_angle = np.random.uniform(0, 2 * np.pi)

        point_x = center_x + offset_radius * np.cos(offset_angle)
        point_y = center_y + offset_radius * np.sin(offset_angle)

        phrase_clusters.append({
            "x": point_x,
            "y": point_y,
            "cluster": closest_topic,
            "phrase": texts_list[i] + " " + topics_list[i]
        })

    return phrase_clusters
