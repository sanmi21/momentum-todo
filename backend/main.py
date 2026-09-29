from contextlib import asynccontextmanager
from datetime import date, datetime, timezone
from pathlib import Path
import sqlite3

from fastapi import FastAPI, HTTPException, Response, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

ROOT = Path(__file__).resolve().parents[1]
DB_PATH = Path(__file__).with_name("tasks.db")

def connection():
    db = sqlite3.connect(DB_PATH)
    db.row_factory = sqlite3.Row
    return db

def init_db():
    with connection() as db:
        db.execute("CREATE TABLE IF NOT EXISTS tasks (id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT NOT NULL, completed INTEGER NOT NULL DEFAULT 0, priority TEXT NOT NULL DEFAULT 'medium', due_date TEXT, created_at TEXT NOT NULL)")

@asynccontextmanager
async def lifespan(_: FastAPI):
    init_db()
    yield

app = FastAPI(title="Momentum Todo API", version="1.0.0", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"], allow_methods=["*"], allow_headers=["*"])

class TaskCreate(BaseModel):
    title: str = Field(min_length=1, max_length=120)
    priority: str = Field(default="medium", pattern="^(low|medium|high)$")
    due_date: date | None = None

class TaskUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=120)
    completed: bool | None = None
    priority: str | None = Field(default=None, pattern="^(low|medium|high)$")
    due_date: date | None = None

def serialize(row):
    return {"id": row["id"], "title": row["title"], "completed": bool(row["completed"]), "priority": row["priority"], "due_date": row["due_date"], "created_at": row["created_at"]}

@app.get("/api/health")
def health():
    return {"status": "ok"}

@app.get("/api/tasks")
def list_tasks():
    with connection() as db:
        rows = db.execute("SELECT * FROM tasks ORDER BY completed, id DESC").fetchall()
    return [serialize(row) for row in rows]

@app.post("/api/tasks", status_code=status.HTTP_201_CREATED)
def create_task(task: TaskCreate):
    title = task.title.strip()
    if not title:
        raise HTTPException(status_code=422, detail="Title cannot be blank")
    with connection() as db:
        cursor = db.execute("INSERT INTO tasks (title, priority, due_date, created_at) VALUES (?, ?, ?, ?)", (title, task.priority, task.due_date.isoformat() if task.due_date else None, datetime.now(timezone.utc).isoformat()))
        row = db.execute("SELECT * FROM tasks WHERE id = ?", (cursor.lastrowid,)).fetchone()
    return serialize(row)

@app.patch("/api/tasks/{task_id}")
def update_task(task_id: int, task: TaskUpdate):
    changes = task.model_dump(exclude_unset=True)
    if "title" in changes:
        changes["title"] = changes["title"].strip()
        if not changes["title"]: raise HTTPException(status_code=422, detail="Title cannot be blank")
    if "due_date" in changes and changes["due_date"]: changes["due_date"] = changes["due_date"].isoformat()
    if "completed" in changes: changes["completed"] = int(changes["completed"])
    with connection() as db:
        if not db.execute("SELECT id FROM tasks WHERE id = ?", (task_id,)).fetchone(): raise HTTPException(status_code=404, detail="Task not found")
        if changes:
            assignments = ", ".join(f"{field} = ?" for field in changes)
            db.execute(f"UPDATE tasks SET {assignments} WHERE id = ?", (*changes.values(), task_id))
        row = db.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()
    return serialize(row)

@app.delete("/api/tasks/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_task(task_id: int):
    with connection() as db:
        cursor = db.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
        if cursor.rowcount == 0: raise HTTPException(status_code=404, detail="Task not found")
    return Response(status_code=status.HTTP_204_NO_CONTENT)

if (ROOT / "dist").exists():
    app.mount("/", StaticFiles(directory=ROOT / "dist", html=True), name="frontend")
