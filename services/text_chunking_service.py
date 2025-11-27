import re
import spacy
from textblob import TextBlob

try:
    nlp = spacy.load("en_core_web_sm")
except OSError:
    from spacy.cli import download
    download("en_core_web_sm")
    nlp = spacy.load("en_core_web_sm")


def clean_chunk(text: str) -> str:
    text = text.strip()
    text = text.strip(".,;:!?")
    text = re.sub(r'\s+', ' ', text)
    return text.strip()


def is_valid_chunk(text: str) -> bool:
    if not text:
        return False

    if len(text) < 3:
        return False

    stop_chunks = {"the", "a", "an", "and", "but", "or", "so", "however", "although"}
    if text.lower() in stop_chunks:
        return False

    return True


def improved_sentence_split(text):
    doc = nlp(text)
    splits = []
    split_indices = [0]
    split_adverbs = {"however", "therefore", "meanwhile", "nevertheless", "furthermore", "moreover"}

    for token in doc:
        if token.pos_ == "CCONJ" or token.text in [",", ";"]:
            next_verb = None
            for child in token.head.children:
                if child.i > token.i and child.dep_ == "conj" and child.pos_ in ("VERB", "AUX"):
                    next_verb = child
                    break

            if next_verb:
                has_subj = any(t.dep_ in ("nsubj", "nsubjpass") for t in next_verb.children)
                if has_subj:
                    split_indices.append(token.idx)

        elif token.text.lower() in split_adverbs:
            split_indices.append(token.idx)

        elif token.dep_ in ("nsubj", "nsubjpass"):
            verb = token.head

            if verb.i > 0:
                prev_word = doc[token.left_edge.i - 1] if token.left_edge.i > 0 else None

                if prev_word and prev_word.pos_ not in ("CCONJ", "PUNCT") and prev_word.text.lower() not in split_adverbs:
                    if prev_word.head != verb and prev_word.head != token:
                        split_indices.append(token.left_edge.idx)

    split_indices.append(len(text))
    split_indices = sorted(list(set(split_indices)))

    for i in range(len(split_indices) - 1):
        start = split_indices[i]
        end = split_indices[i+1]
        chunk = text[start:end]

        cleaned = clean_chunk(chunk)
        if is_valid_chunk(cleaned):
            splits.append(cleaned)

    return splits


def test_chunks(text: str) -> list[str]:
    separators = r"[.!?]\s+"
    raw_segments = re.split(separators, text)

    final_list = []
    for seg in raw_segments:
        if not seg.strip():
            continue
        processed = improved_sentence_split(seg)
        final_list.extend(processed)

    return final_list


def feedback_chunking(feedback_list: list[str]):
    list = []
    number_list = []

    for feedback in feedback_list:
        text_chunks = test_chunks(feedback)
        list.extend(text_chunks)
        number_list.append(len(text_chunks))

    return list, number_list




if __name__ == "__main__":
    print("--- Test 1: However ---")
    print(test_chunks("The app is fast, however the pricing is too high."))

    print("\n--- Test 2: Run-on sentence ---")
    print(test_chunks("The product is bad the company is good. Support is excellent."))

    print("\n--- Test 3: Standard 'but' ---")
    print(test_chunks("I like the design but the speed is slow."))

    print("\n--- Test 4: Comma splice ---")
    print(test_chunks("The UI is great, it looks very modern."))
