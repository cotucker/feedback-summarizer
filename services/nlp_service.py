from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
import nltk
nltk.download('punkt_tab')
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
from nltk.tokenize.treebank import TreebankWordDetokenizer
from transformers import AutoTokenizer, AutoModelForSequenceClassification
import torch
from models.models import Sentiment

import pandas as pd

try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt')
try:
    stopwords.words('english')
except LookupError:
    nltk.download('stopwords')

analyzer = SentimentIntensityAnalyzer()
stop_words = set(stopwords.words('english'))
detokenizer = TreebankWordDetokenizer()

model_name = "tabularisai/multilingual-sentiment-analysis"
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForSequenceClassification.from_pretrained(model_name)

INTENSIFIER_WORDS = {
    "absolutely", "completely", "extremely", "highly", "incredibly",
    "really", "so", "totally", "truly", "very", "quite"
}

def filter_text_final_version(text: str) -> str:
    sentiment_lexicon = analyzer.lexicon
    tokens = word_tokenize(text)

    filtered_words = []
    for word in tokens:
        word_lower = word.lower()

        if not word.isalpha():
            continue

        if word_lower in stop_words:
            continue

        if word_lower in INTENSIFIER_WORDS:
            continue

        score = sentiment_lexicon.get(word_lower, 0)
        if abs(score) >= 1.8:
            continue

        filtered_words.append(word)

    return detokenizer.detokenize(filtered_words)

def predict_sentiment(texts):
    inputs = tokenizer(texts, return_tensors="pt", truncation=True, padding=True, max_length=512)
    with torch.no_grad():
        outputs = model(**inputs)
    probabilities = torch.nn.functional.softmax(outputs.logits, dim=-1)
    sentiment_map = {0: "Very Negative", 1: "Negative", 2: "Neutral", 3: "Positive", 4: "Very Positive"}
    return [sentiment_map[p] for p in torch.argmax(probabilities, dim=-1).tolist()]

if __name__ == "__main__":
    texts = [
        # English
        "We went over a budget.", "The customer service was disappointing.", "The weather is fine, nothing special.",
        "I like final product."
    ]

    for text, sentiment in zip(texts, predict_sentiment(texts)):
        print(f"Text: {text}\nSentiment: {sentiment}\n")
