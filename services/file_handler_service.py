from fastapi.datastructures import UploadFile
import pandas as pd



def get_dataset_from_file_path(file_path: str) -> pd.DataFrame:
    df = pd.read_csv(file_path)
    return df

def get_dataset_from_file(file: UploadFile) -> pd.DataFrame:
    df = pd.read_csv(file.file)
    return df