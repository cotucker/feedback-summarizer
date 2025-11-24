from fastapi.datastructures import UploadFile
from fastapi import HTTPException
import pandas as pd
import io

POCESSED_DF: pd.DataFrame = pd.DataFrame()
RESULTS_DF: pd.DataFrame = pd.DataFrame()


def get_dataset_from_file_path(file_path: str) -> pd.DataFrame:
    df = pd.read_csv(file_path)
    return df


async def get_dataset_from_file(
    file: UploadFile, process_columns, get_separator, topics: str = ""
):
    if file.filename is None:
        raise HTTPException(
            status_code=400, detail="No filename provided for the uploaded file."
        )
    filetype = file.filename.split(".")[-1]
    if filetype not in ["csv", "txt", "json", "xlsx"]:
        raise HTTPException(
            status_code=400,
            detail="Invalid file type. Please upload a CSV | TXT | JSON | XLSX.",
        )

    try:
        match filetype:
            case "csv":
                df = pd.read_csv(file.file)
            case "txt":
                contents = await file.read()
                file.file.seek(0)
                decoded_content = contents.decode("utf-8")
                lines = decoded_content.splitlines()
                separator = get_separator(lines[0])
                if separator == "null":
                    raise ValueError("Separator not detected")
                df = pd.read_csv(file.file, sep=separator)
            case "json":
                df = pd.read_json(file.file)
            case "xlsx":
                contents = await file.read()
                buffer = io.BytesIO(contents)
                df = pd.read_excel(buffer)

        flag1, flag2 = False, False
        for col in df.columns.tolist():
            match col.lower():
                case "text":
                    df.rename(columns={col: "Text"}, inplace=True)
                    flag1 = True
                case "rating":
                    df.rename(columns={col: "Rating"}, inplace=True)
                    flag2 = True
            if flag1 and flag2:
                df = df[["Text", "Rating"]]
                break

        if not (flag1 and flag2):
            print(f"columns: {df.columns.tolist()}")
            selected_columns = process_columns(df.columns.tolist())
            print(f"selected_columns: {selected_columns}")
            if '' in selected_columns:
                raise HTTPException(
                    status_code=400,
                    detail="Could not detect 'Text' and 'Rating' columns in the dataset.",
                )
            if len(selected_columns) == 2:
                df = df[selected_columns]
                df.rename(
                    columns={
                        selected_columns[0]: "Text",
                        selected_columns[1]: "Rating",
                    },
                    inplace=True,
                )
            else:
                raise HTTPException(
                    status_code=400,
                    detail="Could not detect 'Text' and 'Rating' columns in the dataset.",
                )

    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error loading file: {e}")

    if df.shape[0] < 30:
        raise HTTPException(
            status_code=400, detail="t-SNE algorithm requires at least 30 data points"
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
