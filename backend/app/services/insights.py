import json
import os
import re
from difflib import SequenceMatcher
from pathlib import Path

from dotenv import load_dotenv
from google import genai
from google.genai import types


# Go 3 folders up from this file to find the project root, then load .env
PROJECT_ROOT = Path(__file__).resolve().parents[3]
load_dotenv(PROJECT_ROOT / ".env")

MODEL = os.getenv("AI_MODEL", "gemini-3.5-flash-lite")

# Words that look like names but are not real owners.
# "This will be done" should NOT make "This" the owner.
NOT_OWNER_WORDS = {
    "the team", "we", "i", "it", "this", "that",
    "everyone", "someone", "they", "he", "she", "there",
}


def remove_duplicates(items: list[str]) -> list[str]:
    """Remove duplicate strings while keeping the original order."""
    result = []
    seen = set()

    for item in items:
        # Skip anything that is not a string
        if not isinstance(item, str):
            continue

        cleaned = item.strip()
        key = cleaned.casefold()

        # Keep only non-empty items we have not seen before
        if cleaned and key not in seen:
            seen.add(key)
            result.append(cleaned)

    return result


def _normalize(text: str) -> str:
    """Lowercase the text and collapse extra spaces."""
    return " ".join(text.casefold().split())


def _is_transcript_copy(text: str, transcript: str) -> bool:
    """Return True if the text is empty or just a copy of the transcript."""
    normalized_text = _normalize(text)
    normalized_transcript = _normalize(transcript)

    # Empty text or exact copy of the whole transcript
    if not normalized_text or normalized_text == normalized_transcript:
        return True

    word_count = len(normalized_text.split())
    similarity = SequenceMatcher(
        None, normalized_text, normalized_transcript
    ).ratio()

    # Very long text, or long text that is very similar to the transcript
    return word_count > 25 or (
        len(normalized_text) >= 100 and similarity >= 0.60
    )


def _clean_topics(items: list, transcript: str) -> list[str]:
    """Keep only short topic labels (max 5)."""
    cleaned = []

    for item in items:
        if not isinstance(item, str):
            continue

        # Remove extra spaces and leading bullets or dashes
        topic = re.sub(r"\s+", " ", item).strip(" \t\r\n-•")

        if not topic or _is_transcript_copy(topic, transcript):
            continue

        # Topics must be short labels, not full sentences
        if len(topic.split()) > 8 or re.search(r"[.!?]", topic):
            continue

        cleaned.append(topic)

    return remove_duplicates(cleaned)[:5]


def _clean_decisions(items: list, transcript: str) -> list[str]:
    """Keep only valid decisions that are not copies of the transcript."""
    cleaned = []

    for item in items:
        if not isinstance(item, str):
            continue

        decision = re.sub(r"\s+", " ", item).strip()

        if decision and not _is_transcript_copy(decision, transcript):
            cleaned.append(decision)

    return remove_duplicates(cleaned)


def _clean_action_items(items: list, transcript: str) -> list[dict]:
    """Keep only valid action items shaped like {"task": ..., "owner": ...}."""
    cleaned = []
    seen = set()

    for item in items:
        if not isinstance(item, dict):
            continue

        task = item.get("task")
        owner = item.get("owner")

        if not isinstance(task, str):
            continue

        task = re.sub(r"\s+", " ", task).strip(" \t\r\n-•")

        if not task or _is_transcript_copy(task, transcript):
            continue

        # Reject tasks that contain several full sentences
        if len(re.findall(r"[.!?]", task)) > 1:
            continue

        # Owner must be a non-empty string, otherwise use None
        if not isinstance(owner, str) or not owner.strip():
            owner = None
        else:
            owner = owner.strip()

        key = (task.casefold(), (owner or "").casefold())

        if key not in seen:
            seen.add(key)
            cleaned.append({"task": task, "owner": owner})

    return cleaned


def generate_fallback_insights(transcript: str) -> dict:
    """Generate basic insights using simple rules (no Gemini needed)."""
    lines = [
        line.strip()
        for line in transcript.splitlines()
        if line.strip()
    ]

    decisions = []
    action_items = []
    open_questions = []
    topics = []

    for line in lines:
        lower_line = line.casefold()

        # Track if this line is already a decision, action, or question.
        # Those lines should not also become topics.
        used_elsewhere = False

        # Decisions: short lines with words like "decided" or "agreed"
        if any(
            word in lower_line
            for word in ("decided", "agreed", "will use")
        ):
            decisions.append(line.rstrip(".!?"))
            used_elsewhere = True
        # Recognize commitments such as:
        # "Usman will complete the dashboard."
        # "Sara: I will test the API."
        # "We will review the design."

        speaker_match = re.match(
            r"^(?P<speaker>[A-Za-z][A-Za-z'-]*):\s*"
            r"(?P<statement>.+)$",
            line,
        )

        if speaker_match:
            speaker = speaker_match.group("speaker").strip()
            statement = speaker_match.group("statement").strip()

            if re.match(r"^(I|We)\s+will\b", statement, re.IGNORECASE):
                action_items.append({
                    "task": statement.rstrip(".!?"),
                    "owner": speaker,
                })
                used_elsewhere = True

        else:
            match = re.match(
                r"^(?P<owner>[A-Za-z][A-Za-z'-]*(?:\s+team)?)"
                r"\s+will\s+(?P<task>.+)$",
                line,
                flags=re.IGNORECASE,
            )

            if match:
                owner_text = match.group("owner").strip()
                task = match.group("task").strip().rstrip(".!?")

                owner = (
                    None
                    if owner_text.casefold() in NOT_OWNER_WORDS
                    else owner_text
                )

                if task:
                    if owner is None:
                        task = f"{owner_text} will {task}"

                    action_items.append({
                        "task": task,
                        "owner": owner,
                    })
                    used_elsewhere = True


        # Explicit labels such as "Action: ..." or "TODO: ..."
        if lower_line.startswith(("action:", "todo:")):
            _, task = line.split(":", 1)
            if task.strip():
                action_items.append({"task": task.strip(), "owner": None})
                used_elsewhere = True

        # Any line with a question mark is an open question
        if "?" in line:
            open_questions.append(line)
            used_elsewhere = True
        # Extract short topics sentence by sentence.
        sentences = re.split(r"(?<=[.!?])\s+", line)

        for sentence in sentences:
            original_sentence = sentence.strip()
            topic = original_sentence.rstrip(".!?").strip()
            lower_sentence = topic.casefold()

            if not topic:
                continue

            # Skip decisions and questions.
            if any(
                word in lower_sentence
                for word in ("decided", "agreed", "will use")
            ):
                continue

            if "?" in original_sentence:
                continue

            # Skip commitment sentences.
            if re.match(
                r"^(?:[A-Za-z][A-Za-z'-]*|we|i)\s+will\b",
                topic,
                re.IGNORECASE,
            ):
                continue

            # Keep short topic labels without punctuation.
            if 2 <= len(topic.split()) <= 8:
                topics.append(topic)



    return {
        "status": "completed",
        "summary": " ".join(lines[:3]),
        "topics": _clean_topics(topics, transcript),
        "decisions": _clean_decisions(decisions, transcript),
        "action_items": _clean_action_items(action_items, transcript),
        "open_questions": remove_duplicates(open_questions),
    }


def generate_insights(transcript: str) -> dict:
    """Generate insights with Gemini, and use the fallback if Gemini fails."""
    if not transcript or not transcript.strip():
        raise ValueError("Transcript cannot be empty.")

    fallback = generate_fallback_insights(transcript)
    api_key = os.getenv("GEMINI_API_KEY")

    # No API key means we can only use the fallback
    if not api_key:
        return fallback

    prompt = f"""
You are a meeting analysis assistant. Analyze the transcript and return
valid JSON with exactly these fields:
- summary: concise string
- topics: short topic labels, not full sentences
- decisions: explicit decisions
- action_items: objects with "task" and "owner"
- open_questions: unresolved questions

Use only information supported by the transcript.
Never copy the entire transcript or a paragraph into a field.
Extract the actual task, not its surrounding sentence or paragraph.
Use null when the responsible person is unknown.
Do not invent tasks, owners, deadlines, decisions, or questions.
Avoid duplicate entries. Return JSON only, without Markdown fences.

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

        if not isinstance(data, dict):
            raise ValueError("Gemini response must be a JSON object.")

        summary = data.get("summary", "")
        topics = data.get("topics", [])
        decisions = data.get("decisions", [])
        action_items = data.get("action_items", [])
        open_questions = data.get("open_questions", [])

        # Make sure every field has the right type
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

        # Topics: use Gemini first, use fallback only if Gemini gave none
        final_topics = _clean_topics(topics, transcript)
        if not final_topics:
            final_topics = fallback["topics"]

        # Decisions: same idea
        final_decisions = _clean_decisions(decisions, transcript)
        if not final_decisions:
            final_decisions = fallback["decisions"]

        # Action items: start with Gemini's, then add missing fallback ones
        final_action_items = _clean_action_items(action_items, transcript)

        existing_keys = {
            (item["task"].casefold(), (item["owner"] or "").casefold())
            for item in final_action_items
        }

        for item in fallback["action_items"]:
            task_key = (
                item["task"].casefold(),
                (item["owner"] or "").casefold(),
            )

            if task_key not in existing_keys:
                final_action_items.append(item)
                existing_keys.add(task_key)

        # Open questions: use Gemini first, fallback only if empty
        final_questions = remove_duplicates(
            [
                question
                for question in open_questions
                if isinstance(question, str) and question.strip()
            ]
        )
        if not final_questions:
            final_questions = fallback["open_questions"]

        return {
            "status": "completed",
            "summary": summary.strip() or fallback["summary"],
            "topics": final_topics,
            "decisions": final_decisions,
            "action_items": final_action_items,
            "open_questions": final_questions,
        }

    except Exception as error:
        # If anything goes wrong, return the rule-based result
        print(f"Gemini failed; using fallback insights. Reason: {error}")
        return fallback