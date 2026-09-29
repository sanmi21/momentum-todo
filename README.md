# Momentum Todo

A full-stack todo application built with React, Vite, FastAPI, and SQLite. It supports creating, editing, completing, searching, filtering, prioritizing, dating, and deleting tasks.

## Run locally

### 1. Start the FastAPI backend

```bash
cd backend
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload
```

The API runs at `http://127.0.0.1:8000`; interactive docs are at `http://127.0.0.1:8000/docs`.

### 2. Start the React frontend

In another terminal:

```bash
npm install
npm run dev
```

Open `http://localhost:5173`.

## Production-style local run

```bash
npm run build
cd backend
uvicorn main:app
```

Then open `http://127.0.0.1:8000`.

## API

| Method | Endpoint | Purpose |
| --- | --- | --- |
| GET | `/api/tasks` | List tasks |
| POST | `/api/tasks` | Create a task |
| PATCH | `/api/tasks/{id}` | Update a task |
| DELETE | `/api/tasks/{id}` | Delete a task |
| GET | `/api/health` | Health check |

The deployed frontend uses browser storage when a FastAPI server is not available, so the live demo remains fully interactive.
