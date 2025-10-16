import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification, pipeline

# Check if GPU is available and set the device
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
print(f"Device set to use {device}")

tokenizer = AutoTokenizer.from_pretrained("lxyuan/distilbert-base-multilingual-cased-sentiments-student")
model = AutoModelForSequenceClassification.from_pretrained("lxyuan/distilbert-base-multilingual-cased-sentiments-student").to(device)

nlp = pipeline("sentiment-analysis", model=model, tokenizer=tokenizer)

text = "Zoom's recording quality is inconsistent, especially when recording in the cloud."

sentiment = nlp(text)
print(sentiment)