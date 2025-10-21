from google import genai
from google.genai import types
from google.genai.types import GenerationConfig
import os, enum, json
from dotenv import load_dotenv
import pandas as pd
import typing
from pydantic import BaseModel
from services.file_handler_service import create_dataset_from_sentiment_response_list, get_feedback_list, get_topics_list, get_feedback_analysis

class Sentiment(enum.Enum):
    POSITIVE = "Positive"
    NEGATIVE = "Negative"
    NEUTRAL = "Neutral"

class Topic(BaseModel):
    topic: str
    count: int

class Quote(BaseModel):
    text: str
    topic: str
    sentiment: Sentiment

class Analysis(BaseModel):
    summary: str
    topics: list[Topic]
    quotes: list[Quote]

class FeedbackResponse(BaseModel):
    response: str
    sentiment: Sentiment

class SentimentResponse(BaseModel):
    text: str
    topic: str
    sentiment: Sentiment

load_dotenv()
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
MODEL = os.getenv('MODEL')
client = genai.Client(api_key=GEMINI_API_KEY)

def generate_analysis(text_list: list):
    response = client.models.generate_content(
        model=f'{MODEL}',
        contents=[
            types.Content(
                role="user",
                parts=[
                    types.Part(
                        text="Analyze the following feedbacks and provide a summary, topics, and quotes:",
                    ),
                ],
            ),
            types.Content(
                role="user",
                parts=[
                    types.Part(
                        text=f"{text_list}",
                    ),
                ],
            ),
        ],
        config={
            "response_mime_type": "application/json",
            "response_schema": Analysis,
        },
    )

    # Fix for diagnostic error: Ensure response.parsed is a valid Analysis object.
    # The type checker sees response.parsed as BaseModel | dict[Any, Any] | Enum | None.
    # We need to explicitly check its type before assigning to Analysis.
    if not isinstance(response.parsed, Analysis):
        # If parsing fails or the model returns an unexpected type/None,
        # raise an error or handle appropriately. Returning the parsed object
        # is the intent, so a failure to parse into the schema should be an error.
        raise ValueError(f"Failed to parse model response into Analysis object. Received type: {type(response.parsed).__name__}. Raw text: {response.text}")

    my_analysis: Analysis = response.parsed
    # The function should return the parsed Analysis object, not the raw text.
    return response.text


def generate_single_sentiments_feedback_responce(feedback_text: str, topics: str) -> list[SentimentResponse]:

    response = client.models.generate_content(
        model=f'{MODEL}',
        contents=[
            types.Content(
                role="user",
                parts=[
                    types.Part(
                        text="""You are an expert Customer Feedback Analyst
                        whose task is to decompose complex user reviews into individual
                        , atomic entities, assessing the sentiment and topic for each.
                        If topic of entitie is not included in the topics list - create new topic""",
                    ),
                ],
            ),
            types.Content(
                role="user",
                parts=[
                    types.Part(
                        text=f"Feedback text: {feedback_text}",
                    ),
                ],
            ),
            types.Content(
                role="user",
                parts=[
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


def feedback_list_analysis(topics_text: str):
    topics: list[str] = generate_topics_list(topics_text)
    filter = not topics
    sentiments_list: list[SentimentResponse] = []
    feedback_list: list[str] = get_feedback_list()
    for feedback in feedback_list:
        sentiments = generate_single_sentiments_feedback_responce(feedback, ', '.join(topics))
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
        # sentiments_list.extend(sentiments)
    create_dataset_from_sentiment_response_list(sentiments_list)

    print(sentiments_list)
    return sentiments_list

def filter_feedback_analysis(selected_topics: str):

    all_topics = get_topics_list()
    print(all_topics)
    selected_topics: list[str] = generate_topics_list(selected_topics)
    print(selected_topics)
    filtered_topics =  filter_topics(all_topics, selected_topics)
    print(filtered_topics)
    feedback_analysis = get_feedback_analysis(filtered_topics)
    return feedback_analysis



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
                ],
            ),
            types.Content(
                role="user",
                parts=[
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
                ],
            ),
            types.Content(
                role="user",
                parts=[
                    types.Part(
                        text=f"All topics : {all_topics}",
                    ),
                ],
            ),
            types.Content(
                role="user",
                parts=[
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


def generate_sentiments_feedback_responce(text_list: list) -> tuple[list[str], list[str]]:

    response = client.models.generate_content(
        model=f'{MODEL}',
        contents=[
            types.Content(
                role="user",
                parts=[
                    types.Part(
                        text=f"Write a context-aware reply to a every feedback in the list ({len(text_list)} total), taking its topic and sentiment into account. The reply should be short and engaging to appease the customer as much as possible",
                    ),
                ],
            ),
            types.Content(
                role="user",
                parts=[
                    types.Part(
                        text=f"{text_list}",
                    ),
                ],
            ),
        ],
        config={
            "response_mime_type": "application/json",
            "response_schema": list[FeedbackResponse],
        },
    )

    if not isinstance(response.parsed, list) or not all(isinstance(item, FeedbackResponse) for item in response.parsed):
        raise ValueError(f"Failed to parse model response into list[FeedbackResponse] object. Received type: {type(response.parsed).__name__}. Raw text: {response.text}")

    my_feedback_responses: list[FeedbackResponse] = typing.cast(list[FeedbackResponse], response.parsed)
    response_list = [feedback_response.response for feedback_response in my_feedback_responses]
    sentiment_list = [feedback_response.sentiment.value for feedback_response in my_feedback_responses]

    assert len(response_list) == len(text_list)
    assert len(sentiment_list) == len(text_list)
    return response_list, sentiment_list

def test_generate_feedback_responce():

    text_list = [
        "I really like the new features you added to the product. They are very helpful and easy to use.",
        "The customer service team was very responsive and helpful. They resolved my issue quickly and efficiently.",
        "I had a bad experience with the product. The customer service team was unhelpful and rude. I will not buy this product again.",
    ]

    response = client.models.generate_content(
        model=f'{MODEL}',
        contents=[
            types.Content(
                role="user",
                parts=[
                    types.Part(
                        text=f"Write a context-aware reply to a every feedback in the list ({len(text_list)} total), taking its topic and sentiment into account. The reply should be short and engaging to appease the customer as much as possible",
                    ),
                ],
            ),
            types.Content(
                role="user",
                parts=[
                    types.Part(
                        text=f"{text_list}",
                    ),
                ],
            ),
        ],
        config={
            "response_mime_type": "application/json",
            "response_schema": list[FeedbackResponse],
        },
    )
    print(response.text)
    my_feedback_responses: list[FeedbackResponse] = typing.cast(list[FeedbackResponse], response.parsed)
    print(my_feedback_responses)
    assert len(my_feedback_responses) == len(text_list)

if __name__ == "__main__":
    pass
