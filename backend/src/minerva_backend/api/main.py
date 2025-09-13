import os
from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from minerva_backend.graph.db import init_db
from minerva_backend.utils.diary import parse_diary_entry


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    init_db()
    print("✅ Backend started and DB initialized.")

    yield
    # Clean up


backend_app = FastAPI(title="Minerva Backend", version="0.1.0", lifespan=lifespan)

# TODO: Define your vault root (configure via env later)
VAULT_ROOT = Path("D:\\yo")


# TODO: move to some kind of req/resp models folder?
class JournalSubmission(BaseModel):
    filepath: str
    date: str


@backend_app.get("/health")
async def healthcheck():
    await submit_journal(JournalSubmission(filepath="02 - Daily Notes/2025-09-01.md", date="2025-09-01"))
    return {"status": "ok"}


@backend_app.post("/submit")
async def submit_journal(data: JournalSubmission):
    # Build absolute path
    journal_path = (VAULT_ROOT / data.filepath)

    # Check it's inside vault
    if not str(journal_path).startswith(str(VAULT_ROOT)):
        raise HTTPException(status_code=400, detail="Invalid file path")

    # Check file exists
    if not journal_path.exists():
        raise HTTPException(status_code=404, detail="File not found")

    # Read file content
    content = journal_path.read_text(encoding="utf-8")

    # Parse free text + structured fields
    diary_entry = parse_diary_entry(content, data.date)

    # 2. Queue processing job (LLM entity extraction)
    # 3. Return job_id
    return {"job_id": "12345"}
