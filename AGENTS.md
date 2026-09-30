# AGENTS.md

## Project overview

Momentum Todo is a small full-stack task manager built as an internship project.

- Frontend: React with Vite
- Backend: FastAPI
- ORM: SQLAlchemy 2.x
- Production database: Neon PostgreSQL
- Local database: SQLite fallback
- Deployment target: Vercel

Keep the project intentionally straightforward. Prefer clear, maintainable code over additional abstractions or features.

## Repository structure

```text
api/index.py              Vercel Python Function entry point
backend/main.py           FastAPI routes, SQLAlchemy model, and database setup
src/main.jsx              React application and API client
src/styles.css            Application styling and responsive layout
public/favicon.svg        Application favicon
requirements.txt          Production Python dependencies
backend/requirements.txt  Backend-local dependency list
vite.config.js            Vite configuration and local API proxy
```

## Development commands

Install frontend dependencies:

```bash
npm install
```

Start the frontend:

```bash
npm run dev
```

Create and activate a Python virtual environment, then install the backend:

```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS/Linux
source .venv/bin/activate

pip install -r requirements.txt
```

Start FastAPI:

```bash
uvicorn backend.main:app --reload
```

Build the frontend:

```bash
npm run build
```

Useful local URLs:

- Frontend: `http://localhost:5173`
- API: `http://127.0.0.1:8000/api`
- API documentation: `http://127.0.0.1:8000/api/docs`
- Health check: `http://127.0.0.1:8000/api/health`

## Database behavior

- Use the `DATABASE_URL` environment variable for Neon PostgreSQL.
- Never place credentials directly in source files.
- Never commit `.env`, `.env.local`, database passwords, or connection strings.
- When `DATABASE_URL` is absent, the backend must continue using the local SQLite fallback.
- Keep schema initialization idempotent because Vercel may start multiple function instances.
- Use SQLAlchemy sessions for all database operations; do not add raw `sqlite3` access.

## API contract

Preserve these routes unless a task explicitly requires an API change:

| Method | Route | Purpose |
| --- | --- | --- |
| `GET` | `/api/tasks` | List tasks |
| `POST` | `/api/tasks` | Create a task |
| `PATCH` | `/api/tasks/{task_id}` | Update a task |
| `DELETE` | `/api/tasks/{task_id}` | Delete a task |
| `GET` | `/api/health` | Report API and database status |

Task fields:

- `id`: integer
- `title`: required string, 1–120 characters
- `completed`: boolean
- `priority`: `low`, `medium`, or `high`
- `due_date`: nullable ISO date
- `created_at`: ISO datetime

Return `404` for missing tasks and `422` for invalid input.

## Frontend conventions

- Keep API requests relative to `/api`; frontend and backend share a domain on Vercel.
- Preserve the browser-storage fallback only as a demo mode when the API is unavailable.
- Treat PostgreSQL as the authoritative production data store.
- Maintain mobile and desktop layouts.
- Preserve keyboard accessibility, visible focus states, accessible labels, and reduced-motion support.
- Reuse the existing visual system instead of introducing an unrelated component framework.

## Vercel requirements

- Keep `api/index.py` and its module-level `app` export.
- Keep Python dependencies in the root `requirements.txt`.
- Keep the Vite build command as `npm run build` and output directory as `dist`.
- Do not add a separate production API origin unless explicitly required.
- Confirm Neon is connected to the appropriate Vercel environments and provides `DATABASE_URL`.

## Verification checklist

Before submitting a change:

1. Run `npm run build`.
2. Confirm the backend imports without errors.
3. Exercise create, list, update, and delete operations.
4. Check `/api/health`.
5. Confirm invalid titles are rejected.
6. Confirm a missing task returns `404`.
7. Check that no secrets or generated database files are staged.
8. If database code changed, verify both SQLite fallback and PostgreSQL URL handling.

## Scope discipline

This is an internship-scale todo application. Do not add authentication, teams, notifications, real-time synchronization, state-management libraries, or additional services unless explicitly requested. Keep changes small, documented, and easy to explain during a review.
