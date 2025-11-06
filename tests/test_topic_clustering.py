from models.models import TopicQuality
from services.llm_service import test_topic_moddeling, feedback_list_analysis
from services.clustering_service import cluster_texts

feedback_list_analysis_results = feedback_list_analysis('')
phrase_clusters, feedback_analysis = cluster_texts(feedback_list_analysis_results)

count = 0

for feedback in feedback_analysis:
    quality = test_topic_moddeling(feedback.topic, feedback.text)
    if quality.is_match:
        count += 1


print(f"Quality: {count/len(feedback_list_analysis_results)}")
