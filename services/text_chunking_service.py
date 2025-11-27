import re
import spacy

try:
    nlp = spacy.load("en_core_web_sm")
except OSError:
    from spacy.cli import download
    download("en_core_web_sm")
    nlp = spacy.load("en_core_web_sm")

def clean_chunk(text: str) -> str:
    text = text.strip()
    text = text.strip(".,;:!?-")
    start_stopwords = {
        "and", "but", "or", "so", "plus", "yet", "nor",
        "however", "therefore", "thus", "hence", "meanwhile",
        "consequently", "furthermore", "moreover", "nonetheless",
        "nevertheless", "otherwise", "instead", "besides", "also",
        "whereas", "although", "though", "while", "since", "because"
    }
    parts = text.split(' ', 1)
    if parts:
        first_word = parts[0].lower().strip(".,")
        if first_word in start_stopwords:
            text = parts[1] if len(parts) > 1 else ""
            return clean_chunk(text)
    return text.strip()

def is_valid_chunk(text: str) -> bool:
    if not text:
        return False
    if len(text) < 3:
        return False
    words = text.split()
    if len(words) == 1:
        word = words[0].lower().strip(".,!?:")
        single_word_blacklist = {
            "the", "a", "an", "it", "is", "was", "are", "were",
            "and", "but", "or", "so", "if", "for", "to", "of", "in", "on", "at",
            "however", "although", "though", "because", "since",
            "therefore", "consequently", "furthermore", "meanwhile",
            "this", "that", "there", "here", "just", "very", "too", "while"
        }
        if word in single_word_blacklist:
            return False
    return True

def improved_sentence_split(text):
    doc = nlp(text)
    split_indices = [0]
    hard_splitters = {
        "however", "nevertheless", "nonetheless", "conversely",
        "otherwise", "instead", "therefore", "thus", "hence",
        "accordingly", "consequently", "meanwhile", "furthermore",
        "moreover", "besides", "whereas", "although", "though", "yet"
    }
    for token in doc:
        if token.text.lower() in hard_splitters:
            split_indices.append(token.idx)
            continue
        if token.text.lower() == "but":
            split_indices.append(token.idx)
            continue
        if token.text.lower() == "and":
            right_span = doc[token.i+1:]
            has_subj = any(t.dep_ in ("nsubj", "nsubjpass", "expl") for t in right_span)
            has_verb = any(t.pos_ in ("VERB", "AUX") for t in right_span)
            prev_token = doc[token.i - 1] if token.i > 0 else None
            if prev_token and prev_token.pos_ in ("NOUN", "PROPN", "ADJ") and \
               len(right_span) > 0 and right_span[0].pos_ in ("NOUN", "PROPN", "ADJ") and not has_verb:
                continue
            if has_subj and has_verb:
                split_indices.append(token.idx)
            continue
        if token.text in [",", ";"]:
            right_span = doc[token.i+1:]
            left_span = doc[split_indices[-1]:token.i] if split_indices else doc[:token.i]
            has_verb_right = any(t.pos_ in ("VERB", "AUX") for t in right_span)
            has_verb_left = any(t.pos_ in ("VERB", "AUX") for t in left_span)
            has_subj_right = any(t.dep_ in ("nsubj", "nsubjpass", "expl") for t in right_span)
            if has_subj_right and has_verb_right:
                split_indices.append(token.idx + 1)
            elif not has_verb_left and not has_verb_right:
                if len(doc[token.i+1:].text) > 10:
                    split_indices.append(token.idx + 1)
        if token.dep_ in ("nsubj", "nsubjpass", "expl"):
            if token.i > 0:
                prev = doc[token.i - 1]
                if prev.pos_ in ("VERB", "AUX", "NOUN", "ADJ", "ADV") and \
                   prev.dep_ not in ("amod", "det", "compound", "poss") and \
                   prev.head != token and token.head != prev:
                    split_indices.append(token.left_edge.idx)
    split_indices.append(len(text))
    split_indices = sorted(list(set(split_indices)))
    final_splits = []
    for i in range(len(split_indices) - 1):
        chunk = text[split_indices[i]:split_indices[i+1]]
        cleaned = clean_chunk(chunk)
        if is_valid_chunk(cleaned):
            final_splits.append(cleaned)
    return final_splits

def test_chunks(text: str) -> list[str]:
    separators = r"[.!?]\s+"
    raw_segments = re.split(separators, text)
    results = []

    for seg in raw_segments:

        if not seg.strip():
            continue
        results.extend(improved_sentence_split(seg))

    return results

def feedback_chunking(feedback_list: list[str]):
    lst = []
    number_list = []

    for feedback in feedback_list:
        text_chunks = test_chunks(feedback)
        lst.extend(text_chunks)
        number_list.append(len(text_chunks))

    return lst, number_list
