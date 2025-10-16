from google import genai
from google.genai import types
from google.genai.types import GenerationConfig
import os
from dotenv import load_dotenv
import pandas as pd
from pydantic import BaseModel

class Topic(BaseModel):
    topic: str
    count: int

class Quote(BaseModel):
    text: str
    topic: str
    sentiment: str

class Analysis(BaseModel):
    summary: str
    topics: list[Topic]
    quotes: list[Quote]

class FeedbackResponse(BaseModel):
    response: str
    

load_dotenv()
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
client = genai.Client(api_key=GEMINI_API_KEY)

def generate_feedback_responce(text_list: list) -> list:
    response_list = []

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

    my_feedback_responses: list[FeedbackResponse] = response.parsed
    response_list = [feedback_response.response for feedback_response in my_feedback_responses]

    assert len(my_feedback_responses) == len(text_list)
    return response_list

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

    my_feedback_responses: list[FeedbackResponse] = response.parsed
    print(my_feedback_responses)

    assert len(my_feedback_responses) == len(text_list)

test_generate_feedback_responce()
