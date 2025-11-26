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
    file: UploadFile, process_columns, get_separator, topics: str = ""
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

        cols_map = {c.lower().strip(): c for c in df.columns}

        text_col_exact = cols_map.get("text")
        rating_col_exact = cols_map.get("rating")


        if text_col_exact and rating_col_exact:
            df = df[[text_col_exact, rating_col_exact]].copy()
            df.rename(columns={text_col_exact: "Text", rating_col_exact: "Rating"}, inplace=True)
        else:
            selected_columns = process_columns(df.columns.tolist())
            text_col_llm = selected_columns[0]
            rating_col_llm = selected_columns[1] if len(selected_columns) > 1 else ""

            if text_col_llm and text_col_llm in df.columns:
                rename_dict = {text_col_llm: "Text"}

                if rating_col_llm and rating_col_llm in df.columns:
                    rename_dict[rating_col_llm] = "Rating"

                df.rename(columns=rename_dict, inplace=True)
            else:
                raise HTTPException(
                    status_code=400,
                    detail="Could not detect 'Text' column in the dataset.",
                )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error loading file: {e}")

    if df.shape[0] < 30:
        raise HTTPException(
            status_code=400, detail="t-SNE algorithm requires at least 30 data points"
        )

    if df.shape[0] > 15000:
        raise HTTPException(
            status_code=400, detail="Dataset size exceeds the maximum limit of 15,000 rows."
        )

    global POCESSED_DF
    POCESSED_DF = df.copy()

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
