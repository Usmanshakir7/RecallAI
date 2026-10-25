from dotenv import load_dotenv

load_dotenv()

import requests
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from app.schemas import TranscriptRequest, InsightsResponse
from app.services import hmem_client, zetaris_client
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
        return {"status": "ok" if zetaris_client.ping() else "unexpected_result"}
    except zetaris_client.ZetarisError:
        return {"status": "unreachable"}


@app.get("/health/hmem")
def health_hmem():
    if not hmem_client.is_configured():
        return {"status": "not_configured"}
    try:
        return {"status": "ok" if hmem_client.ping() else "unexpected_result"}
    except requests.RequestException:
        return {"status": "unreachable"}


@app.post("/analyze", response_model=InsightsResponse)
def analyze(req: TranscriptRequest):
    try:
        result = generate_insights(req.transcript)
    except Exception:
        raise HTTPException(
            status_code=502,
            detail="AI processing failed. Please try again.",
        )
    # Save the decisions to memory. This is best effort and never breaks the response.
    hmem_client.remember_decisions(result.get("decisions", []), "meeting-transcript")
    return result


@app.get("/memory/recall")
def memory_recall(q: str):
    """Return earlier decisions related to the question q."""
    if not hmem_client.is_configured():
        raise HTTPException(status_code=503, detail="Memory service is not configured.")
    try:
        return {"query": q, "memories": hmem_client.recall(q)}
    except requests.RequestException:
        raise HTTPException(status_code=502, detail="Memory service is unreachable.")