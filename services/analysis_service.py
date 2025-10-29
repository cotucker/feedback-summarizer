import pandas as pd
from sklearn.metrics import accuracy_score
from fastapi.datastructures import UploadFile
from services.clustering_service import cluster_texts
from services.file_handler_service import get_dataset_from_file, get_feedbacks_info
from services.llm_service import feedback_list_analysis, topics_analysis, generate_total_summary, feedback_responces, process_columnes_names, get_separator

async def analysis(file: UploadFile, topics: str = ''):
    df = await get_dataset_from_file(file, process_columnes_names, get_separator, topics)
    print(df.info())
    print(df.head())
    df.to_csv("data/dataset.csv", index=False)

    analysis: dict = {}

    feedback_list_analysis_results = feedback_list_analysis(topics)
    analysis["feedback_analysis"] = [
        {
            "text": sentiment_response.text,
            "topic": sentiment_response.topic,
            "sentiment": sentiment_response.sentiment.value
        }

        for sentiment_response in feedback_list_analysis_results
    ]


    topics_analysis_results = topics_analysis(feedback_list_analysis_results)
    analysis["topics"] = topics_analysis_results
    analysis["phrase_clusters"] = cluster_texts(feedback_list_analysis_results)

    analysis["summary"] = generate_total_summary(topics_analysis_results)

    counts = {"positive": 0, "negative": 0, "neutral": 0}
    for s in feedback_list_analysis_results:
        key = str(s.sentiment.value).lower()
        if key in counts:
            counts[key] += 1

    analysis["sentiment"] = counts

    analysis["feedback_replies"] = [
        {
            "feedback_text": feedback_response.original_feedback_text,
            "feedback_reply": feedback_response.response,
            "score": feedback_response.score
        }
        for feedback_response in feedback_responces(get_feedbacks_info())
    ]


    return analysis
