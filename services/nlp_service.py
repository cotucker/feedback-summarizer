from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
import nltk
nltk.download('punkt_tab')
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
from nltk.tokenize.treebank import TreebankWordDetokenizer
from transformers import AutoTokenizer, AutoModelForSequenceClassification, pipeline
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

if __name__ == "__main__":

    df = pd.read_csv('data/data.csv')
    texts_list = df['Phrase'].tolist()

    for text in texts_list:
        neutral = filter_text_final_version(text)
    print(f"{text} -> {neutral}")

    print("--- Пример 1: Позитивный отзыв ---")
    original1 = "the customer care is a huge problem"
    neutral1 = filter_text_final_version(original1)
    print(f"Оригинал: {original1}")
    print(f"Отфильтрованный: {neutral1}\n")

    print("--- Пример 2: Негативный отзыв ---")
    original2 = "The performance is terrible, it's so slow and frustrating."
    neutral2 = filter_text_final_version(original2)
    print(f"Оригинал: {original2}")
    print(f"Отфильтрованный: {neutral2}\n")

    print("--- Пример 3: Смешанный отзыв ---")
    original3 = "The design is great but the battery is awful."
    neutral3 = filter_text_final_version(original3)
    print(f"Оригинал: {original3}")
    print(f"Отфильтрованный: {neutral3}\n")

    print("--- Пример 4: Более сложный случай ---")
    original4 = "I am extremely disappointed with the customer support, they were rude and completely useless."
    neutral4 = filter_text_final_version(original4)
    print(f"Оригинал: {original4}")
    print(f"Отфильтрованный: {neutral4}\n")



    text = """XYZ Corporation's stock soared by 20% after reporting
    record-breaking annual profits and announcing a significant dividend
    increase for shareholders.
    """

    sentiment = get_sentiment(text)
    print(sentiment)
