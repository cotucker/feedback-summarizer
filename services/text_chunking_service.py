import re
import spacy
from textblob import TextBlob

nlp = spacy.load("en_core_web_sm")


def split_dot(text):
    separators = r"[.!?]\s+"
    segments = re.split(separators, text, flags=re.IGNORECASE)
    cleaned_segments = [s.strip() for s in segments if s and len(s.strip()) > 10]
    return cleaned_segments


def split_feedback_simple(text):
    separators = (
        r"\b(and|but|however|though|while|although|yet|plus|also|meanwhile)\b|[.!?]\s+"
    )
    segments = re.split(separators, text, flags=re.IGNORECASE)
    segments = [s.strip() for s in segments if s and len(s.strip()) > 10]
    return segments


try:
    nlp = spacy.load("en_core_web_sm")
except OSError:
    from spacy.cli import download
    download("en_core_web_sm")
    nlp = spacy.load("en_core_web_sm")


def get_sentiment(text: str) -> str:
    polarity = TextBlob(text).sentiment.polarity
    if polarity > 0.1:
        return "Positive"
    elif polarity < -0.1:
        return "Negative"
    else:
        return "Neutral"


def find_clause_for_subject(subject, all_subjects):
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


def split_sentences_by_conjunctions(text):
    doc = nlp(text)
    sentences = []
    start = 0

    for token in doc:

        if token.pos_ == "CCONJ" or (token.pos_ == "PUNCT" and token.text == ","):
            head = token.head
            is_clause_separator = False

            if token.pos_ == "CCONJ":

                for child in head.children:
                    if child.dep_ == "conj" and (
                        child.pos_ == "VERB" or child.pos_ == "AUX"
                    ):
                        is_clause_separator = True
                        break

            if is_clause_separator:
                part = doc.text[start : token.idx].strip(" ,")

                if part:
                    sentences.append(part)
                start = token.idx + len(token.text)

    last_part = doc.text[start:].strip(" ,")
    if last_part:
        sentences.append(last_part)

    return sentences


def test_chunks(text: str) -> list[str]:
    list = []

    for item in split_dot(text):
        list.extend(split_sentences_by_conjunctions(item))

    return list


def feedback_chunking(feedback_list: list[str]):
    list = []
    number_list = []
    for feedback in feedback_list:
        text_chunks = test_chunks(feedback)
        list.extend(text_chunks)
        number_list.append(len(text_chunks))

    return list, number_list


if __name__ == "__main__":
    print(
        test_chunks("The product is bad but the company is good. Support is excellent.")
    )
