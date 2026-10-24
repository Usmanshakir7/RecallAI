from fastapi import FastAPI

app = FastAPI(title="RecallAI")


@app.get("/health")
def health():
    return {"status": "ok"}

