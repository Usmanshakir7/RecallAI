
def generate_insights(transcript: str) -> dict:
    """Return a placeholder response for meeting insights."""

    if not transcript.strip():
        raise ValueError("Transcript cannot be empty")

    return {
        "status": "completed",
        "summary": "",
        "topics": [],
        "decisions": [],
        "action_items": [],
    }
