import json
import re
import time
import uuid
from pathlib import Path

# backend/data/meetings/
DATA_DIR = Path(__file__).resolve().parents[2] / "data" / "meetings"
_ID_RE = re.compile(r"^[a-f0-9]{8}$")


def new_id():
    return uuid.uuid4().hex[:8]


def save(meeting_id, result):
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    # data folder git mein na jaye
    ignore = DATA_DIR.parent / ".gitignore"
    if not ignore.exists():
        ignore.write_text("*\n", encoding="utf-8")
    record = {
        "meeting_id": meeting_id,
        "saved_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "result": result,
    }
    path = DATA_DIR / f"{meeting_id}.json"
    path.write_text(json.dumps(record, indent=2), encoding="utf-8")


def load(meeting_id):
    # sirf 8 hex characters allow, taake koi galat path na de sake
    if not _ID_RE.match(meeting_id):
        return None
    path = DATA_DIR / f"{meeting_id}.json"
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))