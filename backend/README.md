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
| ZETARIS_API_KEY | API key for Zetaris. If it is missing, Zetaris routes return `503` |
| ZETARIS_REST_URL | Zetaris REST URL, for example `http://localhost:8888/api/v1.0` |
| ZETARIS_ORG_ID | Optional. Organisation ID sent to Zetaris. Default: `1` |
| ZETARIS_TASKS_TABLE | Optional. Tasks table name. Default: `recallai_data.tasks` |

The Memory service (`hmem`) has its own variables. See `.env.example` for their names.

## Zetaris setup (local development)

Zetaris runs in the `zetaris-sandbox` GitHub Codespace. To reach it from your machine:

1. Start the codespace at https://github.com/codespaces.
2. In a separate terminal, keep this running:
   ```
   gh codespace ports forward 8888:8888
   ```
3. Set `ZETARIS_REST_URL=http://localhost:8888/api/v1.0` in `.env`.
4. Open http://127.0.0.1:8000/health/zetaris. It should return `{"status": "ok"}`.

The tasks table must have these columns: `id`, `title`, `owner`, `status`.

When you finish, stop the codespace to save quota.
Do not run `docker compose down -v`, because it deletes the tasks table data.

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
