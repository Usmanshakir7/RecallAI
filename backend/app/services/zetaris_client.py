"""Small client for the Zetaris REST API."""

import os
import uuid

import requests

DEFAULT_URL = "http://localhost:8888/api/v1.0"


class ZetarisError(Exception):
    """Raised when a Zetaris request fails."""


def is_configured() -> bool:
    """Return True if an API key is set."""
    return bool(os.getenv("ZETARIS_API_KEY"))


def run_sql(sql: str, limit: int = 100, timeout: int = 60) -> list:
    """Run one SQL statement and return the rows (a list of lists).

    Zetaris returns every value as a string.
    """
    if not sql or not sql.strip():
        raise ZetarisError("SQL must not be empty.")

    api_key = os.getenv("ZETARIS_API_KEY", "")
    if not api_key:
        raise ZetarisError("ZETARIS_API_KEY is not set.")

    base_url = os.getenv("ZETARIS_REST_URL", DEFAULT_URL).rstrip("/")
    headers = {
        "Authorization": f"Bearer {api_key}",
        "X-Org-ID": os.getenv("ZETARIS_ORG_ID", "1"),
        "X-Request-ID": str(uuid.uuid4()),
        "Content-Type": "application/json",
    }
    body = {
        "queryId": str(uuid.uuid4()),
        "sql": sql,
        "source": "SqlEditor",
        "limit": limit,
    }

    try:
        response = requests.post(
            f"{base_url}/sql-editor/sqls/run",
            json=body,
            headers=headers,
            timeout=timeout,
        )
    except requests.RequestException as error:
        raise ZetarisError(f"Cannot reach Zetaris: {error}") from error

    if response.status_code != 200:
        raise ZetarisError(
            f"Zetaris returned HTTP {response.status_code}: {response.text[:200]}"
        )

    data = response.json()
    rows = data.get("data") if isinstance(data, dict) else None
    return rows or []


def ping() -> bool:
    """Check that Zetaris answers a simple query."""
    return run_sql("SELECT 1") == [["1"]]