from fastapi.testclient import TestClient

from app import main
from app.main import app
from app.services import trace

client = TestClient(app)


def test_trace_records_success():
    trace.clear()
    r = client.post("/analyze", json={"transcript": "Ali will send the report by Friday."})
    assert r.status_code == 200
    data = client.get("/trace").json()
    assert len(data) == 1
    assert data[0]["agent"] == "insights"
    assert data[0]["status"] == "ok"


def test_trace_records_failure(monkeypatch):
    trace.clear()

    def boom(_):
        raise RuntimeError("fail")

    monkeypatch.setattr(main, "generate_insights", boom)
    r = client.post("/analyze", json={"transcript": "Some meeting text."})
    assert r.status_code == 502
    data = client.get("/trace").json()
    assert data[0]["status"] == "error"
    assert data[0]["error"] == "RuntimeError"
    
def test_trace_model_in_sample_mode(monkeypatch):
    monkeypatch.setattr(trace, "SAMPLE_MODE", True)
    trace.clear()
    client.post("/analyze", json={"transcript": "Ali will send the report by Friday."})
    assert trace.get_all()[0]["model"] == "sample-mode"


def test_trace_model_in_live_mode(monkeypatch):
    monkeypatch.setattr(trace, "SAMPLE_MODE", False)
    monkeypatch.setenv("AI_MODEL", "test-model")
    trace.clear()
    client.post("/analyze", json={"transcript": "Ali will send the report by Friday."})
    assert trace.get_all()[0]["model"] == "test-model"