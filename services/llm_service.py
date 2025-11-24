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
from services.file_handler_service import create_dataset_from_sentiment_response_list, get_feedback_list, get_feedback_analysis_by_topic
from services.text_chunking_service import feedback_chunking

load_dotenv()
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
CEREBRAS_API_KEY = os.getenv('CEREBRAS_API_KEY')
MODEL = os.getenv('MODEL')
client = genai.Client(api_key=GEMINI_API_KEY)
client_cerebras = Cerebras(api_key=CEREBRAS_API_KEY)

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

def test_topic_moddeling(cluster_name: str, text: str):
    response = client.models.generate_content(
        model='gemini-flash-lite-latest',
        contents=[
            types.Content(
                role="user",
                parts=[
                    types.Part(
                        text=f"""
                        You are an expert NLP Quality Assurance Analyst. Your task is to perform a strict evaluation to determine if a given `TEXT` is a strong and relevant example of a given `TOPIC_NAME`.
                        **OBJECTIVE:**
                        Based on the semantic relevance, evaluate the match between the `TEXT` and the `TOPIC_NAME`. Your analysis must be critical and follow the scoring rules below. Your response MUST be a single, valid JSON object.
                        **INPUT DATA:**
                        - **TOPIC_NAME:** "{cluster_name}"
                        - **TEXT:** "{text}"
                        **SCORING RULES:**
                        -   **Score 3 (Strong Match):** The `TEXT` is a perfect and direct example of the `TOPIC_NAME`. The main subject of the text *is* the topic.
                        -   **Score 2 (Weak Match):** The `TOPIC_NAME` is mentioned or related to the `TEXT`, but it is not the central theme. The text is more about something else, but has a connection.
                        -   **Score 1 (No Match):** The `TEXT` and the `TOPIC_NAME` are unrelated.
                        **ADDITIONAL RULES:**
                        1.  **Be Critical:** If the match is not obvious and direct, lean towards a lower score. Do not try to find loose connections.
                        2.  **Provide Justification:** You must provide a brief, one-sentence justification for your score, explaining your reasoning.
                        3.  **Strict Output Format:** Do not include any other text.
                        """

                    ),
                ],
            ),
        ],
        config={
            "response_mime_type": "application/json",
            "response_schema": TopicQuality,
        },
    )
    quality: TopicQuality = typing.cast(TopicQuality, response.parsed)
    return quality


def get_cluster_name(cluster_terms: str) -> str:
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

def generate_single_sentiments_feedback_analysis(feedback_text: str, topics: str) -> list[Subtext]:

    response = client.models.generate_content(
        model=f'{MODEL}',
        contents=[
            types.Content(
                role="user",
                parts=[
                    types.Part(
                        text=f"""
                        You are a meticulous Customer Feedback Analyst. Your primary task is to decompose a user's feedback text into the subtext, self-contained, meaningful chunks. For each chunk, you must identify its specific topic.
                        **INPUT DATA:**
                        - **FEEDBACK_TEXT:** "{feedback_text}"
                        - **EXISTING_TOPICS:** {topics}
                        **CRITICAL RULES FOR CHUNKING:**
                        1.  **Decomposition is Key:** Your main goal is to break down the text. A single sentence often contains multiple chunks. Coordinating conjunctions like "and", "but", "while" are strong indicators of a boundary between chunks.
                        2.  **Chunk = One Idea:** Each chunk must represent a single, distinct event, opinion, or observation.
                            Each chunk MUST HAVE a subject (what is descriped in the chunk) and everything related to that subject.
                            -   *Example of a single idea:* "We were overcharged for hours that were not worked."
                            -   *Example of INVALID chunk:* "and modern."
                            -   *Example of another single idea:* "getting it corrected has been a nightmare."
                        3.  **Chunks Must Be Verbatim:** Each chunk you extract MUST be a direct, word-for-word substring of the original `FEEDBACK_TEXT`. Do not rephrase or summarize.
                        4.  **Topic Assignment:**
                            -   Assign the most relevant topic from the `EXISTING_TOPICS` list.
                            -   If no existing topic fits perfectly, create a new, concise topic name (e.g., "Billing Issues", "Support Resolution Process").
                            -   If a chunk is a general statement without a specific subject (e.g., "I am very unhappy"), assign it to "General Feedback".
                        """,
                    ),
                ],
            ),
        ],
        config={
            "response_mime_type": "application/json",
            "response_schema": list[Subtext],
        },
    )
    sentiments: list[Subtext] = typing.cast(list[Subtext], response.parsed)
    return sentiments

def get_separator(row: str) -> str:
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

def topics_analysis(feedback_analysis: list[SentimentResponse]) -> list[dict]:
    topics: dict = {}

    for sentiment in feedback_analysis:
        if sentiment.topic not in topics:
            topics[sentiment.topic] = 1
        else:
            topics[sentiment.topic] += 1

    topic_descriptions = generate_topics_description([topic for topic in topics])

    return [
        {
            "topic": topic,
            "count": topics[topic],
            "summary": topic_descriptions[i].description + '\n' + generate_topic_summary(get_feedback_analysis_by_topic(topic), topic)
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
                        text=f"""
                            - topics summaries:
                            {topics_analysis}""",
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

def filter_topics(selected_topics: str, all_topics_list: str) -> list[str]:

    if len(selected_topics) == 0:
        return []

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



def feedback_list_analysis(topics_text: str = '') -> list[str]:

    if topics_text.replace(' ', '') == '':
        topics = []
    else:
        topics: list[str] = generate_topics_list(topics_text)
        if not topics:
            raise HTTPException(status_code=400, detail="Invalid topics")

    filter = not topics
    feedback_list: list[str] = get_feedback_list()
    texts_list: list[str] = feedback_chunking(feedback_list)
    return texts_list

def generate_topics_list(topics_text: str):
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


def generate_feedback_responce(feedback_info: str) -> FeedbackResponse:
    response = client.models.generate_content(
        model=f'{MODEL}',
        contents=[
            types.Content(
                role="user",
                parts=[
                    types.Part(
                        text="""
                        You are a highly skilled Customer Support Professional with a talent for crafting empathetic, concise, and effective replies.
                        Your primary goal is to make the customer feel heard and valued, aiming to de-escalate negative experiences and reinforce positive ones.
                        Analyze the provided customer feedback and its accompanying rating.
                        Generate the best possible reply that is tailored to the specific situation.
                        """,
                    ),
                    types.Part(
                        text=f"""
                        - feedback text and rating: {feedback_info}
                        """,
                    ),
                ],
            ),
        ],
        config={
            "response_mime_type": "application/json",
            "response_schema": FeedbackResponse,
        },
    )
    feedback_responce: FeedbackResponse = typing.cast(FeedbackResponse, response.parsed)
    return feedback_responce

def feedback_responces(feedbacks_info: list[str]) -> list[FeedbackResponse]:
    return [generate_feedback_responce(feedback_info) for feedback_info in feedbacks_info ]
