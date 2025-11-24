from google import genai
from google.genai import types
from cerebras.cloud.sdk import Cerebras
import os
import enum
from dotenv import load_dotenv
import typing
import json
import numpy as np
from models.models import *
from pydantic import BaseModel
from fastapi import HTTPException
import spacy
from textblob import TextBlob
from services.file_handler_service import get_feedback_list, get_feedback_analysis_by_topic
from services.text_chunking_service import feedback_chunking

load_dotenv()
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
CEREBRAS_API_KEY = os.getenv('CEREBRAS_API_KEY')
MODEL = os.getenv('MODEL')
client = genai.Client(api_key=GEMINI_API_KEY)
client_cerebras = Cerebras(api_key=CEREBRAS_API_KEY)


def generate_topics_description_cerebras(cluster_names: list[str]) -> list[ClusterDescription]:
    response = client_cerebras.chat.completions.create(
        model="gpt-oss-120b",
        messages=[
            {"role": "system", "content": """
                You are a Senior Business Analyst responsible for interpreting clustered customer feedback for an executive audience.
                **OBJECTIVE:**
                Analyze the provided list of `CLUSTER_NAMES`. For each name, generate a concise, business-oriented description that explains what this category represents and, most importantly, how it differs from the other categories in the list. Your goal is to clarify the unique focus of each cluster.
                **CRITICAL RULES FOR DESCRIPTIONS:**
                1.  **Define the Core Theme:** For each cluster, start by explaining the primary topic it covers. What kind of feedback falls into this category?
                2.  **Highlight the Distinction:** This is the most important rule. Explicitly state what makes this cluster different from others. Focus on the nuances. For example, if you have both "Performance & Speed" and "Product Quality", explain that one is about *efficiency and responsiveness*, while the other is about *reliability, bugs, and craftsmanship*.
                3.  **Use Business Language:** Write in a clear, strategic tone. Avoid technical jargon. The descriptions should be immediately understandable to a product manager or executive.
                4.  **Be Concise:** Each description should be 2-3 sentences long.
                5.  **Strict Output Format:** Your response MUST be a object where keys are the original cluster names and values are their corresponding descriptions. Do not include any other text or explanations.
                """},
            {"role": "user", "content": f"""
                INPUT DATA:
                - **CLUSTER_NAMES:** {cluster_names}
                """},
        ],
        response_format={
            "type": "json_schema",
            "json_schema": {
                "name": "cluster_description_schema",
                "strict": True,
                "schema": CLUSTER_DESCRIPTION_SCHEMA
            }
        }
    )

    response_json = json.loads(response.choices[0].message.content)
    raw_list = response_json.get("clusters", [])
    cluster_descriptions = [ClusterDescription(**item) for item in raw_list]
    return cluster_descriptions

def generate_topics_description(cluster_names: list[str]) -> list[ClusterDescription]:
    response = client.models.generate_content(
        model=f'{MODEL}',
        contents=[
            types.Content(
                role="user",
                parts=[
                    types.Part(
                        text=f"""
                        You are a Senior Business Analyst responsible for interpreting clustered customer feedback for an executive audience.
                        **OBJECTIVE:**
                        Analyze the provided list of `CLUSTER_NAMES`. For each name, generate a concise, business-oriented description that explains what this category represents and, most importantly, how it differs from the other categories in the list. Your goal is to clarify the unique focus of each cluster.
                        **INPUT DATA:**
                        - **CLUSTER_NAMES:** {cluster_names}
                        **CRITICAL RULES FOR DESCRIPTIONS:**
                        1.  **Define the Core Theme:** For each cluster, start by explaining the primary topic it covers. What kind of feedback falls into this category?
                        2.  **Highlight the Distinction:** This is the most important rule. Explicitly state what makes this cluster different from others. Focus on the nuances. For example, if you have both "Performance & Speed" and "Product Quality", explain that one is about *efficiency and responsiveness*, while the other is about *reliability, bugs, and craftsmanship*.
                        3.  **Use Business Language:** Write in a clear, strategic tone. Avoid technical jargon. The descriptions should be immediately understandable to a product manager or executive.
                        4.  **Be Concise:** Each description should be 2-3 sentences long.
                        5.  **Strict Output Format:** Your response MUST be a object where keys are the original cluster names and values are their corresponding descriptions. Do not include any other text or explanations.
                        """,
                    ),
                ],
            ),
        ],
        config={
            "response_mime_type": "application/json",
            "response_schema": list[ClusterDescription],
        },
    )
    cluster_descriptions: list[ClusterDescription] = typing.cast(list[ClusterDescription], response.parsed)
    return cluster_descriptions

def get_topic_description(cluster_names: list[str]) -> list[ClusterDescription]:
    try:
        return generate_topics_description(cluster_names)
    except Exception as e:
        return generate_topics_description_cerebras(cluster_names)

def generate_cluster_name(cluster_terms: str) -> str:
    response = client.models.generate_content(
        model='gemini-2.5-flash-lite',
        contents=[
            types.Content(
                role="user",
                parts=[
                    types.Part(
                        text=f"""
                                You are an expert Data Analyst and Taxonomist. Your task is to analyze a list of keywords with clustery specificity score representing a cluster of customer feedback and generate a single, concise, and descriptive name for that cluster.
                                OBJECTIVE:
                                Based on the provided list of `CLUSTER_KEYWORDS`, synthesize them into a clear, high-level topic name that accurately represents the central theme of the cluster.
                                **RULES FOR NAMING:**
                                1.  **Be Abstract and High-Level:** The name should be a general category, not just a repetition of the keywords. Think about the underlying concept that connects these words.
                                2.  **Use Business Language:** The name must be professional, clear, and easily understandable by a business audience (e.g., "Project Management", "Technical Competence", "Pricing and Value").
                                3.  **Be Concise:** The name should be short, ideally 2-4 words long.
                                4.  **Format:** Use Title Case (e.g., "Customer Support Experience").
                                5.  **Strict Output Format:** Your response MUST ONLY be the generated cluster name. Do not include any explanation, introductory text like "The cluster name is:", or any quotation marks.
                                6.  **DO MUST NOT  return empty string.** You must return something.
                                INPUT DATA:
                                - CLUSTER_KEYWORDS: "{cluster_terms}"
                            """

                    ),
                ],
            ),
        ],
        config={
            "response_mime_type": "application/json",
            "response_schema": ClusterName,
        },
    )
    cluster_name: ClusterName = typing.cast(ClusterName, response.parsed)
    return cluster_name.name

def generate_cluster_name_cerebras(cluster_terms: str) -> str:
    response = client_cerebras.chat.completions.create(
        model="gpt-oss-120b",
        messages=[
            {"role": "system", "content": """
                You are an expert Data Analyst and Taxonomist. Your task is to analyze a list of keywords with clustery specificity score representing a cluster of customer feedback and generate a single, concise, and descriptive name for that cluster.
                OBJECTIVE:
                Based on the provided list of `CLUSTER_KEYWORDS`, synthesize them into a clear, high-level topic name that accurately represents the central theme of the cluster.
                **RULES FOR NAMING:**
                1.  **Be Abstract and High-Level:** The name should be a general category, not just a repetition of the keywords. Think about the underlying concept that connects these words.
                2.  **Use Business Language:** The name must be professional, clear, and easily understandable by a business audience (e.g., "Project Management", "Technical Competence", "Pricing and Value").
                3.  **Be Concise:** The name should be short, ideally 2-4 words long.
                4.  **Format:** Use Title Case (e.g., "Customer Support Experience").
                5.  **Strict Output Format:** Your response MUST ONLY be the generated cluster name. Do not include any explanation, introductory text like "The cluster name is:", or any quotation marks.
                6.  **DO MUST NOT  return empty string.** You must return something.
                """},
            {"role": "user", "content": f"""
                INPUT DATA:
                - CLUSTER_KEYWORDS: "{cluster_terms}
                """},
        ],
        response_format={
            "type": "json_schema",
            "json_schema": {
                "name": "cluster_name_schema",
                "strict": True,
                "schema": CLUSTER_NAME_SCHEMA
            }
        }
    )

    response_json = json.loads(response.choices[0].message.content)
    return response_json['name']


def get_cluster_name(cluster_terms: str) -> str:
    try:
        return generate_cluster_name(cluster_terms)
    except Exception as e:
        return generate_cluster_name_cerebras(cluster_terms)

def generate_separator(row: str) -> str:
    response = client.models.generate_content(
        model=f'{MODEL}',
        contents=[
            types.Content(
                role="user",
                parts=[
                    types.Part(
                        text="""
                        You are an expert Data Parsing utility. Your task is to analyze the first line of a text file and determine the most likely column separator (delimiter) used.
                        Based on the provided first line of text, identify the single character used as a delimiter.
                        This line must contain at least two columns about customer feedback and feedback rating.
                        the most common delimiters in this order of precedence: comma (`,`), semicolon (`;`), tab (`\t`), pipe (`|`)
                        If no consistent delimiter from the list above is found (e.g.
                        , the line is a single-column header or a natural language sentence)
                        , the value for the "separator" MUST be string 'null'.
                        """,
                    ),
                    types.Part(
                        text=f"""
                        input:
                        - first line of text: {row}
                        """
                    )
                ],
            ),
        ],
        config={
            "response_mime_type": "application/json",
            "response_schema": Separator,
        },
    )
    separator: Separator = typing.cast(Separator, response.parsed)
    return separator.separator

def generate_separator_cerebras(row: str) -> str:
    response = client_cerebras.chat.completions.create(
        model="gpt-oss-120b",
        messages=[
            {"role": "system", "content": """
                You are an expert Data Parsing utility. Your task is to analyze the first line of a text file and determine the most likely column separator (delimiter) used.
                Based on the provided first line of text, identify the single character used as a delimiter.
                This line must contain at least two columns about customer feedback and feedback rating.
                the most common delimiters in this order of precedence: comma (`,`), semicolon (`;`), tab (`\t`), pipe (`|`)
                If no consistent delimiter from the list above is found (e.g.
                , the line is a single-column header or a natural language sentence)
                , the value for the "separator" MUST be string 'null'.
                """},
            {"role": "user", "content": f"""
                INPUT DATA:
                - first line of text: {row}
                """},
        ],
        response_format={
            "type": "json_schema",
            "json_schema": {
                "name": "separator_schema",
                "strict": True,
                "schema": SEPARATOR_SCHEMA
            }
        }
    )

    response_json = json.loads(response.choices[0].message.content)
    return response_json['separator']

def get_separator(row: str) -> str:
    try:
        return generate_separator(row)
    except Exception as e:
        return generate_separator_cerebras(row)

def topics_analysis(feedback_analysis: list[SentimentResponse]) -> list[dict]:
    topics: dict = {}

    for sentiment in feedback_analysis:
        if sentiment.topic not in topics:
            topics[sentiment.topic] = 1
        else:
            topics[sentiment.topic] += 1

    topic_descriptions = get_topic_description([topic for topic in topics])

    return [
        {
            "topic": topic,
            "count": topics[topic],
            "summary": topic_descriptions[i].description + '\n' + get_topic_summary(get_feedback_analysis_by_topic(topic), topic)
        }
        for i, topic in enumerate(topics)
    ]

def generate_total_summary(topics_analysis: list[dict]) -> str:
    response = client.models.generate_content(
        model=f'{MODEL}',
        contents=[
            types.Content(
                role="user",
                parts=[
                    types.Part(
                        text="""
                        You are a Senior Product Analyst responsible for creating a high-level executive summary for leadership.
                        Your goal is to synthesize a list of pre-analyzed topic summaries into a single, cohesive paragraph.
                        This total summary must provide a bird's-eye view of the most critical takeaways from all customer feedback,
                        highlighting both key strengths and major pain points.
                        """,
                    ),
                    types.Part(
                        text=f"- topics summaries: {topics_analysis}",
                    ),
                ],
            ),
        ],
        config={
            "response_mime_type": "application/json",
            "response_schema": TotalSummary,
        },
    )
    total_summary: TotalSummary = typing.cast(TotalSummary, response.parsed)
    return total_summary.summary

def generate_total_summary_cerebras(topics_analysis: list[dict]) -> str:
    response = client_cerebras.chat.completions.create(
        model="gpt-oss-120b",
        messages=[
            {"role": "system", "content": """
                You are a Senior Product Analyst responsible for creating a high-level executive summary for leadership.
                Your goal is to synthesize a list of pre-analyzed topic summaries into a single, cohesive paragraph.
                This total summary must provide a bird's-eye view of the most critical takeaways from all customer feedback,
                highlighting both key strengths and major pain points.
                """},
            {"role": "user", "content": f"""
                INPUT DATA:
                - topics summaries: {topics_analysis}
                """},
        ],
        response_format={
            "type": "json_schema",
            "json_schema": {
                "name": "total_summary_schema",
                "strict": True,
                "schema": TOTAL_SUMMARY_SCHEMA
            }
        }
    )

    response_json = json.loads(response.choices[0].message.content)
    return response_json['summary']

def get_total_summary(topics_analysis: list[dict]) -> str:
    try:
        return generate_total_summary(topics_analysis)
    except Exception as e:
        return generate_total_summary_cerebras(topics_analysis)


def generate_topic_summary(topic_texts: list[str], topic_name: str) -> str:
    response = client.models.generate_content(
        model=f'{MODEL}',
        contents=[
            types.Content(
                role="user",
                parts=[
                    types.Part(
                        text="""
                        You are an expert Data Analyst specializing in synthesizing qualitative user feedback into actionable business insights.
                        Analyze the provided list of user feedback comments, which all relate to the single topic of "{topic_name}".
                        Your task is to explain topic name in simple terms, generate a concise, neutral, and informative summary that captures the main points from the feedback list.
                        """,
                    ),
                    types.Part(
                        text=f"""
                        - topic name: "{topic_name}"
                        - feedback texts list: {topic_texts}
                        """,
                    ),
                ],
            ),
        ],
        config={
            "response_mime_type": "application/json",
            "response_schema": TopicSummary,
        },
    )
    summary: TopicSummary = typing.cast(TopicSummary, response.parsed)
    return summary.summary

def generate_topic_summary_cerebras(topic_texts: list[str], topic_name: str) -> str:
    response = client_cerebras.chat.completions.create(
        model="gpt-oss-120b",
        messages=[
            {"role": "system", "content": """
                You are an expert Data Analyst specializing in synthesizing qualitative user feedback into actionable business insights.
                Analyze the provided list of user feedback comments, which all relate to the single topic of "{topic_name}".
                Your task is to explain topic name in simple terms, generate a concise, neutral, and informative summary that captures the main points from the feedback list.
                """},
            {"role": "user", "content": f"""
                INPUT DATA:
                - topic name: "{topic_name}"
                - feedback texts list: {topic_texts}
                """},
        ],
        response_format={
            "type": "json_schema",
            "json_schema": {
                "name": "tpoic_summary_schema",
                "strict": True,
                "schema": TOPIC_SUMMARY_SCHEMA
            }
        }
    )

    response_json = json.loads(response.choices[0].message.content)
    return response_json['summary']

def get_topic_summary(topic_texts: list[str], topic_name: str) -> str:
    try:
        return generate_topic_summary(topic_texts, topic_name)
    except Exception as e:
        return generate_topic_summary_cerebras(topic_texts, topic_name)

def filter_topics(selected_topics: str, all_topics_list: str) -> list[str]:
    response = client.models.generate_content(
        model=f'{MODEL}',
        contents=[
            types.Content(
                role="user",
                parts=[
                    types.Part(
                        text=f"""
                        You are an intelligent Semantic Filter. Your task is to interpret a user's search query and select the most relevant topics from a provided list of available options.
                        **OBJECTIVE:**
                        Analyze the `USER_QUERY` and compare it against the `AVAILABLE_TOPICS`. Return a JSON array containing ONLY the topics from the list that are semantically related to the user's intent.
                        **INPUT DATA:**
                        - **USER_QUERY:** "{selected_topics}"
                        - **AVAILABLE_TOPICS:** {all_topics_list}
                        **FILTERING RULES:**
                        1.  **Semantic Matching:** Do not look for exact string matches only. Understand the intent.
                            -   *Example:* If query is "too expensive", select "Pricing & Cost".
                            -   *Example:* If query is "bugs and glitches", select "Product Quality" or "Technical Issues".
                            -   *Example:* If query is "slow app", select "Performance & Speed".
                        2.  **Strict Constraints:** The output topics MUST be exact strings from the `AVAILABLE_TOPICS` list. Do not invent new topics or modify existing ones.
                        3.  **"All" Intent:** If the `USER_QUERY` implies "all", "everything", or is empty/generic (e.g., "show me data"), return the entire list of `AVAILABLE_TOPICS`.
                        4.  **No Match:** If the query is completely unrelated to any available topic, return an empty array `[]`.
                        """,
                    )
                ],
            ),
        ],
        config={
            "response_mime_type": "application/json",
            "response_schema": list[str],
        },
    )
    filtered_topics: list[str] = typing.cast(list[str], response.parsed)
    return filtered_topics


def filter_topics_cerebras(selected_topics: str, all_topics_list: str) -> list[str]:
    response = client_cerebras.chat.completions.create(
        model="gpt-oss-120b",
        messages=[
            {"role": "system", "content": """
                You are an intelligent Semantic Filter. Your task is to interpret a user's search query and select the most relevant topics from a provided list of available options.
                **OBJECTIVE:**
                Analyze the `USER_QUERY` and compare it against the `AVAILABLE_TOPICS`. Return a JSON array containing ONLY the topics from the list that are semantically related to the user's intent.
                **FILTERING RULES:**
                1.  **Semantic Matching:** Do not look for exact string matches only. Understand the intent.
                    -   *Example:* If query is "too expensive", select "Pricing & Cost".
                    -   *Example:* If query is "bugs and glitches", select "Product Quality" or "Technical Issues".
                    -   *Example:* If query is "slow app", select "Performance & Speed".
                2.  **Strict Constraints:** The output topics MUST be exact strings from the `AVAILABLE_TOPICS` list. Do not invent new topics or modify existing ones.
                3.  **"All" Intent:** If the `USER_QUERY` implies "all", "everything", or is empty/generic (e.g., "show me data"), return the entire list of `AVAILABLE_TOPICS`.
                4.  **No Match:** If the query is completely unrelated to any available topic, return an empty array `[]`.
                """},
            {"role": "user", "content": f"""
                **INPUT DATA:**
                - **USER_QUERY:** "{selected_topics}"
                - **AVAILABLE_TOPICS:** {all_topics_list}
                """},
        ],
        response_format={
            "type": "json_schema",
            "json_schema": {
                "name": "list_str_schema",
                "strict": True,
                "schema": LIST_STR_SCHEMA
            }
        }
    )

    response_json = json.loads(response.choices[0].message.content)
    return response_json['items']

def get_filtered_topics(selected_topics: str, all_topics_list: str) -> list[str]:

    if len(selected_topics) == 0:
        return []

    try:
        return filter_topics(selected_topics, all_topics_list)
    except Exception as e:
        return filter_topics_cerebras(selected_topics, all_topics_list)

def feedback_list_analysis(topics_text: str = '') -> list[str]:

    if topics_text.replace(' ', '') == '':
        topics = []
    else:
        topics: list[str] = get_topics_list(topics_text)
        if not topics:
            raise HTTPException(status_code=400, detail="Invalid topics")

    filter = not topics
    feedback_list: list[str] = get_feedback_list()
    texts_list: list[str] = feedback_chunking(feedback_list)
    return texts_list

def generate_topics_list(topics_text: str) -> list[str]:
    response = client.models.generate_content(
        model="gemini-flash-lite-latest",
        contents=[
            types.Content(
                role="user",
                parts=[
                    types.Part(
                        text="""Create Topics list of customers feedback on IT Company from query
                        , keep original topics names
                        , if there is no information about topics in query OR quety is not related to IT return empty list""",
                    ),
                    types.Part(
                        text=f"Query: {topics_text}",
                    ),
                ],
            ),
        ],
        config={
            "response_mime_type": "application/json",
            "response_schema": list[str],
        },
    )
    topics_list: list[str] = typing.cast(list[str], response.parsed)
    return topics_list

def generate_topics_list_cerebras(topics_text: str) -> list[str]:
    response = client_cerebras.chat.completions.create(
        model="gpt-oss-120b",
        messages=[
            {"role": "system", "content": """
                Create Topics list of customers feedback on IT Company from query
                , keep original topics names
                , if there is no information about topics in query OR quety is not related to IT return empty list
                """},
            {"role": "user", "content": f"""
                **INPUT DATA:**
                - Query: {topics_text}
                """},
        ],
        response_format={
            "type": "json_schema",
            "json_schema": {
                "name": "list_str_schema",
                "strict": True,
                "schema": LIST_STR_SCHEMA
            }
        }
    )

    response_json = json.loads(response.choices[0].message.content)
    return response_json['items']

def get_topics_list(topics_text: str) -> list[str]:
    try:
        return generate_topics_list(topics_text)
    except Exception as e:
        return generate_topics_list_cerebras(topics_text)

def process_columnes_names(list_of_column_names: list[str]) -> list[str]:
    response = client.models.generate_content(
        model=f'{MODEL}',
        contents=[
            types.Content(
                role="user",
                parts=[
                    types.Part(
                        text=f"""
                        You are an expert Data Schema Analyst. Your task is to analyze a given list of column headers from a CSV file and identify which columns contain user feedback text and a numerical user score, respectively.
                        **OBJECTIVE:**
                        Based on the provided list of column names, identify the single best candidate for the "Feedback Text" column and the single best candidate for the "Numerical Score" column. Your response MUST be a single, valid JSON array containing exactly two elements in the specified order: `["<FEEDBACK_COLUMN_NAME>", "<SCORE_COLUMN_NAME>"]`.
                        **INPUT DATA:**
                        - **COLUMN_NAMES:** `{list_of_column_names}`
                        **RULES:**
                        1.  **Feedback Text Column:** This column should contain the main body of the user's review or comment. Common names include `review`, `text`, `comment`, `feedback`, `описание`, `отзыв`. It must be the primary text column, not an ID, title, or summary.
                        2.  **Numerical Score Column:** This column should contain a numerical rating provided by the user (e.g., 1-5, 1-10). Common names include `rating`, `score`, `stars`, `оценка`, `рейтинг`.
                        3.  **Case-Insensitive Analysis:** Analyze the column names in a case-insensitive manner, but you MUST return the original, exact names as they appeared in the input list.
                        4.  **Handling Missing Columns:** If you cannot find a suitable candidate for one of the columns, skip it.
                        ---
                        **EXAMPLES (for reference):**
                        **Input:** `["Review Text", "Date", "Rating", "User_ID"]`
                        **Expected Output:**
                        ```json
                        ["Review Text", "Rating"]
                        """,
                    ),
                ],
            ),
        ],
        config={
            "response_mime_type": "application/json",
            "response_schema": list[str],
        },
    )
    selected_columns: list[str] = typing.cast(list[str], response.parsed)
    return selected_columns

def process_columnes_names_cerebras(list_of_column_names: list[str]) -> list[str]:
    response = client_cerebras.chat.completions.create(
        model="gpt-oss-120b",
        messages=[
            {"role": "system", "content": """
                You are an expert Data Schema Analyst. Your task is to analyze a given list of column headers from a CSV file and identify which columns contain user feedback text and a numerical user score, respectively.
                **OBJECTIVE:**
                Based on the provided list of column names, identify the single best candidate for the "Feedback Text" column and the single best candidate for the "Numerical Score" column. Your response MUST be a single, valid JSON array containing exactly two elements in the specified order: `["<FEEDBACK_COLUMN_NAME>", "<SCORE_COLUMN_NAME>"]`.
                **RULES:**
                1.  **Feedback Text Column:** This column should contain the main body of the user's review or comment. Common names include `review`, `text`, `comment`, `feedback`, `описание`, `отзыв`. It must be the primary text column, not an ID, title, or summary.
                2.  **Numerical Score Column:** This column should contain a numerical rating provided by the user (e.g., 1-5, 1-10). Common names include `rating`, `score`, `stars`, `оценка`, `рейтинг`.
                3.  **Case-Insensitive Analysis:** Analyze the column names in a case-insensitive manner, but you MUST return the original, exact names as they appeared in the input list.
                4.  **Handling Missing Columns:** If you cannot find a suitable candidate for one of the columns, skip it.
                ---
                **EXAMPLES (for reference):**
                **Input:** `["Review Text", "Date", "Rating", "User_ID"]`
                **Expected Output:**
                ```json
                ["Review Text", "Rating"]
                ```
                """},
            {"role": "user", "content": f"""
                **INPUT DATA:**
                - **COLUMN_NAMES:** `{list_of_column_names}`
                """},
        ],
        response_format={
            "type": "json_schema",
            "json_schema": {
                "name": "list_str_schema",
                "strict": True,
                "schema": LIST_STR_SCHEMA
            }
        }
    )

    response_json = json.loads(response.choices[0].message.content)
    return response_json['items']

def get_processed_columns(list_of_column_names: list[str]) -> list[str]:
    try:
        return process_columnes_names(list_of_column_names)
    except Exception as e:
        return process_columnes_names_cerebras(list_of_column_names)

if __name__ == "__main__":
   a = process_columnes_names_cerebras(['Review Text', 'Date', 'Rating', 'User_ID'])
   print(a)
