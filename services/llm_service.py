from google import genai
from google.genai import types
import os
import enum
from dotenv import load_dotenv
import typing
from models.models import FeedbackResponse, SentimentResponse, TopicSummary, TotalSummary, Separator
from pydantic import BaseModel
from fastapi import HTTPException
from services.file_handler_service import create_dataset_from_sentiment_response_list, get_feedback_list, get_feedback_analysis_by_topic

load_dotenv()
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
MODEL = os.getenv('MODEL')
client = genai.Client(api_key=GEMINI_API_KEY)

def generate_single_sentiments_feedback_analysis(feedback_text: str, topics: str) -> list[SentimentResponse]:

    response = client.models.generate_content(
        model=f'{MODEL}',
        contents=[
            types.Content(
                role="user",
                parts=[
                    types.Part(
                        text="""You are an expert Customer Feedback Analyst
                        whose task is to decompose complex user reviews by topics into individual
                        , atomic entities , assessing the sentiment and topic for each.
                        If topic of entitie is not included in the topics list - create new topic
                        If atomic entitie doesnt provide any information assign it to "General Feedback"
                        """,
                    ),
                    types.Part(
                        text=f"Feedback text: {feedback_text}",
                    ),
                    types.Part(
                        text=f"Topics: {topics}",
                    ),
                ],
            ),
        ],
        config={
            "response_mime_type": "application/json",
            "response_schema": list[SentimentResponse],
        },
    )
    print(response.text)
    sentiments: list[SentimentResponse] = typing.cast(list[SentimentResponse], response.parsed)
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
    print(separator)
    return separator.separator

def topics_analysis(feedback_analysis: list[SentimentResponse]) -> list[dict]:
    topics: dict = {}
    for sentiment in feedback_analysis:
        if sentiment.topic not in topics:
            topics[sentiment.topic] = 1
        else:
            topics[sentiment.topic] += 1

    for topic in topics:
        print(f"{topic}: {topics[topic]}")

    return [
        {
            "topic": topic,
            "count": topics[topic],
            "summary": generate_topic_summary(get_feedback_analysis_by_topic(topic), topic)
        }
        for topic in topics
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
    print(f"Generating summary for topic: {topic_name}, texts: {topic_texts}")
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
                        Your task is to generate a concise, neutral, and informative summary that captures the main points from the feedback list.
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

def feedback_list_analysis(topics_text: str = '') -> list[SentimentResponse]:
    if topics_text.replace(' ', '') == '':
        topics = []
    else:
        topics: list[str] = generate_topics_list(topics_text)
        if not topics:
            raise HTTPException(status_code=400, detail="Invalid topics")

    print(f"Generaled topics: {topics}")
    filter = not topics
    sentiments_list: list[SentimentResponse] = []
    feedback_list: list[str] = get_feedback_list()
    for feedback in feedback_list:
        sentiments = generate_single_sentiments_feedback_analysis(feedback, ', '.join(topics))
        for sentiment in sentiments:
            if filter:
                if sentiment.topic not in topics:
                    topics.append(sentiment.topic)
                    sentiments_list.append(sentiment)
                else:
                    sentiments_list.append(sentiment)
            else:
                if sentiment.topic in topics:
                    sentiments_list.append(sentiment)
    create_dataset_from_sentiment_response_list(sentiments_list)

    print(sentiments_list)
    return sentiments_list

def generate_topics_list(topics_text: str):
    response = client.models.generate_content(
        model=f'{MODEL}',
        contents=[
            types.Content(
                role="user",
                parts=[
                    types.Part(
                        text="Create Topics list of customers feedback from query, keep original topics names, if there is no information about topics in query return empty list",
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

def filter_topics(all_topics: list[str], selected_topics: list[str]) -> list[str]:
    response = client.models.generate_content(
        model=f'{MODEL}',
        contents=[
            types.Content(
                role="user",
                parts=[
                    types.Part(
                        text="Filter all existing topics by what topics customer wants to see",
                    ),
                    types.Part(
                        text=f"All topics : {all_topics}",
                    ),
                    types.Part(
                        text=f"Selected topics : {selected_topics}",
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

if __name__ == "__main__":
    pass
