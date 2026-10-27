
import time
import requests
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from app.schemas import TranscriptRequest, InsightsResponse
from app.services import hmem_client, storage, trace, zetaris_client
from app.services.insights import generate_insights

app = FastAPI(title="RecallAI")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/health/zetaris")
def health_zetaris():
    if not zetaris_client.is_configured():
        return {"status": "not_configured"}
    try:
        return {
            "status": "ok" if zetaris_client.ping() else "unexpected_result"
        }
    except (zetaris_client.ZetarisError, requests.RequestException):
        return {"status": "unreachable"}


@app.get("/health/hmem")
def health_hmem():
    if not hmem_client.is_configured():
        return {"status": "not_configured"}
    try:
        return {
            "status": "ok" if hmem_client.ping() else "unexpected_result"
        }
    except requests.RequestException:
        return {"status": "unreachable"}


@app.get("/trace")
def get_trace():
    return trace.get_all()


@app.post("/analyze", response_model=InsightsResponse)
def analyze(req: TranscriptRequest):
    start = time.perf_counter()
    model = trace.current_model()

    try:
        result = generate_insights(req.transcript)
    except Exception as e:
        ms = int((time.perf_counter() - start) * 1000)
        trace.record("insights", model, "error", ms, type(e).__name__)
        raise HTTPException(
            status_code=502,
            detail="AI processing failed. Please try again.",
        )

    ms = int((time.perf_counter() - start) * 1000)
    trace.record("insights", model, "ok", ms)

    meeting_id = storage.new_id()
    result = {**result, "meeting_id": meeting_id}

    try:
        storage.save(meeting_id, result)
    except OSError:
        pass

    hmem_client.remember_decisions(
        result.get("decisions", []),
        "meeting-transcript",
    )

    return result


@app.get("/memory/recall")
def memory_recall(q: str):
    """Return earlier decisions related to the question q."""
    if not hmem_client.is_configured():
        raise HTTPException(
            status_code=503,
            detail="Memory service is not configured.",
        )
    try:
        return {"query": q, "memories": hmem_client.recall(q)}
    except requests.RequestException:
        raise HTTPException(
            status_code=502,
            detail="Memory service is unreachable.",
        )


@app.get("/meetings")
def list_meetings():
    return storage.list_all()


@app.get("/meetings/{meeting_id}")
def get_meeting(meeting_id: str):
    record = storage.load(meeting_id)
    if record is None:
        raise HTTPException(status_code=404, detail="Meeting not found.")
    return record["result"]
