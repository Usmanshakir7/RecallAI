from fastapi.testclient import TestClient

import app.main as main_module
from app.main import app

client = TestClient(app)

EXPECTED_KEYS = {"status", "summary", "topics", "decisions", "action_items", "meeting_id"}
VALID_TRANSCRIPT = "This is a valid transcript for testing purposes."

def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
    
def test_analyze_valid_transcript():
    response = client.post("/analyze", json={"transcript": VALID_TRANSCRIPT})
    assert response.status_code == 200
    assert set(response.json().keys()) == EXPECTED_KEYS
    
def test_analyze_same_structure_every_time():
    first_response = client.post("/analyze", json={"transcript": VALID_TRANSCRIPT}).json()
    second_response = client.post("/analyze", json={"transcript": "He fixes the bug"}).json()
    assert set(first_response) == set(second_response)
    
def test_analyze_missing_transcript():
    response = client.post("/analyze", json={})
    assert response.status_code == 422  
    
def test_analyze_empty_transcript():
    response = client.post("/analyze", json={"transcript": "   "})
    assert response.status_code == 422
    
def test_analyze_only_spaces():
    response = client.post("/analyze", json={"transcript": "   "})
    assert response.status_code == 422
    
def test_analyze_too_long_transcript():
    response = client.post("/analyze", json={"transcript": "a" * 100_001})
    assert response.status_code == 422
    
def test_analyze_AI_failure(monkeypatch):
    # Make an AI function crash on purpose
    def broken_function(transcript):
        raise RuntimeError("AI is Down")
    monkeypatch.setattr(main_module, "generate_insights", broken_function)
    
    response = client.post("/analyze", json={"transcript": VALID_TRANSCRIPT})
    assert response.status_code == 502        