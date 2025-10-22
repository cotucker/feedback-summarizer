# backend/main.py

from fastapi import FastAPI, File, UploadFile, HTTPException, Body, Query
from fastapi.middleware.cors import CORSMiddleware
import asyncio # To simulate processing delay
import os
from typing import Annotated, Optional
from dotenv import load_dotenv
from services.analysis_service import analysis
from services.llm_service import feedback_list_analysis, filter_feedback_analysis
load_dotenv()
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
PORT = os.getenv('PORT')

app = FastAPI()

origins = [
    f"http://localhost:{PORT}",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==========================================
# 2. Mock Data (Matches frontend structure)
# ==========================================
# Since we don't have OpenAI connected yet, we return this fake data
# so the frontend can render the charts.
MOCK_RESPONSE = {
  "summary": "Users are generally happy with the new UI update, finding it more intuitive. However, there is a significant cluster of complaints regarding slow loading times on mobile devices. Pricing seems to be a neutral topic.",
  "sentiment": {
    "positive": 8,
    "negative": 4,
    "neutral": 0
  },
  "topics": [
    {
      "topic": "Platform Utility",
      "count": 5,
      "summary": "Users are generally happy with the new UI update, finding it more intuitive. However, there is a significant cluster of complaints regarding slow loading times on mobile devices. Pricing seems to be a neutral topic."
    },
    {
      "topic": "Pricing/Cost",
      "count": 2,
      "summary": "Users are experiencing slow loading times on mobile devices, which is causing frustration. This issue needs to be addressed to improve user satisfaction."
    },
    {
      "topic": "Customer Support",
      "count": 2,
      "summary": "Users are generally satisfied with the customer support provided, but some have reported issues with response times."
    },
    {
      "topic": "Project Delivery",
      "count": 1,
      "summary": "Users are generally satisfied with the pricing, but some have expressed concerns about the cost of certain features."
    },
    {
      "topic": "Technical Competency",
      "count": 1,
      "summary": "Users are generally satisfied with the pricing, but some have expressed concerns about the cost of certain features."
    },
    {
      "topic": "Project Management",
      "count": 1,
      "summary": "Users are generally satisfied with the project delivery, but some have expressed concerns about the timeline."
    }
  ],
  "quotes": [
    {
      "text": "The new dashboard looks amazing, so much easier to use!",
      "topic": "UI/UX Design",
      "sentiment": "positive"
    },
    {
      "text": "It takes forever to load on my iPhone since the update.",
      "topic": "Mobile Performance",
      "sentiment": "negative"
    },
    {
      "text": "Support replied fast, but didn't really solve my issue.",
      "topic": "Customer Support",
      "sentiment": "neutral"
    }
  ],
  "feedback_analysis": [
    {
      "text": "It takes forever to load on my iPhone since the update.",
      "topic": "Mobile Performance",
      "sentiment": "negative"
    },
    {
      "text": "Support replied fast, but didn't really solve my issue.",
      "topic": "Customer Support",
      "sentiment": "neutral"
    }
  ],
  "feedback_replies": [
    {
      "feedback_text": "Support replied fast, but didn't really solve my issue.",
      "feedback_reply": "Thank you for your feedback. We are working on improving our response times.",
      "score": 5
    },
    {
      "feedback_text": "It takes forever to load on my iPhone since the update.",
      "feedback_reply": "Thank you for your feedback. We are working on improving our response times.",
      "score": 4
    }
  ]
}


# ==========================================
# 3. The API Endpoint
# ==========================================
@app.post("/api/feedback/analyze")
async def analyze_feedback(topics: str | None = Query(default=None), file: UploadFile = File(...)):
    # 1. Validate file type
    if file.filename is None:
        raise HTTPException(status_code=400, detail="No filename provided for the uploaded file.")
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="Invalid file type. Please upload a CSV.")

    print(f"Receiving file: {file.filename}, Parameters: {topics}")

    # 2. Simulate AI processing time (fake loading bar progress)
    # In real life, this is where we read the CSV and call OpenAI
    # responce = analysis(file)
    await asyncio.sleep(2)
    print("Analysis complete. Sending mock results.")

    # 3. Return the mock data
    return MOCK_RESPONSE

@app.get('/test')
async def get_test(topics: str):
    return filter_feedback_analysis(topics)

@app.get('/api/sentiments')
async def get_sentiments(topics: str):
    return feedback_list_analysis(topics)
