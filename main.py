# backend/main.py

from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import asyncio # To simulate processing delay
import os
from dotenv import load_dotenv
load_dotenv()
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
PORT = os.getenv('PORT')

app = FastAPI()

# ==========================================
# 1. CORS Configuration (Crucial for React)
# ==========================================
# This allows requests from your React app running on localhost:3000
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
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="Invalid file type. Please upload a CSV.")

    print(f"Receiving file: {file.filename}")


    # 2. Simulate AI processing time (fake loading bar progress)
    # In real life, this is where we read the CSV and call OpenAI
    # from services.analysis_service import analysis
    # responce = analysis(file)

    print("Analysis complete. Sending mock results.")

    # 3. Return the mock data
    return MOCK_RESPONSE

@app.post("/test")
async def analyze_test():
    await asyncio.sleep(3)

    print("Analysis complete. Sending mock results.")

    # 3. Return the mock data
    return MOCK_RESPONSE

@app.get('/test')
async def get_test():
    return MOCK_RESPONSE
