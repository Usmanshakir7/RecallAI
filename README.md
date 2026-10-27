# 🧠 RecallAI

### Every Conversation. Every Insight. One Place.

RecallAI turns meeting transcripts into structured, searchable and actionable knowledge. It extracts a summary, topics, decisions and action items, remembers decisions across meetings, and checks the owners named in a meeting against the open tasks in a Zetaris table.

Built for the **Open Agent Hackathon 2026**.

## 🌟 Zetaris Demo Challenge: In one sentence, why did you think it was amazing?

Zetaris let us check a commitment made in a meeting against the real open tasks of that person with a single SQL call over REST, without copying or moving any data. <!-- EDIT: replace with your own sentence -->

## 🎯 The Problem

Important decisions and commitments get lost in long meetings, lectures and interviews. Re-reading a recording to find one deadline takes time, and it is hard to tell whether a topic was already decided in an earlier meeting.

## 💡 Our Solution

RecallAI reads a transcript and returns organized insights. Every decision is stored in a memory service so earlier meetings can be recalled later, and task owners can be compared with what is actually open in the tracker.

## ✨ Features

- **📝 Structured insights**: summary, topics, decisions and action items with owners, returned as a fixed JSON schema.
- **✅ Grounded extraction**: only explicit commitments become action items. Unknown owners stay empty instead of being guessed.
- **🧠 Decision memory**: decisions are stored in H-MEM and can be recalled by a text query across meetings.
- **📋 Task cross-check**: looks up the open tasks of any owner in a Zetaris table.
- **🛟 Works without a key**: a rule-based extractor produces insights when no AI key is set or the AI call fails.
- **🔒 Safe by design**: input validation, a 100,000 character limit, escaped SQL values, and clear 422, 502 and 503 errors.

## 🏗️ Architecture

```text
Streamlit UI  ──►  FastAPI backend  ──►  Gemini (insights, rule-based fallback)
                         │
                         ├──────────►  H-MEM memory service (Node.js, port 7171)
                         │
                         └──────────►  Zetaris REST SQL (forwarded port 8888)
```

H-MEM and Zetaris are optional services. If either is unavailable, `/analyze` still returns insights.

### How `POST /analyze` works

1. **Validate** the transcript. Empty text or more than 100,000 characters returns `422`.
2. **Extract with rules.** Finds decisions ("decided", "agreed", "will use"), commitments ("Alice: I will…", "Action:", "TODO:"), questions and short topic labels.
3. **Extract with Gemini** when `GEMINI_API_KEY` is set. Without a key, the rule-based result is returned.
4. **Clean the output.** Topics are limited to five short labels, copies of the transcript and duplicates are removed, and generic owners such as "we" or "someone" become `null`.
5. **Merge.** Gemini's result is used first and rule-based items fill any gaps.
6. **Remember.** Each decision is saved to H-MEM. This step never blocks the response.
7. **Respond** with the five-field result. If the AI step fails, the client receives `502`.

## 🔌 Sponsor Technology

| Technology | Role in RecallAI | Where |
|---|---|---|
| [**Zetaris**](https://www.zetaris.com) | Data layer. Queries the tasks table through its REST SQL API without copying data. | `backend/app/services/zetaris_client.py`, `tasks_service.py`, `POST /tasks/check` |
| [**H-MEM**](https://github.com/Meterless/Meterless) (Meterless) | Memory engine. Stores every decision and recalls related ones by query. | `services/hmem`, `hmem_client.py`, `GET /memory/recall` |

`services/hmem` is adapted from the Meterless H-MEM reference implementation (Apache-2.0). `server.ts` is our own HTTP wrapper around the engine. Memories are saved to disk and survive a restart.

## 🛠️ Technology Stack

[![Python](https://img.shields.io/badge/PYTHON-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org) [![TypeScript](https://img.shields.io/badge/TYPESCRIPT-3178C6?style=for-the-badge&logo=typescript&logoColor=white)](https://www.typescriptlang.org)

[![FastAPI](https://img.shields.io/badge/FASTAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com) [![Streamlit](https://img.shields.io/badge/STREAMLIT-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white)](https://streamlit.io) [![Node.js](https://img.shields.io/badge/NODE.JS-339933?style=for-the-badge&logo=nodedotjs&logoColor=white)](https://nodejs.org)

[![Gemini](https://img.shields.io/badge/GEMINI-8E75B2?style=for-the-badge&logo=googlegemini&logoColor=white)](https://ai.google.dev) [![Zetaris](https://img.shields.io/badge/ZETARIS-0B6B63?style=for-the-badge)](https://www.zetaris.com) [![H-MEM](https://img.shields.io/badge/H--MEM-1F2937?style=for-the-badge)](https://github.com/Meterless/Meterless)

[![pytest](https://img.shields.io/badge/PYTEST-0A9EDC?style=for-the-badge&logo=pytest&logoColor=white)](https://pytest.org) [![Git](https://img.shields.io/badge/GIT-F05032?style=for-the-badge&logo=git&logoColor=white)](https://git-scm.com) [![GitHub](https://img.shields.io/badge/GITHUB-181717?style=for-the-badge&logo=github&logoColor=white)](https://github.com)

## 📂 Project Structure

```text
RecallAI/
├── frontend/
│   └── app.py                      Streamlit interface
├── backend/
│   ├── app/
│   │   ├── main.py                 routes, CORS, error handling
│   │   ├── schemas.py              request and response models
│   │   └── services/
│   │       ├── insights.py         Gemini + rule-based extraction
│   │       ├── verifier.py         transcript grounding check
│   │       ├── prompts.py          extraction prompt
│   │       ├── hmem_client.py      H-MEM HTTP client
│   │       ├── zetaris_client.py   Zetaris REST SQL client
│   │       └── tasks_service.py    open-task query
│   ├── tests/                      33 tests
│   └── requirements.txt
├── services/
│   └── hmem/                       H-MEM memory service
├── .env.example
└── README.md
```

## 🚀 Getting Started

### Prerequisites

- Python 3.11 or 3.12
- Git
- [Node.js](https://nodejs.org) (only for the H-MEM memory service)

### 1. Clone the repository

```bash
git clone https://github.com/Usmanshakir7/RecallAI.git
cd RecallAI
```

### 2. Start the backend

```bash
cd backend
python -m venv venv
venv\Scripts\activate          # macOS/Linux: source venv/bin/activate
pip install -r requirements.txt google-genai
uvicorn app.main:app --reload
```

Open `http://127.0.0.1:8000/health`. The response is `{"status":"ok"}`. Interactive API docs are at `http://127.0.0.1:8000/docs`.

### 3. Start the frontend

In a second terminal, from the project root:

```bash
pip install streamlit requests
streamlit run frontend/app.py
```

### 4. Start H-MEM (optional)

```bash
cd services/hmem
npm install
set HMEM_PORT=7171             # macOS/Linux: export HMEM_PORT=7171
npx tsx server.ts
```

Set `HMEM_URL=http://127.0.0.1:7171` in `.env` and restart the backend.

### 5. Connect Zetaris (optional)

Zetaris runs in a GitHub Codespace. Start it, run `docker compose up -d` in the Zetaris folder, then forward the API port:

```bash
gh codespace ports forward 8888:8888
```

Set `ZETARIS_REST_URL`, `ZETARIS_ORG_ID` and `ZETARIS_API_KEY` in `.env`, then check `/health/zetaris`.

> **Quick demo:** run steps 2 and 3 with no keys. `/analyze` works through the rule-based extractor, and the health endpoints report `not_configured`.

## ⚙️ Configuration

Copy `.env.example` to `.env` and fill in the values. `.env` is ignored by git.

| Variable | Meaning |
|---|---|
| `GEMINI_API_KEY` | Gemini API key. Without it the rule-based extractor is used. |
| `AI_MODEL` | Gemini model name. Default `gemini-3.5-flash-lite`. |
| `HMEM_URL` | Memory service address, for example `http://127.0.0.1:7171`. |
| `HMEM_PORT`, `HMEM_DIR` | Memory service port (7171) and data folder (`./data`). |
| `ZETARIS_REST_URL` | Zetaris REST base URL. Default `http://localhost:8888/api/v1.0`. |
| `ZETARIS_ORG_ID` | Numeric Zetaris organisation id. Default `1`. |
| `ZETARIS_API_KEY` | Zetaris API token. |
| `ZETARIS_TASKS_TABLE` | Tasks table. Default `recallai_data.tasks`. |

## 📡 API Reference

| Method | Endpoint | Purpose | Errors |
|---|---|---|---|
| GET | `/health` | Backend availability | none |
| GET | `/health/zetaris` | `ok`, `not_configured`, `unreachable` or `unexpected_result` | none |
| GET | `/health/hmem` | `ok`, `not_configured`, `unreachable` or `unexpected_result` | none |
| POST | `/analyze` | Transcript in, structured insights out. Saves decisions to H-MEM | 422, 502 |
| GET | `/memory/recall?q=…` | Up to three earlier decisions related to `q` | 503, 502 |
| POST | `/tasks/check` | Open tasks for the given owners | 422, 502, 503 |

### Analyze a transcript

```bash
curl -X POST http://127.0.0.1:8000/analyze \
  -H "Content-Type: application/json" \
  -d '{"transcript":"Alice: I will test the API.\nWe decided to use FastAPI."}'
```

```json
{
  "status": "completed",
  "summary": "Alice: I will test the API. We decided to use FastAPI.",
  "topics": ["Alice: I will test the API"],
  "decisions": ["We decided to use FastAPI"],
  "action_items": [{"task": "I will test the API", "owner": "Alice"}]
}
```

### Check open tasks

```json
POST /tasks/check
{"owners": ["John Doe"]}

{
  "owners_checked": ["John Doe"],
  "open_tasks": [
    {"id": "T-101", "title": "Fix login bug", "owner": "John Doe", "status": "In Progress"}
  ]
}
```

### Recall earlier decisions

```json
GET /memory/recall?q=analytics

{
  "query": "analytics",
  "memories": [{"id": "...", "content": "Use Zetaris", "source": "meeting-transcript"}]
}
```

## 🧪 Testing

```bash
cd backend
pytest -v
```

The suite has 33 tests covering the analyze endpoint, extraction rules, the prompt, the verifier, H-MEM and Zetaris health checks, memory recall, saving decisions and the task query, including service-down cases and SQL quote escaping. Tests never contact real services.

## 🗺️ Roadmap

- **Recording intake:** audio and video upload, FFmpeg, faster-whisper transcription with timestamps, speaker separation with WhisperX.
- **Search and Q&A:** speaker-turn chunks, keyword plus vector search, answers that cite timestamps, semantic embeddings for H-MEM recall.
- **Trust and review:** verifier confidence in the UI, human approve/edit/reject before task updates, deadlines and supporting quotes per action item.
- **Product:** PDF export, accounts and per-user access, persistent storage, an evaluation set of labeled transcripts.

## 🔐 Security

- Never commit API keys, passwords or tokens.
- Keep secrets in `.env` and commit only `.env.example` with placeholders.
- Avoid confidential meeting data in public demonstrations.

## 👥 Team

| Member | Role |
|---|---|
| **Ch. Muhammad Usman Shakir** | Team Lead, AI/ML |
| **Azizullah Asad** | Backend |
| **Palwasha Sajjad** | Frontend |
| **Muhammad Anis** | Mentor, issue support |

## 🤝 Contribution Workflow

1. Pull the latest changes from `main`.
2. Create a feature branch for your task.
3. Implement and test your changes.
4. Commit and push your branch.
5. Open a pull request for review.

---

**RecallAI: Every Conversation. Every Insight. One Place.**
