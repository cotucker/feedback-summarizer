from typing import Dict, Any, Union
from pydantic import BaseModel
import pandas as pd
import math
from fastapi.datastructures import UploadFile
from models.models import SentimentResponse
from services.clustering_service import cluster_texts
from services.file_handler_service import get_dataset_from_file
from services.llm_service import (
    feedback_list_analysis,
    topics_analysis,
    get_total_summary,
    get_processed_columns,
    get_separator,
)
import logging
import asyncio

logging.basicConfig(level=logging.INFO, format="%(levelname)s:%(name)s:%(message)s")
logger = logging.getLogger(__name__)


async def analysis(file: UploadFile, topics: str = ""):
    original_texts, rating_series = await get_dataset_from_file(file, get_processed_columns, get_separator, topics)
    logger.info("Dataset loaded and preprocessed.")
    analysis: dict = {}
    analysis["filename"] = file.filename
    logger.info("Starting feedback list analysis.")
    feedback_list_analysis_results, number_list = await asyncio.to_thread(
        feedback_list_analysis, topics
    )
    logger.info("Feedback list analysis completed. Starting text clustering.")
    phrase_clusters, feedback_analysis, clustering_info = await asyncio.to_thread(
        cluster_texts, feedback_list_analysis_results, topics
    )
    logger.info("Text clustering completed.")
    analysis["all_feedbacks"] = format_original_feedback_analysis(original_texts, rating_series, feedback_analysis, number_list)
    logger.info(f"Clustering Info: {clustering_info}")
    analysis["feedback_analysis"] = [
        {
            "text": sentiment_response.text,
            "topic": sentiment_response.topic,
            "sentiment": feedback_analysis[i].sentiment,
        }
        for i, sentiment_response in enumerate(feedback_analysis)
    ]
    analysis["phrase_clusters"] = phrase_clusters
    logger.info("Starting topics analysis.")
    topics_analysis_results = await asyncio.to_thread(
        topics_analysis, feedback_analysis
    )
    logger.info("Topics analysis completed. Generating total summary.")
    analysis["topics"] = topics_analysis_results
    analysis["summary"] = await asyncio.to_thread(
        get_total_summary, topics_analysis_results
    )
    logger.info("Total summary generated. Calculating sentiment counts.")
    counts = {"positive": 0, "negative": 0, "neutral": 0}

    for s in feedback_analysis:
        key = str(s.sentiment).lower()

        if key in counts:
            counts[key] += 1

    analysis["sentiment"] = counts
    logger.info("Analysis completed.")
    return analysis

def format_original_feedback_analysis(
    original_texts: list[str],
    rating_series: Union[list[int], pd.Series, None],
    feedback_analysis: list[SentimentResponse],
    number_list: list[int]
) -> list[dict[str, Any]]:

    result = []
    current_analysis_idx = 0

    if rating_series is not None and len(rating_series) > 0:
        ratings = list(rating_series)
        has_ratings = True
    else:
        ratings = []
        has_ratings = False

    for i, original_text in enumerate(original_texts):
        count = number_list[i]
        sub_analyses = feedback_analysis[current_analysis_idx : current_analysis_idx + count]
        current_analysis_idx += count
        unique_topics = set(item.topic for item in sub_analyses if item.topic)
        topics_str = ", ".join(sorted(unique_topics))
        current_rating = None

        if has_ratings and i < len(ratings):
            val = ratings[i]
            try:
                if val is not None and not (isinstance(val, float) and (math.isnan(val) or math.isinf(val))):
                    current_rating = val
            except:
                current_rating = None

        entry = {
            "feedback": original_text,
            "topics": topics_str,
            "rating": current_rating
        }
        result.append(entry)

    return result
