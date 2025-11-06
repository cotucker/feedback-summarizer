from models.models import TopicQuality
from services.llm_service import test_topic_moddeling, feedback_list_analysis

feedback_list_analysis_results = feedback_list_analysis('')

count = 0

for feedback in feedback_list_analysis_results:
    quality = test_topic_moddeling(feedback.topic, feedback.text)
    if quality.is_match:
        count += 1


print(f"Quality: {count/len(feedback_list_analysis_results)}")
