from fastapi.testclient import TestClient
from app.services.insights import remove_duplicates
import app.main as main_module
from app.main import app

client = TestClient(app)

EXPECTED_KEYS = {"status", "summary", "topics", "decisions", "action_items"}
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


    
def test_analyze_extracts_decisions():
    response = client.post(
        "/analyze",
        json={"transcript": "We decided to use FastAPI for the backend."},
    )

    assert response.status_code == 200
    data = response.json()
    assert any("decided" in item.lower() for item in data["decisions"])


def test_analyze_extracts_action_items():
    response = client.post(
        "/analyze",
        json={"transcript": "I will finish the API tests by Friday."},
    )

    assert response.status_code == 200
    data = response.json()
    assert len(data["action_items"]) >= 1
    assert any(
        "finish the API tests" in item["task"]
        for item in data["action_items"]
    )


def test_analyze_extracts_topics():
    response = client.post(
        "/analyze",
        json={
            "transcript": (
                "The team discussed backend development. "
                "We decided to use FastAPI for the backend."
            )
        },
    )

    assert response.status_code == 200
    assert len(response.json()["topics"]) >= 1
def test_remove_duplicates_preserves_order():
    items = [
        "We decided to use FastAPI.",
        "Sara will test the API.",
        "we decided to use fastapi.",
    ]

    result = remove_duplicates(items)

    assert result == [
        "We decided to use FastAPI.",
        "Sara will test the API.",
    ]

    
def test_analyze_extracts_action_owner():
    response = client.post(
        "/analyze",
        json={"transcript": "Sara: I will test the API."},
    )

    assert response.status_code == 200
    action_items = response.json()["action_items"]

    assert any(
        item["owner"] == "Sara"
        and "I will test the API" in item["task"]
        for item in action_items
    )

def test_action_without_named_owner():
    response = client.post(
        "/analyze",
        json={"transcript": "We will review the design."},
    )

    assert response.status_code == 200
    action_items = response.json()["action_items"]

    assert any(
        item["owner"] is None
        and "We will review the design" in item["task"]
        for item in action_items
    )
