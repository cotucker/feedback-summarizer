from fastapi import FastAPI, File, UploadFile, Query
from fastapi.middleware.cors import CORSMiddleware
import os
from dotenv import load_dotenv
from services.analysis_service import analysis


load_dotenv()
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')

app = FastAPI()

origins = [
    "http://localhost:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/api/feedback/analyze")
async def analyze_feedback(topics: str | None = Query(default=None), file: UploadFile = File(...)):

    analysis_results = await analysis(file, topics if topics else '')
    print("Analysis complete. Sending mock results.")

    return analysis_results
