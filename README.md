# Momentum Todo

A full-stack todo application built with React, Vite, FastAPI, SQLAlchemy, and PostgreSQL. It supports creating, editing, completing, searching, filtering, prioritizing, dating, and deleting tasks.

## Architecture

- `src/` — React frontend
- `backend/main.py` — FastAPI API and SQLAlchemy models
- `api/index.py` — Vercel Python Function entry point
- Neon PostgreSQL — production persistence through `DATABASE_URL`
- SQLite — automatic local-development fallback

## Run locally

### 1. Start the FastAPI backend

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
uvicorn backend.main:app --reload
```

Without `DATABASE_URL`, the API automatically creates `backend/tasks.db`. The API runs at `http://127.0.0.1:8000`, with interactive docs at `http://127.0.0.1:8000/docs`.

### 2. Start the React frontend

In another terminal:

```bash
npm install
npm run dev
```

Open `http://localhost:5173`. Vite proxies `/api` requests to FastAPI.

## Deploy to Vercel with Neon

1. Push this project to GitHub and import it into Vercel.
2. Use the **Vite** preset, build command `npm run build`, and output directory `dist`.
3. In the Vercel project, open **Storage**, select **Create Database**, and install **Neon**.
4. Connect Neon to the **Production**, **Preview**, and **Development** environments.
5. Confirm `DATABASE_URL` exists under **Settings → Environment Variables**.
6. Redeploy. Vercel serves the Vite build and packages `api/index.py` as FastAPI.
7. Verify `/api/health` reports `"database": "postgresql"`, open `/api/docs`, then create a task and refresh to confirm persistence.

To use Neon locally, copy `.env.example` to `.env`, insert your development connection string, and load it into your shell before starting Uvicorn. Never commit `.env`.

## API

| Method | Endpoint | Purpose |
| --- | --- | --- |
| GET | `/api/tasks` | List tasks |
| POST | `/api/tasks` | Create a task |
| PATCH | `/api/tasks/{id}` | Update a task |
| DELETE | `/api/tasks/{id}` | Delete a task |
| GET | `/api/health` | Health and database check |

On Vercel, the frontend and API share one domain, so the browser calls `/api/*` without a separate API URL or production CORS configuration.
