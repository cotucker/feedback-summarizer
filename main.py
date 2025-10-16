import pandas as pd
import nltk, os
from dotenv import load_dotenv
from nltk.sentiment.vader import SentimentIntensityAnalyzer
from sklearn.metrics import accuracy_score
from google import genai
from google.genai import types

load_dotenv()

GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')

client = genai.Client(api_key=GEMINI_API_KEY)
response = client.models.generate_content(
    model="gemini-flash-latest",
    contents="Explain how AI works in a few words",
)
print(response.text)

def main():
    process_dataset()
    create_test_dataset()

    df = pd.read_csv("data/data0.csv")
    print(df.info())
    print(df.head())
    text_list = df["Text"].apply(process_text).values.tolist()
    sentiment_list = sentiment_analysis(text_list)
    # print(sentiment_list[:5])
    df["Sentiment"] = sentiment_list
    df.to_csv("data/res.csv", index=False)

    # real = pd.read_csv("data/data.csv")["Sentiments"].values.tolist()
    # test_sentiment_analysis(real, sentiment_list)


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
        "Confidence Score": [segmented_data[6] for segmented_data in segmented_data_list],
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


def sentiment_analysis(text_list: list) -> list:
    try:
        nltk.data.find("sentiment/vader_lexicon.zip")
    except LookupError:
        nltk.download("vader_lexicon")

    sentiment_list = [
        SentimentIntensityAnalyzer().polarity_scores(text) for text in text_list
    ]
    print(sentiment_list[:5])

    return [
        convert_sentiment(sentiment['compound']) + f' ({sentiment["compound"]:.2f})'
        for sentiment in sentiment_list
    ]

def convert_sentiment(compound: float) -> str:
    if compound >= 0.01:
        return 'Positive'
    elif compound <= -0.01:
        return 'Negative'
    else:
        return 'Neutral'


if __name__ == "__main__":
    main()
