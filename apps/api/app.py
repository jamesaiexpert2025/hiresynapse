# apps/api/app.py
from datetime import datetime, timedelta
from typing import Optional, Literal, List
import os

from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import jwt, JWTError
from pydantic import BaseModel
from sqlmodel import SQLModel, Field, Session, select, create_engine

# Config
APP_NAME = "HireSynapse API (Agentic CEO)"
AUTH_SECRET = os.getenv("AUTH_SECRET", "dev-secret-change")
ALGO = "HS256"
TOKEN_EXPIRE_MIN = 60 * 8

DB_URL = os.getenv("DATABASE_URL", "sqlite:///./hiresynapse.db")
engine = create_engine(DB_URL, connect_args={"check_same_thread": False} if DB_URL.startswith("sqlite") else {}, pool_pre_ping=True)

# Models
class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    email: str = Field(index=True, unique=True)
    password: str  # NOTE: demo only; use hashed passwords in production
    role: Literal["admin", "ceo", "viewer"] = "viewer"

class Idea(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    title: str
    description: str
    created_by: str
    status: str = "proposed"  # proposed -> approved -> executing -> done / rejected
    branch_name: Optional[str] = None
    pr_number: Optional[int] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

# Schemas
class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"

class IdeaIn(BaseModel):
    title: str
    description: str

# Auth tools
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token")

def get_db():
    with Session(engine) as s:
        yield s

def create_token(u: User):
    payload = {"sub": u.email, "uid": u.id, "role": u.role, "exp": datetime.utcnow() + timedelta(minutes=TOKEN_EXPIRE_MIN)}
    return jwt.encode(payload, AUTH_SECRET, algorithm=ALGO)

class AuthedUser(BaseModel):
    id: int
    email: str
    role: str

def current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> AuthedUser:
    try:
        data = jwt.decode(token, AUTH_SECRET, algorithms=[ALGO])
        email = data.get("sub")
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    user = db.exec(select(User).where(User.email == email)).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    return AuthedUser(id=user.id, email=user.email, role=user.role)

# App
app = FastAPI(title=APP_NAME)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def on_startup():
    SQLModel.metadata.create_all(engine)
    with Session(engine) as db:
        # seed master admin and AI CEO from env
        admin_email = os.getenv("ADMIN_EMAIL", "admin@hiresynapse.ai")
        admin_pwd = os.getenv("ADMIN_PASSWORD", "admin123")
        ceo_email = os.getenv("AI_CEO_EMAIL", "ceo@hiresynapse.ai")
        ceo_pwd = os.getenv("AI_CEO_PASSWORD", "ceo123")

        if not db.exec(select(User).where(User.email == admin_email)).first():
            db.add(User(email=admin_email, password=admin_pwd, role="admin"))
        if not db.exec(select(User).where(User.email == ceo_email)).first():
            db.add(User(email=ceo_email, password=ceo_pwd, role="ceo"))
        db.commit()

# Auth endpoints
@app.post("/auth/token", response_model=Token)
def token(form: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    u = db.exec(select(User).where(User.email == form.username)).first()
    if not u or u.password != form.password:
        raise HTTPException(status_code=400, detail="Incorrect email or password")
    return Token(access_token=create_token(u))

# Basic ping
@app.get("/")
def root():
    return {"ok": True, "service": APP_NAME}

# Import and mount Agent CEO router
from agent_ceo import router as agent_router  # noqa: E402
app.include_router(agent_router)
