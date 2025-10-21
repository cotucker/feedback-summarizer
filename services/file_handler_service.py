from fastapi.datastructures import UploadFile
import pandas as pd



def get_dataset_from_file_path(file_path: str) -> pd.DataFrame:
    df = pd.read_csv(file_path)
    return df

def get_dataset_from_file(file: UploadFile) -> pd.DataFrame:
    df = pd.read_csv(file.file)
    return df

def create_dataset_from_sentiment_response_list(sentiments_list) -> pd.DataFrame:
    df = pd.DataFrame({
        'text': [sentiment.text for sentiment in sentiments_list],
        'sentiment': [sentiment.sentiment.value for sentiment in sentiments_list],
        'topic': [sentiment.topic for sentiment in sentiments_list]
    })
    df.to_csv('data/sentiment_data.csv', index=False)
    return df
