import json

from app.services.ai_provider import generate_insights


def test_sample_mode_returns_expected_schema(monkeypatch):
    monkeypatch.setenv("SAMPLE_MODE", "true")
    result = generate_insights("Decision: ship the demo\nAlice: Will prepare slides\nTODO: test upload")
    assert set(result) == {"status", "summary", "topics", "decisions", "action_items"}
    assert result["status"] == "completed"
    assert result["decisions"] == ["Decision: ship the demo"]
    assert isinstance(result["action_items"], list)


def test_sample_mode_does_not_need_api_key(monkeypatch):
    monkeypatch.setenv("SAMPLE_MODE", "true")
    monkeypatch.delenv("METERLESS_API_KEY", raising=False)
    monkeypatch.delenv("METERLESS_TOKEN_FILE", raising=False)
    assert generate_insights("Meeting started").get("status") == "completed"
