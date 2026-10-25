
def generate_insights(transcript: str) -> dict:
    """Generate structured insights from a meeting transcript."""

    if not transcript.strip():
        raise ValueError("Transcript cannot be empty")

    return {
        "summary": "",
        "topics": [],
        "decisions": [],
        "action_items": [],
        "open_questions": [],
        "original_transcript": transcript
    }
