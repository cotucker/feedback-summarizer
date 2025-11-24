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
