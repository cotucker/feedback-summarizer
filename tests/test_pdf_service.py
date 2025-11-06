import unittest
from services.pdf_service import generate_pdf_from_data

class TestPdfService(unittest.TestCase):

    def test_generate_pdf_from_data(self):
        mock_data = {
            "summary": "This is a test summary.",
            "sentiment": {"positive": 10, "negative": 5, "neutral": 2},
            "topics": [
                {
                    "topic": "Pricing",
                    "count": 5,
                    "summary": "Summary of feedback related to pricing."
                },
                {
                    "topic": "Features",
                    "count": 12,
                    "summary": "Users want more features."
                }
            ],
            "feedback_analysis": [
                {
                    "text": "The app is too expensive.",
                    "topic": "Pricing",
                    "sentiment": "negative"
                }
            ]
        }

        pdf_bytes = generate_pdf_from_data(mock_data)

        # Check if the output is bytearray
        self.assertIsInstance(pdf_bytes, bytearray)

        # Check if it's a non-empty PDF file (basic check for PDF header)
        self.assertTrue(pdf_bytes.startswith(b'%PDF-'))

if __name__ == '__main__':
    unittest.main()
