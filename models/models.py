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
    # sentiment: Sentiment

class TopicSummary(BaseModel):
    topic: str
    summary: str

class TotalSummary(BaseModel):
    summary: str

class Separator(BaseModel):
    separator: str

class ClusterName(BaseModel):
    name: str

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
