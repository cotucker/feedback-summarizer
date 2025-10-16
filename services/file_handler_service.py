import pandas as pd


def get_dataset(file_path: str) -> pd.DataFrame:
    df = pd.read_csv(file_path)
    return df