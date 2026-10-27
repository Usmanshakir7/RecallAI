"""Small client for the H-MEM memory service (Node.js)."""

import os

import requests


def is_configured() -> bool:
    """Return True if the H-MEM service address is set."""
    return bool(os.getenv("HMEM_URL"))


def _base_url() -> str:
    return os.getenv("HMEM_URL", "").rstrip("/")


def ping() -> bool:
    """Check that the H-MEM service is running."""
    response = requests.get(f"{_base_url()}/healthz", timeout=5)
    return response.status_code == 200


def add_memory(content: str, source: str, tags=None) -> dict:
    """Save one memory. A source is required by H-MEM."""
    response = requests.post(
        f"{_base_url()}/add",
        json={"content": content, "source": source, "tags": tags or []},
        timeout=10,
    )
    response.raise_for_status()
    return response.json()


def recall(query: str, top_n: int = 3, threshold: float = 0.1) -> list:
    """Return memories related to the query, best match first."""
    response = requests.post(
        f"{_base_url()}/query",
        json={"query": query, "topN": top_n, "threshold": threshold},
        timeout=10,
    )
    response.raise_for_status()
    return response.json().get("memories", [])


def remember_decisions(decisions: list, source: str) -> int:
    """Save decisions on a best-effort basis. Never raises. Returns how many were saved."""
    if not is_configured():
        return 0
    saved = 0
    for decision in decisions:
        try:
            add_memory(decision, source, ["decision"])
            saved += 1
        except requests.RequestException:
            pass
    return saved