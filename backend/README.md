# RecallAI Backend

FastAPI backend that accepts a meeting transcript and returns meeting insights.

## Requirements

- Python 3.11 or 3.12

## Setup

Run these commands from the `backend` folder.

```
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

On macOS or Linux, use `source venv/bin/activate` instead of `venv\Scripts\activate`.

## Environment variables

Copy `.env.example` (in the project root) to `.env` and fill in the values.
Never commit the `.env` file.

| Variable | Description |
|----------|-------------|
| AI_API_KEY | API key for the AI provider |
| AI_MODEL | Model name to use |
| SAMPLE_MODE | Set to `true` to run with sample data |
| ZETARIS_REST_URL | Zetaris REST API base URL, e.g. `http://localhost:8888/api/v1.0` |
| ZETARIS_ORG_ID | Zetaris organisation ID (numeric) |
| ZETARIS_API_KEY | Zetaris API token. Keep it in `.env` only |
| HMEM_URL | H-MEM service address, e.g. `http://127.0.0.1:7171` |

## Optional services

### H-MEM (memory service)

Runs locally from `services/hmem` (Node.js). From the project root:

```
cd services\hmem
npm install
set HMEM_PORT=7171
npx tsx server.ts
```

Keep this window open and set `HMEM_URL=http://127.0.0.1:7171` in `.env`.

### Zetaris (data platform)

Zetaris runs in a GitHub Codespace, not on the laptop. Start the Codespace, run
`docker compose up -d` in the Zetaris platform folder, then forward the API port
to your laptop:

```
gh codespace ports forward 8888:8888
```

Set `ZETARIS_REST_URL=http://localhost:8888/api/v1.0`, `ZETARIS_ORG_ID` and
`ZETARIS_API_KEY` in `.env`. Stop the Codespace when you are done.

## Run the server

```
uvicorn app.main:app --reload
```

The server runs at http://127.0.0.1:8000.
API docs (Swagger) are at http://127.0.0.1:8000/docs.

## Endpoints

### GET /health

Response:

```json
{"status": "ok"}
```

### POST /analyze

Request:

```json
{"transcript": "text of the meeting"}
```

Response:

```json
{
  "status": "completed",
  "summary": "...",
  "topics": ["..."],
  "decisions": ["..."],
  "action_items": [{"task": "...", "owner": null}]
}
```

Errors:

- `422`: transcript is missing, empty, or longer than 100,000 characters.
- `502`: AI processing failed. The server keeps running.

## Run tests

```
pytest -v
```

## Notes

- `generate_insights` in `app/services/insights.py` is a placeholder.
  The AI/ML developer will replace it. The returned keys must not change.
- CORS allows the frontend at http://localhost:3000.