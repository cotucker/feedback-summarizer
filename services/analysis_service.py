import pandas as pd
from sklearn.metrics import accuracy_score
from fastapi.datastructures import UploadFile
from services.clustering_service import cluster_texts
from services.file_handler_service import get_dataset_from_file, get_feedbacks_info
from services.llm_service import feedback_list_analysis, topics_analysis, generate_total_summary, process_columnes_names, get_separator
import logging
import asyncio

logging.basicConfig(level=logging.INFO, format='%(levelname)s:%(name)s:%(message)s')
logger = logging.getLogger(__name__)

async def analysis(file: UploadFile, topics: str = ''):
    df = await get_dataset_from_file(file, process_columnes_names, get_separator, topics)
    logger.info("Dataset loaded and preprocessed.")
    
    # Run file I/O in thread
    await asyncio.to_thread(df.to_csv, "data/dataset.csv", index=False)
    
    analysis: dict = {}
    logger.info("Starting feedback list analysis.")
    
    # Run heavy sync task in thread
    feedback_list_analysis_results = await asyncio.to_thread(feedback_list_analysis, topics)
    
    logger.info("Feedback list analysis completed. Starting text clustering.")
    
    # Run heavy sync task in thread
    phrase_clusters, feedback_analysis, clustering_info = await asyncio.to_thread(cluster_texts, feedback_list_analysis_results, topics)
    
    logger.info("Text clustering completed.")
    logger.info(f"Clustering Info: {clustering_info}")
    analysis["feedback_analysis"] = [
        {
            "text": sentiment_response.text,
            "topic": sentiment_response.topic,
            "sentiment": feedback_analysis[i].sentiment
        }

        for i, sentiment_response in enumerate(feedback_analysis)
    ]
    analysis["phrase_clusters"] = phrase_clusters
    logger.info("Starting topics analysis.")
    
    # Run heavy sync task in thread
    topics_analysis_results = await asyncio.to_thread(topics_analysis, feedback_analysis)
    
    logger.info("Topics analysis completed. Generating total summary.")
    analysis["topics"] = topics_analysis_results
    
    # Run heavy sync task in thread
    analysis["summary"] = await asyncio.to_thread(generate_total_summary, topics_analysis_results)
    
    logger.info("Total summary generated. Calculating sentiment counts.")
    counts = {"positive": 0, "negative": 0, "neutral": 0}

    for s in feedback_analysis:
        key = str(s.sentiment).lower()
        if key in counts:
            counts[key] += 1

    analysis["sentiment"] = counts
    return analysis
