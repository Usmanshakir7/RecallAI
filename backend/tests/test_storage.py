from fastapi.testclient import TestClient

from app.main import app
from app.services import storage

client = TestClient(app)


def test_analyze_saves_and_fetches(tmp_path, monkeypatch):
    monkeypatch.setattr(storage, "DATA_DIR", tmp_path / "meetings")
    r = client.post("/analyze", json={"transcript": "Alice will send the report by Friday."})
    assert r.status_code == 200
    meeting_id = r.json()["meeting_id"]
    assert meeting_id

    g = client.get(f"/meetings/{meeting_id}")
    assert g.status_code == 200
    assert g.json()["meeting_id"] == meeting_id


def test_meeting_not_found(tmp_path, monkeypatch):
    monkeypatch.setattr(storage, "DATA_DIR", tmp_path / "meetings")
    assert client.get("/meetings/deadbeef").status_code == 404
    assert client.get("/meetings/bad-id").status_code == 404
    
def test_list_meetings(tmp_path, monkeypatch):
    monkeypatch.setattr(storage, "DATA_DIR", tmp_path / "meetings")
    client.post("/analyze", json={"transcript": "Alice will send the report by Friday."})
    r = client.get("/meetings")
    assert r.status_code == 200
    assert len(r.json()) == 1
    assert "meeting_id" in r.json()[0]