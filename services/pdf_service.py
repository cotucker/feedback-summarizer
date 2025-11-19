from fpdf import FPDF

def generate_pdf_from_data(data: dict) -> bytes:
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)

    pdf.set_font("Arial", 'B', 16)
    pdf.cell(200, 10, txt="Feedback Analysis Report", ln=True, align='C')
    pdf.ln(10)

    pdf.set_font("Arial", 'B', 14)
    pdf.cell(200, 10, txt="Overall Summary", ln=True)
    pdf.set_font("Arial", size=12)
    summary_text = data.get('summary', 'No summary available.').encode('latin-1', 'replace').decode('latin-1')
    pdf.multi_cell(0, 10, txt=summary_text)
    pdf.ln(5)

    pdf.set_font("Arial", 'B', 14)
    pdf.cell(200, 10, txt="Sentiment Analysis", ln=True)
    pdf.set_font("Arial", size=12)
    sentiments = data.get('sentiment', {})
    for sentiment, value in sentiments.items():
        pdf.cell(200, 10, txt=f"{sentiment.capitalize()}: {value}", ln=True)
    pdf.ln(5)

    # Topics
    pdf.set_font("Arial", 'B', 14)
    pdf.cell(200, 10, txt="Topics", ln=True)
    pdf.set_font("Arial", size=12)
    topics = data.get('topics', [])
    for topic in topics:
        pdf.set_x(pdf.l_margin)
        topic_text = f"Topic: {topic.get('topic', 'N/A')} (Count: {topic.get('count', 0)})".encode('latin-1', 'replace').decode('latin-1')
        pdf.cell(0, 10, txt=topic_text, ln=True)
        summary_text = f"  Summary: {topic.get('summary', 'N/A')}".encode('latin-1', 'replace').decode('latin-1')
        pdf.multi_cell(0, 10, txt=summary_text)
    pdf.ln(5)

    return pdf.output(dest='S')
