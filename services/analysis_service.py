from fastapi.datastructures import UploadFile
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
    await get_dataset_from_file(file, get_processed_columns, get_separator, topics)
    logger.info("Dataset loaded and preprocessed.")
    analysis: dict = {}
    analysis["filename"] = file.filename
    logger.info("Starting feedback list analysis.")
    feedback_list_analysis_results = await asyncio.to_thread(
        feedback_list_analysis, topics
    )
    logger.info("Feedback list analysis completed. Starting text clustering.")
    phrase_clusters, feedback_analysis, clustering_info = await asyncio.to_thread(
        cluster_texts, feedback_list_analysis_results, topics
    )

    logger.info("Text clustering completed.")
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
