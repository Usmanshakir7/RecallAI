import time

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from app.schemas import TranscriptRequest, InsightsResponse
from app.services import trace
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
    return result