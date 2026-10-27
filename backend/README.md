# RecallAI Backend

FastAPI backend that accepts a meeting transcript and returns meeting insights.
It can also look up open tasks for given owners in a Zetaris table.

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

Copy `.env.example` (in the project root) to `backend/.env` and fill in the values.
The `.env` file must be in the `backend` folder, because the server is started from there.
Never commit the `.env` file.
Restart the server after changing `.env`, because `--reload` does not watch it.

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

### GET /health/zetaris

Checks that Zetaris answers a simple query.

Response:

```json
{"status": "ok"}
```

Other values of `status`: `not_configured` (no `ZETARIS_API_KEY`) and `unexpected_result`.

### GET /health/hmem

Checks the Memory service. Returns `{"status": "not_configured"}` if it is not set up.

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

### GET /memory/recall

Reads from the Memory service.

Errors:

- `503`: Memory service is not configured.

### POST /tasks/check

Returns the open (not done) tasks for the given owners from the Zetaris tasks table.
Owner names are matched without regard to upper or lower case.

Request:

```json
{"owners": ["John Doe"]}
```

Response:

```json
{
  "owners_checked": ["John Doe"],
  "open_tasks": [
    {"id": "T-101", "title": "Fix login bug", "owner": "John Doe", "status": "In Progress"},
    {"id": "T-105", "title": "Write API documentation", "owner": "John Doe", "status": "Not Started"}
  ]
}
```

Errors:

- `422`: the request body is invalid.
- `502`: Zetaris is unreachable or returned an error (for example, a wrong column name).
- `503`: Zetaris is not configured (`ZETARIS_API_KEY` is missing).

## Run tests

```
pytest -v
```

## Troubleshooting

- `503 Zetaris is not configured`: `ZETARIS_API_KEY` was not loaded. Check that `backend/.env`
  is not empty, then restart the server.
- `502 Zetaris is unreachable`: the codespace is stopped, the port forward is not running,
  or the query failed. To see the real error, run in the `backend` folder:
  `python -c "from dotenv import load_dotenv; load_dotenv(); from app.services import tasks_service as t; print(t.get_open_tasks(['John Doe']))"`

## Notes

- `generate_insights` in `app/services/insights.py` is a placeholder.
  The AI/ML developer will replace it. The returned keys must not change.
- CORS allows the frontend at http://localhost:3000.
