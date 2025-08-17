# apps/api/agent_ceo.py
from datetime import datetime
from typing import List, Optional
import os
import base64
import httpx

from pydantic import BaseModel
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import SQLModel, Field, Session, select

from app import get_db, current_user, AuthedUser

router = APIRouter(prefix="/agent", tags=["Agentic CEO"])

# DB Model (mirrors app.py Idea but kept here for clarity if imported alone)
class Idea(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    title: str
    description: str
    created_by: str
    status: str = "proposed"
    branch_name: Optional[str] = None
    pr_number: Optional[int] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

class IdeaIn(BaseModel):
    title: str
    description: str

class ExecFile(BaseModel):
    path: str
    content: str

class ExecRequest(BaseModel):
    idea_id: int
    files: List[ExecFile] = []
    message: str = ""

OWNER = os.getenv("GITHUB_OWNER")
REPO = os.getenv("GITHUB_REPO")
TOKEN = os.getenv("GITHUB_TOKEN")
G_API = "https://api.github.com"

def _headers():
    if not TOKEN:
        raise HTTPException(500, "GITHUB_TOKEN not configured")
    return {"Authorization": f"Bearer {TOKEN}", "Accept": "application/vnd.github+json"}

async def _get(url):
    async with httpx.AsyncClient(timeout=30) as c:
        r = await c.get(url, headers=_headers())
        r.raise_for_status()
        return r.json()

async def _post(url, data):
    async with httpx.AsyncClient(timeout=60) as c:
        r = await c.post(url, headers=_headers(), json=data)
        r.raise_for_status()
        return r.json()

async def _put(url, data):
    async with httpx.AsyncClient(timeout=60) as c:
        r = await c.put(url, headers=_headers(), json=data)
        r.raise_for_status()
        return r.json()

@router.post("/propose")
async def propose_idea(data: IdeaIn, au: AuthedUser = Depends(current_user), db: Session = Depends(get_db)):
    # Admin or CEO can propose
    idea = Idea(title=data.title, description=data.description, created_by=au.email, status="proposed")
    db.add(idea)
    db.commit()
    db.refresh(idea)
    return {"ok": True, "idea": idea}

@router.get("/list")
async def list_ideas(_: AuthedUser = Depends(current_user), db: Session = Depends(get_db)):
    return db.exec(select(Idea).order_by(Idea.created_at.desc())).all()

@router.post("/approve/{idea_id}")
async def approve_idea(idea_id: int, au: AuthedUser = Depends(current_user), db: Session = Depends(get_db)):
    if au.role != "admin":
        raise HTTPException(403, "Only admin can approve")
    idea = db.get(Idea, idea_id)
    if not idea:
        raise HTTPException(404, "Idea not found")
    idea.status = "approved"
    db.add(idea)
    db.commit()
    return {"ok": True, "idea": idea}

@router.post("/execute")
async def execute_idea(req: ExecRequest, au: AuthedUser = Depends(current_user), db: Session = Depends(get_db)):
    # CEO can execute only after admin approval
    idea = db.get(Idea, req.idea_id)
    if not idea:
        raise HTTPException(404, "Idea not found")
    if idea.status != "approved":
        raise HTTPException(400, "Idea must be approved by Admin before execution")
    if not OWNER or not REPO:
        raise HTTPException(500, "GITHUB_OWNER/REPO not configured")

    # Get default branch and base sha
    repo = await _get(f"{G_API}/repos/{OWNER}/{REPO}")
    default_branch = repo.get("default_branch", "main")
    ref = await _get(f"{G_API}/repos/{OWNER}/{REPO}/git/ref/heads/{default_branch}")
    base_sha = ref["object"]["sha"]

    # Create a unique branch
    import secrets
    branch = f"agent/{idea.id}-{secrets.token_hex(3)}"
    await _post(f"{G_API}/repos/{OWNER}/{REPO}/git/refs", {"ref": f"refs/heads/{branch}", "sha": base_sha})

    # Commit files (create or update)
    for f in req.files:
        b64 = base64.b64encode(f.content.encode()).decode()
        url = f"{G_API}/repos/{OWNER}/{REPO}/contents/{f.path}"
        msg = req.message or f"Agentic CEO: implement {idea.title}"
        try:
            # Check if file exists to include its sha
            existing = await _get(url + f"?ref={branch}")
            file_sha = existing.get("sha")
            await _put(url, {"message": msg, "content": b64, "branch": branch, "sha": file_sha})
        except Exception:
            # New file
            await _put(url, {"message": msg, "content": b64, "branch": branch})

    # Open PR
    pr = await _post(f"{G_API}/repos/{OWNER}/{REPO}/pulls", {
        "title": f"Agentic CEO: {idea.title}",
        "head": branch,
        "base": default_branch,
        "body": f"Automated change for idea #{idea.id}.\n\n{idea.description}\n\n**Admin approval required before merge.**"
    })

    idea.status = "executing"
    idea.branch_name = branch
    idea.pr_number = pr.get("number")
    db.add(idea); db.commit(); db.refresh(idea)
    return {"ok": True, "idea": idea, "pr_url": pr.get("html_url")}
