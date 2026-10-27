
import json
import os
from pathlib import Path

from dotenv import load_dotenv
from google import genai
from google.genai import types


# Load environment variables from the RecallAI project root.
PROJECT_ROOT = Path(__file__).resolve().parents[3]
load_dotenv(PROJECT_ROOT / ".env")

MODEL = os.getenv("AI_MODEL", "gemini-3.5-flash-lite")


def remove_duplicates(items: list[str]) -> list[str]:
    """Remove duplicate strings while preserving their original order."""
    result = []
    seen = set()

    for item in items:
        if not isinstance(item, str):
            continue

        cleaned = item.strip()
        key = cleaned.casefold()

        if cleaned and key not in seen:
            seen.add(key)
            result.append(cleaned)

    return result


def generate_fallback_insights(transcript: str) -> dict:
    """Generate basic meeting insights without using the Gemini API."""
    lines = [
        line.strip()
        for line in transcript.splitlines()
        if line.strip()
    ]

    decisions = []
    action_items = []
    open_questions = []
    topics = []

    decision_keywords = (
        "decided",
        "agreed",
        "will use",
    )

    action_keywords = (
        "i will",
        "we will",
        "action:",
        "todo:",
    )

    for line in lines:
        lower_line = line.casefold()

        # Extract possible decisions.
        if any(keyword in lower_line for keyword in decision_keywords):
            decisions.append(line)

        # Extract possible action items and owners.
        if any(keyword in lower_line for keyword in action_keywords):
            owner = None
            task = line

            if ":" in line:
                possible_owner, remaining_text = line.split(":", 1)
                possible_owner = possible_owner.strip()

                if (
                    possible_owner
                    and len(possible_owner.split()) <= 3
                ):
                    owner = possible_owner
                    task = remaining_text.strip()

            action_items.append(
                {
                    "task": task,
                    "owner": owner,
                }
            )

        # Extract open questions.
        if "?" in line:
            open_questions.append(line)

        # Use the first five sufficiently descriptive lines as topics.
        if len(line.split()) >= 3:
            topics.append(line)

    return {
        "status": "completed",
        "summary": " ".join(lines[:3]),
        "topics": remove_duplicates(topics)[:5],
        "decisions": remove_duplicates(decisions),
        "action_items": action_items,
        "open_questions": remove_duplicates(open_questions),
    }


def generate_insights(transcript: str) -> dict:
    """Generate meeting insights with Gemini and a rule-based fallback."""
    if not transcript or not transcript.strip():
        raise ValueError("Transcript cannot be empty.")

    fallback = generate_fallback_insights(transcript)

    api_key = os.getenv("GEMINI_API_KEY")

    # Continue without Gemini when no API key is configured.
    if not api_key:
        return fallback

    prompt = f"""
Analyze the following meeting transcript.

Return valid JSON with these exact fields:
- summary: a concise string
- topics: a list of strings
- decisions: a list of strings
- action_items: a list of objects containing "task" and "owner"
- open_questions: a list of strings

Rules:
1. Use only information supported by the transcript.
2. Do not invent decisions, tasks, owners, or deadlines.
3. Use null for an unknown action-item owner.
4. Preserve important names and commitments.
5. Keep action items clear and specific.
6. If a category has no supported information, return an empty list.
7. Return JSON only.

MEETING TRANSCRIPT:
{transcript}
"""

    try:
        client = genai.Client(api_key=api_key)

        response = client.models.generate_content(
            model=MODEL,
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                temperature=0.2,
            ),
        )

        if not response.text:
            raise ValueError("Gemini returned an empty response.")

        data = json.loads(response.text)

        # Validate and normalize Gemini's response.
        summary = data.get("summary", "")
        topics = data.get("topics", [])
        decisions = data.get("decisions", [])
        action_items = data.get("action_items", [])
        open_questions = data.get("open_questions", [])

        if not isinstance(summary, str):
            summary = ""

        if not isinstance(topics, list):
            topics = []

        if not isinstance(decisions, list):
            decisions = []

        if not isinstance(action_items, list):
            action_items = []

        if not isinstance(open_questions, list):
            open_questions = []

        # Keep only valid action-item objects.
        valid_action_items = []

        for item in action_items:
            if not isinstance(item, dict):
                continue

            task = item.get("task")
            owner = item.get("owner")

            if not isinstance(task, str) or not task.strip():
                continue

            if not isinstance(owner, str) or not owner.strip():
                owner = None
            else:
                owner = owner.strip()

            valid_action_items.append(
                {
                    "task": task.strip(),
                    "owner": owner,
                }
            )

        # Combine AI insights with transcript-based extraction.
        # This helps retain explicit commitments that Gemini misses.
        combined_topics = remove_duplicates(
            [
                item
                for item in topics + fallback["topics"]
                if isinstance(item, str)
            ]
        )[:5]

        combined_decisions = remove_duplicates(
            [
                item
                for item in decisions + fallback["decisions"]
                if isinstance(item, str)
            ]
        )

        combined_action_items = list(valid_action_items)

        existing_tasks = {
            item["task"].casefold().strip()
            for item in combined_action_items
        }

        for item in fallback["action_items"]:
            task_key = item["task"].casefold().strip()

            if task_key not in existing_tasks:
                combined_action_items.append(item)
                existing_tasks.add(task_key)

        combined_questions = remove_duplicates(
            [
                item
                for item in open_questions + fallback["open_questions"]
                if isinstance(item, str)
            ]
        )

        return {
            "status": "completed",
            "summary": summary.strip() or fallback["summary"],
            "topics": combined_topics,
            "decisions": combined_decisions,
            "action_items": combined_action_items,
            "open_questions": combined_questions,
        }

    except Exception as error:
        # If Gemini fails, the application can still return basic insights.
        print(
            f"Gemini failed; using fallback insights. "
            f"Reason: {error}"
        )
        return fallback
