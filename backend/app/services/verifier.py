
def verify_insights(transcript: str, insights: dict) -> dict:
    """Flag unsupported decisions, tasks, and owners."""

    normalized_transcript = " ".join(transcript.casefold().split())

    unsupported_decisions = []

    for decision in insights.get("decisions", []):
        normalized_decision = " ".join(decision.casefold().split())

        if normalized_decision not in normalized_transcript:
            unsupported_decisions.append(decision)

    unsupported_action_items = []

    for item in insights.get("action_items", []):
        task = item.get("task", "")
        owner = item.get("owner")

        normalized_task = " ".join(task.casefold().split())
        task_unsupported = (
            not normalized_task
            or normalized_task not in normalized_transcript
        )

        normalized_owner = (
            " ".join(owner.casefold().split())
            if isinstance(owner, str)
            else ""
        )
        owner_unsupported = (
            bool(normalized_owner)
            and normalized_owner not in normalized_transcript
        )

        if task_unsupported or owner_unsupported:
            unsupported_action_items.append(item)

    return {
        "passed": (
            not unsupported_decisions
            and not unsupported_action_items
        ),
        "unsupported_decisions": unsupported_decisions,
        "unsupported_action_items": unsupported_action_items,
    }
