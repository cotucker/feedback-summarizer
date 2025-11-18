import re
import spacy
from textblob import TextBlob
from typing import List, Dict
from textblob import TextBlob

nlp = spacy.load("en_core_web_sm")

def split_dot(text):
    separators = r'[.!?]\s+'

    segments = re.split(separators, text, flags=re.IGNORECASE)

    cleaned_segments = [s.strip() for s in segments if s and len(s.strip()) > 10]

    return cleaned_segments

def split_feedback_simple(text):
    separators = r'\b(and|but|however|though|while|although|yet|plus|also|meanwhile)\b|[.!?]\s+'
    segments = re.split(separators, text, flags=re.IGNORECASE)
    segments = [s.strip() for s in segments if s and len(s.strip()) > 10]
    return segments


try:
    nlp = spacy.load("en_core_web_sm")
except OSError:
    print("Downloading spaCy model 'en_core_web_sm'...")
    from spacy.cli import download
    download("en_core_web_sm")
    nlp = spacy.load("en_core_web_sm")


def get_sentiment(text: str) -> str:
    """Определяет тональность текста с помощью TextBlob."""
    polarity = TextBlob(text).sentiment.polarity
    if polarity > 0.1:
        return "Positive"
    elif polarity < -0.1:
        return "Negative"
    else:
        return "Neutral"

def find_clause_for_subject(subject, all_subjects):
    """
    Находит и "выращивает" текстовую клаузу для данного субъекта,
    аккуратно определяя ее границы.
    """
    head_verb = subject.head
    start_index = min([t.i for t in subject.subtree])
    end_index = max([t.i for t in head_verb.subtree])
    next_subjects = [s for s in all_subjects if s.i > subject.i and s.i <= end_index]

    if next_subjects:
        first_next_subject = next_subjects[0]
        next_subj_start_index = min([t.i for t in first_next_subject.subtree])
        end_index = next_subj_start_index - 1

    clause_span = subject.doc[start_index : end_index + 1]

    if clause_span and clause_span[-1].dep_ == "cc":
        return clause_span[:-1].text.strip()

    return clause_span.text.strip()

def extract_semantic_chunks(text: str) -> list:
    """
    Основная функция. Разделяет текст на осмысленные подтексты (чанки),
    анализируя синтаксическую структуру предложения.

    Для каждого чанка определяет аспект и тональность.
    """
    doc = nlp(text)
    results = []
    subjects = [token for token in doc if token.dep_ == "nsubj"]

    if not subjects:
        return [text]

    for subject in subjects:
        clause_text = find_clause_for_subject(subject, subjects)

        if not clause_text:
            continue

        results.append(clause_text)

    return results

def test_chunks(text: str) -> list[str]:
    list = []
    for item in split_dot(text):
        list.extend(extract_semantic_chunks(item))
    return list

def feedback_chunking(feedback_list: list[str]):
    list = []
    for feedback in feedback_list:
        list.extend(test_chunks(feedback))
    return list

if __name__ == "__main__":
    test_chunks("The product is bad but the company is good. Support is excellent.")
