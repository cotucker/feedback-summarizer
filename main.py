from fastapi import FastAPI, File, UploadFile, Query, Body
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
import os
from dotenv import load_dotenv
from services.analysis_service import analysis
from services.pdf_service import generate_pdf_from_data
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

# def generate_pdf_from_data(data: dict) -> bytes:
#     pdf = FPDF()
#     pdf.add_page()
#     pdf.set_font("Arial", size=12)

#     # Add a title
#     pdf.set_font("Arial", 'B', 16)
#     pdf.cell(200, 10, txt="Feedback Analysis Report", ln=True, align='C')
#     pdf.ln(10)

#     # Overall Summary
#     pdf.set_font("Arial", 'B', 14)
#     pdf.cell(200, 10, txt="Overall Summary", ln=True)
#     pdf.set_font("Arial", size=12)
#     # FPDF doesn't handle UTF-8 characters automatically, so we encode the string
#     summary_text = data.get('summary', 'No summary available.').encode('latin-1', 'replace').decode('latin-1')
#     pdf.multi_cell(0, 10, txt=summary_text)
#     pdf.ln(5)

#     # Sentiment Analysis
#     pdf.set_font("Arial", 'B', 14)
#     pdf.cell(200, 10, txt="Sentiment Analysis", ln=True)
#     pdf.set_font("Arial", size=12)
#     sentiments = data.get('sentiment', {})
#     for sentiment, value in sentiments.items():
#         pdf.cell(200, 10, txt=f"{sentiment.capitalize()}: {value}", ln=True)
#     pdf.ln(5)

#     # Topics
#     pdf.set_font("Arial", 'B', 14)
#     pdf.cell(200, 10, txt="Topics", ln=True)
#     pdf.set_font("Arial", size=12)
#     topics = data.get('topics', [])
#     for topic in topics:
#         pdf.set_x(pdf.l_margin) # Ensure cursor is at the left margin for each new topic
#         topic_text = f"Topic: {topic.get('topic', 'N/A')} (Count: {topic.get('count', 0)})".encode('latin-1', 'replace').decode('latin-1')
#         pdf.cell(0, 10, txt=topic_text, ln=True) # Use 0 for width to extend to right margin
#         summary_text = f"  Summary: {topic.get('summary', 'N/A')}".encode('latin-1', 'replace').decode('latin-1')
#         pdf.multi_cell(0, 10, txt=summary_text)
#     pdf.ln(5)

#     # Detailed Feedback Analysis
#     pdf.set_font("Arial", 'B', 14)
#     pdf.cell(200, 10, txt="Detailed Feedback Analysis", ln=True)
#     pdf.set_font("Arial", 'B', 10)
#     pdf.cell(80, 10, 'Text', 1)
#     pdf.cell(40, 10, 'Topic', 1)
#     pdf.cell(40, 10, 'Sentiment', 1)
#     pdf.ln()
#     pdf.set_font("Arial", size=10)
#     feedback_analysis = data.get('feedback_analysis', [])
#     for item in feedback_analysis:
#         text = item.get('text', 'N/A')[:50] + '...' if len(item.get('text', 'N/A')) > 50 else item.get('text', 'N/A')
#         text = text.encode('latin-1', 'replace').decode('latin-1')
#         topic = item.get('topic', 'N/A').encode('latin-1', 'replace').decode('latin-1')
#         sentiment = item.get('sentiment', 'N/A').encode('latin-1', 'replace').decode('latin-1')
#         pdf.cell(80, 10, text, 1)
#         pdf.cell(40, 10, topic, 1)
#         pdf.cell(40, 10, sentiment, 1)
#         pdf.ln()

#     return pdf.output(dest='S')

@app.post("/api/feedback/analyze")
async def analyze_feedback(topics: str | None = Query(default=None), file: UploadFile = File(...)):

    analysis_results = await analysis(file, topics if topics else '')
    return analysis_results

@app.post("/api/feedback/report")
async def generate_report(data: dict = Body(...)):
    pdf_bytes = generate_pdf_from_data(data)
    return StreamingResponse(
        io.BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={"Content-Disposition": "attachment; filename=feedback_report.pdf"}
    )
