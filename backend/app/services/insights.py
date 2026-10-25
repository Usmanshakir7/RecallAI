
def generate_insights(transcript: str) -> dict:
    """Extract basic meeting insights without an external AI provider."""

    if not transcript.strip():
        raise ValueError("Transcript cannot be empty.")

    lines = [
        line.strip()
        for line in transcript.splitlines()
        if line.strip()
    ]

    topics = []
    decisions = []
    action_items = []
    open_questions = []

    for line in lines:
        lower_line = line.lower()

        if any(word in lower_line for word in ["decided", "agreed", "will use"]):
            decisions.append(line)

        if any(word in lower_line for word in ["i will", "we will", "action:", "todo:"]):
            owner = None
            if ":" in line:
                possible_owner = line.split(":", 1)[0].strip()
                if possible_owner and len(possible_owner.split()) <= 3:
                    owner = possible_owner

            action_items.append({
                "task": line,
                "owner": owner,
            })

        if "?" in line:
            open_questions.append(line)

        if len(topics) < 5 and len(line.split()) >= 3:
            topics.append(line)

    summary = " ".join(lines[:3])

    return {
        "status": "completed",
        "summary": summary,
        "topics": topics,
        "decisions": decisions,
        "action_items": action_items,
        "open_questions": open_questions,
    }
