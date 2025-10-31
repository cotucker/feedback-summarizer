from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
import nltk
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
from nltk.tokenize.treebank import TreebankWordDetokenizer
import pandas as pd


df = pd.read_csv('test.csv')
texts_list = df['Phrase'].tolist()

# --- Одноразовая настройка NLTK ---
try:
    nltk.data.find('tokenizers/punkt')
except nltk.downloader.DownloadError:
    nltk.download('punkt')
try:
    stopwords.words('english')
except LookupError:
    nltk.download('stopwords')
# ------------------------------------

# --- Создаем ресурсы один раз ---
analyzer = SentimentIntensityAnalyzer()
stop_words = set(stopwords.words('english'))
detokenizer = TreebankWordDetokenizer()

# --- НОВЫЙ ЭЛЕМЕНТ: Список слов-усилителей/интенсификаторов ---
# VADER часто считает их нейтральными, поэтому нужен отдельный список.
INTENSIFIER_WORDS = {
    "absolutely", "completely", "extremely", "highly", "incredibly",
    "really", "so", "totally", "truly", "very", "quite"
}

def filter_text_final_version(text: str) -> str:
    """
    Удаляет из текста стоп-слова, слова-усилители и слова с эмоциональной окраской.
    """
    # 1. Получаем доступ к словарю тональности VADER
    sentiment_lexicon = analyzer.lexicon

    # 2. Разбиваем текст на слова
    tokens = word_tokenize(text)

    filtered_words = []
    for word in tokens:
        word_lower = word.lower()

        # --- Проверки в новом порядке ---

        # Шаг 1: Пропускаем, если это просто знак препинания или не-буквенный токен
        if not word.isalpha():
            continue

        # Шаг 2: Пропускаем, если это стоп-слово
        if word_lower in stop_words:
            continue

        # Шаг 3: Пропускаем, если это слово-усилитель
        if word_lower in INTENSIFIER_WORDS:
            continue

        # Шаг 4: Пропускаем, если слово имеет сильную эмоциональную окраску
        # Порог 1.0 - это хороший старт для отсечения слов вроде 'good', 'bad', 'great'
        score = sentiment_lexicon.get(word_lower, 0)
        if abs(score) >= 1.8:
            continue

        # Если слово прошло все проверки, добавляем его
        filtered_words.append(word)

    # Собираем отфильтрованные слова обратно в строку
    return detokenizer.detokenize(filtered_words)


# --- Тестирование ---

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
