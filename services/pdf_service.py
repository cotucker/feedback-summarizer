from fpdf import FPDF
from datetime import datetime

class PDFReport(FPDF):
    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.set_text_color(128)
        self.cell(0, 10, f'Page {self.page_no()}', 0, 0, 'C')

    def clean_text(self, text):
        if not isinstance(text, str):
            return str(text)
        return text.encode('latin-1', 'replace').decode('latin-1')

def generate_pdf_from_data(data: dict) -> bytes:
    pdf = PDFReport()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16)
    pdf.set_text_color(0, 0, 0)
    title = "Feedback Analysis Report"
    pdf.cell(0, 10, txt=title, ln=True, align='C')
    pdf.set_draw_color(0, 0, 255)
    pdf.set_line_width(0.5)
    title_w = pdf.get_string_width(title)
    x_start = (pdf.w - title_w) / 2
    y_pos = pdf.get_y()
    pdf.line(x_start - 2, y_pos, x_start + title_w + 2, y_pos)
    pdf.ln(5)
    pdf.set_font("Arial", size=10)
    pdf.set_text_color(100, 100, 100)
    timestamp = datetime.now().strftime("%d-%m-%Y %H:%M:%S")
    filename = pdf.clean_text(data.get('filename', 'Unknown File'))
    pdf.cell(0, 5, txt=f"Generated on: {timestamp}", ln=True, align='R')
    pdf.cell(0, 5, txt=f"Analyzed File: {filename}", ln=True, align='R')
    pdf.ln(10)
    pdf.set_text_color(50, 50, 50)
    pdf.set_font("Arial", 'B', 14)
    pdf.cell(0, 10, txt="Overall Summary", ln=True)
    pdf.set_font("Arial", size=12)
    summary_text = pdf.clean_text(data.get('summary', 'No summary available.'))
    pdf.set_fill_color(240, 240, 240)
    pdf.multi_cell(0, 8, txt=summary_text, fill=True)
    pdf.ln(5)
    pdf.set_font("Arial", 'B', 14)
    pdf.cell(0, 10, txt="Sentiment Analysis", ln=True)
    sentiments = data.get('sentiment', {})
    pdf.set_font("Arial", size=12)
    colors = {
        'positive': (76, 175, 80),   # Green
        'negative': (244, 67, 54),   # Red
        'neutral': (255, 152, 0),    # Orange
        'mixed': (255, 152, 0)       # Orange
    }
    max_val = 0

    for v in sentiments.values():
        if isinstance(v, (int, float)):
            if v > max_val: max_val = v

    if max_val == 0: max_val = 1

    for sentiment, value in sentiments.items():
        s_key = sentiment.lower()
        r, g, b = colors.get(s_key, (150, 150, 150))
        label = f"{sentiment.capitalize()}: {value}"
        pdf.cell(50, 10, txt=label)
        bar_len = 0

        if isinstance(value, (int, float)):
            bar_len = (value / max_val) * 100

        x = pdf.get_x()
        y = pdf.get_y()
        pdf.set_fill_color(r, g, b)
        pdf.rect(x, y + 2, bar_len, 6, 'F')
        pdf.ln(10)

    pdf.ln(5)
    pdf.set_font("Arial", 'B', 14)
    pdf.cell(0, 10, txt="Topics", ln=True)
    topics = data.get('topics', [])

    for topic in topics:
        pdf.set_font("Arial", 'B', 12)
        t_topic = pdf.clean_text(topic.get('topic', 'N/A'))
        t_count = topic.get('count', 0)
        y_start = pdf.get_y()
        pdf.cell(0, 10, txt=f"Count: {t_count}", align='R', ln=0)
        pdf.set_x(pdf.l_margin)
        pdf.cell(0, 10, txt=f"Topic: {t_topic}", align='L', ln=1)
        pdf.set_draw_color(200, 200, 200)
        pdf.line(pdf.l_margin, pdf.get_y(), pdf.w - pdf.r_margin, pdf.get_y())
        pdf.ln(2)
        pdf.set_font("Arial", size=12)
        t_summary = pdf.clean_text(topic.get('summary', 'N/A'))
        pdf.multi_cell(0, 8, txt=t_summary)
        pdf.ln(5)

    return pdf.output(dest='S')
