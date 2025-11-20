from fastapi import FastAPI, File, UploadFile, Query, Body, HTTPException
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
import os
from dotenv import load_dotenv
from services.analysis_service import analysis
from services.pdf_service import generate_pdf_from_data
from google.genai.errors import ServerError
import json
from fpdf import FPDF
import io

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
    try:
        analysis_results = await analysis(file, topics if topics else '')
        return analysis_results
    except ServerError as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/feedback/report")
async def generate_report(data: dict = Body(...)):
    pdf_bytes = generate_pdf_from_data(data)
    return StreamingResponse(
        io.BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={"Content-Disposition": "attachment; filename=feedback_report.pdf"}
    )
