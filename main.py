# backend/main.py

from fastapi import FastAPI, File, UploadFile, HTTPException, Body
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
        "positive": 65,
        "negative": 25,
        "neutral": 10
    },
    "topics": [
        {"topic": "UI/UX Design", "count": 150},
        {"topic": "Mobile Performance", "count": 80},
        {"topic": "Customer Support", "count": 45},
        {"topic": "Pricing", "count": 30}
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
    ]
}

# ==========================================
# 3. The API Endpoint
# ==========================================
@app.post("/api/feedback/analyze")
async def analyze_feedback(file: UploadFile = File(...)):
    # 1. Validate file type
    if file.filename is None:
        raise HTTPException(status_code=400, detail="No filename provided for the uploaded file.")
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="Invalid file type. Please upload a CSV.")

    print(f"Receiving file: {file.filename}")


    # 2. Simulate AI processing time (fake loading bar progress)
    # In real life, this is where we read the CSV and call OpenAI
    responce = analysis(file)

    print("Analysis complete. Sending mock results.")

    # 3. Return the mock data
    return responce

@app.get('/test')
async def get_test(topics: str):
    return filter_feedback_analysis(topics)

@app.get('/api/sentiments')
async def get_sentiments(topics: str):
    return feedback_list_analysis(topics)
