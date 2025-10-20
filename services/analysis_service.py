import pandas as pd
from sklearn.metrics import accuracy_score
from fastapi.datastructures import UploadFile
from services.file_handler_service import get_dataset_from_file_path, get_dataset_from_file
from services.llm_service import generate_sentiments_feedback_responce, generate_analysis
import json

# import torch
# from transformers import AutoTokenizer, AutoModelForSequenceClassification, pipeline

# device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
# print(f"Device set to use {device}")
# tokenizer = AutoTokenizer.from_pretrained(
#     "lxyuan/distilbert-base-multilingual-cased-sentiments-student"
# )
# model = AutoModelForSequenceClassification.from_pretrained(
#     "lxyuan/distilbert-base-multilingual-cased-sentiments-student"
# ).to(device)

# nlp = pipeline("sentiment-analysis", model=model, tokenizer=tokenizer)


def analysis(file: UploadFile) -> str:
    # df = get_dataset_from_file_path("data/data.csv")
    df = get_dataset_from_file(file)
    print(df.info())
    print(df.head())
    text_list = df["Text"].apply(process_text).values.tolist()
    feedback_list, sentiment_list = generate_sentiments_feedback_responce(text_list)
    df["Sentiment"] = sentiment_list
    df["Feedback Response"] = feedback_list
    df.to_csv("data/res.csv", index=False)

    analysis = generate_analysis(text_list)
    print(analysis)
    analysis = json.loads(analysis)
    counts = {"positive": 0, "negative": 0, "neutral": 0}
    for s in sentiment_list:
        key = str(s).lower()
        if key in counts:
            counts[key] += 1
    analysis["sentiment"] = counts
    return analysis


# def get_sentiment(text):
#     sentiment = nlp(text)
#     return sentiment[0]["label"]


def process_text(text) -> str:
    import re

    if not isinstance(text, str):
        text = str(text)
    return re.sub(r"\d+", "", text)


def process_dataset():
    df = pd.read_csv("data/sentiment-analysis.csv")
    print(df.info())
    print(df.head())

    df["Text, Sentiment, Source, Date/Time, User ID, Location, Confidence Score"] = (
        df["Text, Sentiment, Source, Date/Time, User ID, Location, Confidence Score"]
        .fillna('"",,,,,,')
        .astype(str)
    )
    data_list = df[
        "Text, Sentiment, Source, Date/Time, User ID, Location, Confidence Score"
    ].values.tolist()

    print(data_list[:5])

    segmented_data_list = [data.split(",") for data in data_list]

    print(segmented_data_list[0])

    data_dict = {
        "Text": [segmented_data[0][1:-1] for segmented_data in segmented_data_list],
        "Sentiments": [segmented_data[1] for segmented_data in segmented_data_list],
        "Source": [segmented_data[2] for segmented_data in segmented_data_list],
        "Data/Time": [segmented_data[3] for segmented_data in segmented_data_list],
        "User ID": [segmented_data[4] for segmented_data in segmented_data_list],
        "Location": [segmented_data[5] for segmented_data in segmented_data_list],
        "Confidence Score": [
            segmented_data[6] for segmented_data in segmented_data_list
        ],
    }

    new_df = pd.DataFrame(data_dict)

    for column in new_df.select_dtypes(include=["object"]).columns:
        new_df[column] = new_df[column].apply(
            lambda x: x.strip() if isinstance(x, str) else x
        )

    new_df.to_csv("data/data.csv")

    print(new_df.head())


def create_test_dataset():
    df = pd.read_csv("data/data.csv")
    test_df = df[["Text", "Source", "Confidence Score"]]
    test_df.to_csv("data/test.csv", index=False)
    print(test_df.head())
    print(test_df.info())


def preprocess():
    df = pd.read_csv("data/test.csv")
    print(df.info())
    print(df.head())


def test_sentiment_analysis(real: list, pred: list):
    accuracy = accuracy_score(real, pred)
    print(f"Accuracy: {accuracy:.2f}")


# def sentiment_analysis(text_list: list) -> list:
#     sentiment_list = nlp(text_list)
#     sentiment_list = [sentiment["label"] for sentiment in sentiment_list]
#     return sentiment_list


def convert_sentiment(compound: float) -> str:
    if compound >= 0.01:
        return "Positive"
    elif compound <= -0.01:
        return "Negative"
    else:
        return "Neutral"
