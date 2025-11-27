from fastapi.datastructures import UploadFile
from fastapi import HTTPException
import pandas as pd
import io

POCESSED_DF: pd.DataFrame = pd.DataFrame()
RESULTS_DF: pd.DataFrame = pd.DataFrame()


def get_dataset_from_file_path(file_path: str) -> pd.DataFrame:
    df = pd.read_csv(file_path)
    return df

import io
import pandas as pd
from fastapi import UploadFile, HTTPException

async def get_dataset_from_file(
    file: UploadFile, get_separator, topics: str, columns: str
):
    if file.filename is None:
        raise HTTPException(
            status_code=400, detail="No filename provided for the uploaded file."
        )

    filetype = file.filename.split(".")[-1].lower()
    allowed_extensions = ["csv", "txt", "json", "xlsx"]

    if filetype not in allowed_extensions:
        raise HTTPException(
            status_code=400,
            detail="Invalid file type. Please upload a CSV | TXT | JSON | XLSX.",
        )

    try:
        df: pd.DataFrame
        match filetype:
            case "csv":
                df = pd.read_csv(file.file)
            case "txt":
                contents = await file.read()
                decoded_content = contents.decode("utf-8")
                lines = decoded_content.splitlines()
                if len(lines) == 0:
                    raise HTTPException(status_code=400, detail="Empty TXT file.")
                separator = get_separator(lines[0])
                if separator == "null":
                    df = pd.DataFrame({"Text": lines})
                else:
                    df = pd.read_csv(io.StringIO(decoded_content), sep=separator)
            case "json":
                df = pd.read_json(file.file)
            case "xlsx":
                contents = await file.read()
                buffer = io.BytesIO(contents)
                df = pd.read_excel(buffer)

        if columns: # User provided columns
            column_names = [col.strip() for col in columns.split(',')]
        else: # No columns provided, use defaults 'Text', 'Rating'
            column_names = ["Text", "Rating"]

        if len(column_names) < 1:
            raise HTTPException(status_code=400, detail="Invalid columns parameter. Please provide at least one column name (e.g., 'Text').")

        text_column_name = column_names[0]
        rating_column_name = column_names[1] if len(column_names) > 1 else None

        if text_column_name not in df.columns:
            raise HTTPException(status_code=400, detail=f"Text column '{text_column_name}' not found in the file. Available columns: {', '.join(df.columns)}")

        columns_to_select = [text_column_name]
        rename_dict = {text_column_name: "Text"}

        if rating_column_name and rating_column_name in df.columns:
            columns_to_select.append(rating_column_name)
            rename_dict[rating_column_name] = "Rating"
        elif rating_column_name and rating_column_name not in df.columns:
            # If rating column was specified but not found, log a warning or just ignore it
            # For now, we'll just not include it.
            pass

        df = df[columns_to_select].copy()
        df.rename(columns=rename_dict, inplace=True)

        df.dropna(subset=["Text"], inplace=True)
        df = df[df["Text"].astype(str).str.strip() != ""]
        df.reset_index(drop=True, inplace=True)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error loading file: {e}")

    if df.shape[0] < 30:
        raise HTTPException(
            status_code=400, detail="Dataset requires at least 30 valid text rows."
        )
    if df.shape[0] > 15000:
        raise HTTPException(
            status_code=400, detail="Dataset size exceeds 15,000 rows."
        )

    global POCESSED_DF
    POCESSED_DF = df.copy()

    if "Text" in POCESSED_DF.columns:
        text_series = POCESSED_DF["Text"]
    else:
        text_series = pd.Series([], dtype=object)

    if "Rating" in POCESSED_DF.columns:
        rating_series = POCESSED_DF["Rating"]
    else:
        rating_series = pd.Series([], dtype=object)

    return text_series, rating_series

def create_dataset_from_sentiment_response_list(sentiments_list):
    df = pd.DataFrame(
        {
            "text": [sentiment.text for sentiment in sentiments_list],
            "sentiment": [sentiment.sentiment for sentiment in sentiments_list],
            "topic": [sentiment.topic for sentiment in sentiments_list],
        }
    )
    global RESULTS_DF
    RESULTS_DF = df.copy()


def get_feedback_list() -> list[str]:
    df = POCESSED_DF
    return df["Text"].dropna().apply(process_text).values.tolist()


def process_text(text) -> str:
    import re

    if not isinstance(text, str):
        text = str(text)
    return re.sub(r"\d+", "", text)


def get_topics_list() -> list[str]:
    df = RESULTS_DF
    return df["topic"].apply(process_text).values.tolist()


def get_feedback_analysis_by_topic(topic: str | None) -> list[str]:
    df = RESULTS_DF.copy()
    if topic:
        df = df[df["topic"] == topic]
    return df["text"].values.tolist()


def get_feedbacks_info() -> list[str]:
    df = RESULTS_DF
    return ("'" + df["Text"].astype(str) + "'. " + df["Rating"].astype(str)).tolist()
