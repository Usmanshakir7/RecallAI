import pytest
import requests
from fastapi.testclient import TestClient

import app.main as main_module
from app.main import app
from app.services import hmem_client, zetaris_client, tasks_service

client = TestClient(app)

VALID_TRANSCRIPT = "This is a valid transcript for testing purposes."
FAKE_INSIGHTS = {
    "status": "completed",
    "summary": "s",
    "topics": [],
    "decisions": ["Use Zetaris"],
    "action_items": [],
}


def test_health_hmem_not_configured():
    assert client.get("/health/hmem").json() == {"status": "not_configured"}


def test_health_hmem_ok(monkeypatch):
    monkeypatch.setenv("HMEM_URL", "http://hmem.test")
    monkeypatch.setattr(hmem_client, "ping", lambda: True)
    assert client.get("/health/hmem").json() == {"status": "ok"}


def test_health_hmem_unreachable(monkeypatch):
    monkeypatch.setenv("HMEM_URL", "http://hmem.test")

    def down():
        raise requests.ConnectionError("down")

    monkeypatch.setattr(hmem_client, "ping", down)
    assert client.get("/health/hmem").json() == {"status": "unreachable"}


def test_health_zetaris_not_configured():
    assert client.get("/health/zetaris").json() == {"status": "not_configured"}


def test_health_zetaris_ok(monkeypatch):
    monkeypatch.setenv("ZETARIS_API_KEY", "test-key")
    monkeypatch.setattr(zetaris_client, "ping", lambda: True)
    assert client.get("/health/zetaris").json() == {"status": "ok"}


def test_health_zetaris_unreachable(monkeypatch):
    monkeypatch.setenv("ZETARIS_API_KEY", "test-key")

    def down():
        raise zetaris_client.ZetarisError("down")

    monkeypatch.setattr(zetaris_client, "ping", down)
    assert client.get("/health/zetaris").json() == {"status": "unreachable"}


def test_memory_recall_not_configured():
    response = client.get("/memory/recall", params={"q": "analytics"})
    assert response.status_code == 503


def test_memory_recall_returns_memories(monkeypatch):
    monkeypatch.setenv("HMEM_URL", "http://hmem.test")
    fake = [{"id": "mem-1", "content": "Use Zetaris"}]
    monkeypatch.setattr(hmem_client, "recall", lambda q: fake)
    response = client.get("/memory/recall", params={"q": "analytics"})
    assert response.status_code == 200
    assert response.json() == {"query": "analytics", "memories": fake}


def test_memory_recall_unreachable(monkeypatch):
    monkeypatch.setenv("HMEM_URL", "http://hmem.test")

    def down(q):
        raise requests.ConnectionError("down")

    monkeypatch.setattr(hmem_client, "recall", down)
    response = client.get("/memory/recall", params={"q": "analytics"})
    assert response.status_code == 502


def test_analyze_saves_decisions(monkeypatch):
    saved = []

    def fake_remember(decisions, source):
        saved.append((decisions, source))
        return len(decisions)

    monkeypatch.setattr(main_module, "generate_insights", lambda t: FAKE_INSIGHTS)
    monkeypatch.setattr(hmem_client, "remember_decisions", fake_remember)
    response = client.post("/analyze", json={"transcript": VALID_TRANSCRIPT})
    assert response.status_code == 200
    assert saved == [(["Use Zetaris"], "meeting-transcript")]


def test_analyze_works_when_hmem_is_down(monkeypatch):
    monkeypatch.setenv("HMEM_URL", "http://hmem.test")

    def down(*args, **kwargs):
        raise requests.ConnectionError("down")

    monkeypatch.setattr(main_module, "generate_insights", lambda t: FAKE_INSIGHTS)
    monkeypatch.setattr(hmem_client, "add_memory", down)
    response = client.post("/analyze", json={"transcript": VALID_TRANSCRIPT})
    assert response.status_code == 200
    
def test_tasks_check_not_configured():
    response = client.post("/tasks/check", json={"owners": ["John Doe"]})
    assert response.status_code == 503


def test_tasks_check_returns_open_tasks(monkeypatch):
    monkeypatch.setenv("ZETARIS_API_KEY", "test-key")
    captured = {}

    def fake_run_sql(sql, limit=100, timeout=60):
        captured["sql"] = sql
        return [["T-101", "Fix login bug", "John Doe", "Open"]]

    monkeypatch.setattr(zetaris_client, "run_sql", fake_run_sql)
    response = client.post("/tasks/check", json={"owners": ["John Doe"]})
    assert response.status_code == 200
    assert response.json() == {
        "owners_checked": ["John Doe"],
        "open_tasks": [
            {"id": "T-101", "title": "Fix login bug", "owner": "John Doe", "status": "Open"}
        ],
    }
    assert "'john doe'" in captured["sql"]


def test_tasks_check_escapes_quotes(monkeypatch):
    monkeypatch.setenv("ZETARIS_API_KEY", "test-key")
    captured = {}

    def fake_run_sql(sql, limit=100, timeout=60):
        captured["sql"] = sql
        return []

    monkeypatch.setattr(zetaris_client, "run_sql", fake_run_sql)
    tasks_service.get_open_tasks(["x' OR '1'='1"])
    assert "\\'" in captured["sql"]


def test_tasks_check_unreachable(monkeypatch):
    monkeypatch.setenv("ZETARIS_API_KEY", "test-key")

    def down(*args, **kwargs):
        raise zetaris_client.ZetarisError("down")

    monkeypatch.setattr(zetaris_client, "run_sql", down)
    response = client.post("/tasks/check", json={"owners": ["John Doe"]})
    assert response.status_code == 502