from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from app.schemas import TranscriptRequest, InsightsResponse
from app.services.insights import generate_insights

app = FastAPI(title="RecallAI")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "https://recallai.vercel.app"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/analyze", response_model=InsightsResponse)
def analyze(req: TranscriptRequest):
    try:
        result = generate_insights(req.transcript)
    except Exception:
        raise HTTPException(
            status_code=502,
            detail="AI processing failed. Please try again.",
        )
    return result