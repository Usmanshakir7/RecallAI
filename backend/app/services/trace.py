import os
import time
from threading import Lock

_TRACE = []
_LOCK = Lock()
MAX_ENTRIES = 200


def current_model():
    return os.getenv("AI_MODEL") or "not-set"


def record(agent, model, status, duration_ms, error=None):
    entry = {
        "time": time.strftime("%Y-%m-%d %H:%M:%S"),
        "agent": agent,
        "model": model,
        "status": status,
        "duration_ms": duration_ms,
        "error": error,
    }
    with _LOCK:
        _TRACE.append(entry)
        del _TRACE[:-MAX_ENTRIES]


def get_all():
    with _LOCK:
        return list(_TRACE)


def clear():
    with _LOCK:
        _TRACE.clear()