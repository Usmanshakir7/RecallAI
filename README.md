# 🧠 RecallAI
### Every Conversation. Every Insight. One Place.

RecallAI is an AI-powered meeting and video intelligence platform designed to transform conversations into structured, searchable, and actionable knowledge.

From meetings and lectures to interviews and recorded discussions, RecallAI helps users capture important information, understand key insights, and keep track of decisions without manually reviewing lengthy recordings.

## ✨ Key Features

- **🎙️ Audio & Video Intelligence** — Designed to support meeting, lecture, interview, and video recordings.
- **📝 AI-Powered Summaries** — Turn lengthy transcripts into concise, meaningful summaries.
- **📌 Key Topics & Important Points** — Identify the main ideas and essential information from conversations.
- **✅ Decisions & Action Items** — Organize important decisions, tasks, and follow-up actions.
- **🔎 Evidence-Based Q&A** — Ask questions and receive answers grounded in transcript evidence.
- **⏱️ Timestamped Transcripts** — Navigate conversation content using timestamps.
- **📄 PDF Export** — Export transcripts and insights into shareable reports.

## 🎯 The Problem

Important details often get lost in long meetings, lectures, interviews, and recorded discussions. Manually reviewing recordings takes time, and finding a specific decision or action item can be difficult.

## 💡 Our Solution

RecallAI transforms conversations into organized information by combining transcription, AI-generated insights, and searchable knowledge workflows.

Our goal is to help users spend less time reviewing recordings and more time acting on the information that matters.

## 🛠️ Technology Stack

| Component | Technology |
|---|---|
| Frontend | Python, Streamlit |
| Backend API | Python, FastAPI |
| AI Processing | AI-powered transcript analysis |
| Media Processing | FFmpeg (planned integration) |
| Speech-to-Text | faster-whisper or compatible speech API (planned integration) |
| Testing | pytest |
| Version Control | Git & GitHub |

*Note: Technologies and integrations may evolve as development progresses.*

## 📂 Project Structure

```text
RecallAI/
├── frontend/
│   └── app.py
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── schemas.py
│   │   └── services/
│   │       └── insights.py
│   ├── tests/
│   ├── requirements.txt
│   └── README.md
├── docs/
└── README.md
```

## 🚀 Getting Started

### Prerequisites

- Python 3.10 or a compatible version
- Git
- pip

### 1. Clone the Repository

```bash
git clone https://github.com/Usmanshakir7/RecallAI.git
cd RecallAI
```

### 2. Install Backend Dependencies

```bash
python -m pip install -r backend/requirements.txt
```

### 3. Start the Backend

```bash
python -m uvicorn app.main:app --reload --app-dir backend
```

The API will be available at:

- API: `http://127.0.0.1:8000`
- Health Check: `http://127.0.0.1:8000/health`
- API Documentation: `http://127.0.0.1:8000/docs`

### 4. Install Frontend Dependencies

```bash
python -m pip install streamlit requests
```

### 5. Run the Frontend

Open a second terminal in the project root and run:

```bash
streamlit run frontend/app.py
```

The Streamlit interface will open in your browser.

## 🔌 API Overview

The backend exposes the following endpoints:

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/health` | Check backend availability |
| POST | `/analyze` | Analyze a submitted transcript and return insights |

The transcript analysis endpoint accepts a transcript and returns structured insights according to the backend response schema.

For the exact request and response formats, visit `/docs` while the backend is running.

## 👥 Team Contributions

RecallAI is developed collaboratively, with team members contributing to AI processing, backend development, frontend implementation, testing, and documentation.

We use Git branches and pull requests to keep development organized and review changes before merging them into the main branch.

### Contribution Workflow

1. Pull the latest changes from `main`.
2. Create a feature branch for your task.
3. Implement and test your changes.
4. Commit and push your branch.
5. Open a pull request for review.

## 🔐 Security

- Never commit API keys, passwords, or secrets.
- Store sensitive configuration in environment variables.
- Keep `.env` files out of version control.
- Avoid using confidential meeting recordings or personal information in public demonstrations.

*Roadmap items should be updated as features are implemented and verified.*

## 🌟 Our Vision

We envision a future where every conversation can become useful knowledge — easy to understand, easy to search, and easy to act upon.

**RecallAI — Remember the conversation. Act on the insights.**

---

Developed with ❤️ by the RecallAI team.
