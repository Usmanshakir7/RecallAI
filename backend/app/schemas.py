
from typing import List, Optional
from pydantic import BaseModel, field_validator

MAX_TRANSCRIPT_CHARS = 100_000


class TranscriptRequest(BaseModel):
    transcript: str

    @field_validator("transcript")
    @classmethod
    def check_transcript(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Transcript cannot be empty.")
        if len(v) > MAX_TRANSCRIPT_CHARS:
            raise ValueError("Transcript is too long.")
        return v


class ActionItem(BaseModel):
    task: str
    owner: Optional[str] = None


class InsightsResponse(BaseModel):
    status: str
    summary: str
    topics: List[str]
    decisions: List[str]
    action_items: List[ActionItem]

