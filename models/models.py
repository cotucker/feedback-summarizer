import json
import enum
from pydantic import BaseModel

class Sentiment(enum.Enum):
    POSITIVE = "Positive"
    NEGATIVE = "Negative"
    NEUTRAL = "Neutral"

class FeedbackResponse(BaseModel):
    original_feedback_text: str
    response: str
    score: int

class SentimentResponse(BaseModel):
    text: str
    topic: str
    sentiment: str

class TopicSummary(BaseModel):
    topic: str
    summary: str

class TotalSummary(BaseModel):
    summary: str

class Separator(BaseModel):
    separator: str

class ClusterName(BaseModel):
    name: str
    description: str

class ClusterDescription(BaseModel):
    cluster_name: str
    description: str

class TopicQuality(BaseModel):
    score: int
    is_match: bool
    justification: str

class Subtext(BaseModel):
    text: str
    topic: str


CLUSTER_DESCRIPTION_SCHEMA = {
    "type": "object",
    "properties": {
        "clusters": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "cluster_name": {"type": "string"},
                    "description": {"type": "string"}
                },
                "required": ["cluster_name", "description"],
                "additionalProperties": False
            }
        }
    },
    "required": ["clusters"],
    "additionalProperties": False
}

CLUSTER_NAME_SCHEMA = {
    "type": "object",
    "properties": {
        "name": {
            "type": "string",
            "description": "A short, concise title for the cluster (2-4 words)."
        },
        "description": {
            "type": "string",
            "description": "A brief explanation of what this cluster represents."
        }
    },
    "required": ["name", "description"],
    "additionalProperties": False
}

SEPARATOR_SCHEMA = {
    "type": "object",
    "properties": {
        "separator": {
            "type": "string",
            "description": "The detected delimiter character (e.g., ',', ';', '|', '\t')."
        }
    },
    "required": ["separator"],
    "additionalProperties": False
}

TOTAL_SUMMARY_SCHEMA = {
    "type": "object",
    "properties": {
        "summary": {
            "type": "string",
            "description": "A concise summary that encapsulates the main points from the analyzed feedback."
        }
    },
    "required": ["summary"],
    "additionalProperties": False
}

TOPIC_SUMMARY_SCHEMA = {
    "type": "object",
    "properties": {
        "topic": {
            "type": "string",
            "description": "The main subject or theme of the text."
        },
        "summary": {
            "type": "string",
            "description": "A concise summary of the content related to this topic."
        }
    },
    "required": ["topic", "summary"],
    "additionalProperties": False
}

LIST_STR_SCHEMA = {
    "type": "object",
    "properties": {
        "items": {
            "type": "array",
            "items": {
                "type": "string"
            }
        }
    },
    "required": ["items"],
    "additionalProperties": False
}
