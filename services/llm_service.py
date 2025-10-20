from google import genai
from google.genai import types
from google.genai.types import GenerationConfig
import os, enum
from dotenv import load_dotenv
import pandas as pd
import typing
from pydantic import BaseModel

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


load_dotenv()
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
client = genai.Client(api_key=GEMINI_API_KEY)

def generate_analysis(text_list: list):
    client = genai.Client()
    response = client.models.generate_content(
        model="gemini-2.5-flash",
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

def generate_sentiments_feedback_responce(text_list: list) -> tuple[list[str], list[str]]:
    client = genai.Client()
    response = client.models.generate_content(
        model="gemini-2.5-flash",
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

    # Fix for diagnostic error: Ensure response.parsed is a valid list[FeedbackResponse] object.
    # The type checker sees response.parsed as BaseModel | dict[Any, Any] | Enum | None.
    # We need to explicitly check its type before assigning to list[FeedbackResponse].
    if not isinstance(response.parsed, list) or not all(isinstance(item, FeedbackResponse) for item in response.parsed):
        raise ValueError(f"Failed to parse model response into list[FeedbackResponse] object. Received type: {type(response.parsed).__name__}. Raw text: {response.text}")

    # Use typing.cast to explicitly inform the type checker that response.parsed is now a list[FeedbackResponse]
    # after the runtime check, resolving the diagnostic error.
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

    client = genai.Client()
    response = client.models.generate_content(
        model="gemini-flash-latest",
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
        # Use the response as a JSON string.
    print(response.text)

    my_feedback_responses: list[FeedbackResponse] = typing.cast(list[FeedbackResponse], response.parsed)
    print(my_feedback_responses)

    assert len(my_feedback_responses) == len(text_list)
