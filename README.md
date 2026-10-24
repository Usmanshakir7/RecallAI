# RecallAI
Multimodal meeting and video intelligence platform with timestamped transcripts, AI summaries, evidence-based Q&amp;A, and PDF export.


**Every conversation. Every insight. One place.**

RecallAI is a multimodal meeting and video intelligence platform that transforms recorded meetings, lectures, interviews, and videos into searchable knowledge.

## Core Features

- Upload audio and video recordings.
- Generate timestamped transcripts.
- Create AI summaries, key points, decisions, and action items.
- Ask questions and receive answers grounded in transcript evidence.
- Export transcripts and insights as PDF reports.

## Technology Stack

- **Frontend:** Next.js, React, TypeScript, Tailwind CSS
- **Backend:** Python, FastAPI
- **Database:** PostgreSQL
- **Media processing:** FFmpeg
- **Speech-to-text:** faster-whisper or a replaceable speech API
- **Testing:** pytest

## Project Structure

- `frontend/` — user interface
- `backend/app/` — backend application
- `backend/tests/` — backend tests
- `docs/` — project documentation

## Development Status

Initial repository setup is complete. Application development is starting.

## Team Contribution Workflow

1. Pull the latest changes from `main`.
2. Create a branch for your task.
3. Make and test your changes.
4. Commit and push your branch.
5. Open a pull request for review before merging into `main`.

## Security

Never commit API keys, passwords, or real environment files. Use environment variables and keep secrets on the server.
