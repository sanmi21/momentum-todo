from contextlib import asynccontextmanager
from datetime import date, datetime, timezone
import os
from pathlib import Path
from typing import Generator

from fastapi import Depends, FastAPI, HTTPException, Response, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from sqlalchemy import Boolean, Date, DateTime, String, create_engine, select
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column
from sqlalchemy.pool import NullPool

ROOT = Path(__file__).resolve().parents[1]
LOCAL_DB_PATH = Path(__file__).with_name("tasks.db")


def database_url() -> str:
    """Return Neon in production and SQLite during local development."""
    url = os.getenv("DATABASE_URL")
    if not url:
        return f"sqlite:///{LOCAL_DB_PATH.as_posix()}"
    if url.startswith("postgres://"):
        return url.replace("postgres://", "postgresql+psycopg://", 1)
    if url.startswith("postgresql://"):
        return url.replace("postgresql://", "postgresql+psycopg://", 1)
    return url


DB_URL = database_url()
IS_SQLITE = DB_URL.startswith("sqlite")
engine = create_engine(
    DB_URL,
    connect_args={"check_same_thread": False} if IS_SQLITE else {},
    poolclass=None if IS_SQLITE else NullPool,
    pool_pre_ping=not IS_SQLITE,
)


class Base(DeclarativeBase):
    pass


class TaskRecord(Base):
    __tablename__ = "tasks"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(120), nullable=False)
    completed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    priority: Mapped[str] = mapped_column(String(10), nullable=False, default="medium")
    due_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc)
    )


def get_db() -> Generator[Session, None, None]:
    with Session(engine) as session:
        yield session


@asynccontextmanager
async def lifespan(_: FastAPI):
    Base.metadata.create_all(engine)
    yield


app = FastAPI(
    title="Momentum Todo API",
    version="2.0.0",
    lifespan=lifespan,
    docs_url="/api/docs",
    openapi_url="/api/openapi.json",
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class TaskCreate(BaseModel):
    title: str = Field(min_length=1, max_length=120)
    priority: str = Field(default="medium", pattern="^(low|medium|high)$")
    due_date: date | None = None


class TaskUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=120)
    completed: bool | None = None
    priority: str | None = Field(default=None, pattern="^(low|medium|high)$")
    due_date: date | None = None


def serialize(task: TaskRecord) -> dict:
    return {
        "id": task.id,
        "title": task.title,
        "completed": task.completed,
        "priority": task.priority,
        "due_date": task.due_date.isoformat() if task.due_date else None,
        "created_at": task.created_at.isoformat(),
    }


@app.get("/api/health")
def health():
    return {"status": "ok", "database": "sqlite" if IS_SQLITE else "postgresql"}


@app.get("/api/tasks")
def list_tasks(db: Session = Depends(get_db)):
    tasks = db.scalars(
        select(TaskRecord).order_by(TaskRecord.completed, TaskRecord.id.desc())
    ).all()
    return [serialize(task) for task in tasks]


@app.post("/api/tasks", status_code=status.HTTP_201_CREATED)
def create_task(task: TaskCreate, db: Session = Depends(get_db)):
    title = task.title.strip()
    if not title:
        raise HTTPException(status_code=422, detail="Title cannot be blank")
    record = TaskRecord(title=title, priority=task.priority, due_date=task.due_date)
    db.add(record)
    db.commit()
    db.refresh(record)
    return serialize(record)


@app.patch("/api/tasks/{task_id}")
def update_task(task_id: int, task: TaskUpdate, db: Session = Depends(get_db)):
    record = db.get(TaskRecord, task_id)
    if not record:
        raise HTTPException(status_code=404, detail="Task not found")

    changes = task.model_dump(exclude_unset=True)
    if "title" in changes:
        changes["title"] = changes["title"].strip()
        if not changes["title"]:
            raise HTTPException(status_code=422, detail="Title cannot be blank")
    for field, value in changes.items():
        setattr(record, field, value)
    db.commit()
    db.refresh(record)
    return serialize(record)


@app.delete("/api/tasks/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_task(task_id: int, db: Session = Depends(get_db)):
    record = db.get(TaskRecord, task_id)
    if not record:
        raise HTTPException(status_code=404, detail="Task not found")
    db.delete(record)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


if not os.getenv("VERCEL") and (ROOT / "dist").exists():
    app.mount("/", StaticFiles(directory=ROOT / "dist", html=True), name="frontend")
