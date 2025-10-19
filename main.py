from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel, EmailStr
from typing import List
import logging
import os
import json
from filelock import FileLock
from pythonjsonlogger import jsonlogger
from datetime import datetime
import uuid

USERS_FILE = "users.json"
LOCK_FILE = USERS_FILE + ".lock"

# logger setup: JSON formatter (only stdout)
logger = logging.getLogger("api_logger")
logger.setLevel(logging.INFO)
logHandler = logging.StreamHandler()  # stdout (Docker captures this)
formatter = jsonlogger.JsonFormatter('%(asctime)s %(levelname)s %(name)s %(message)s %(request_id)s %(email)s')
logHandler.setFormatter(formatter)
logger.addHandler(logHandler)

app = FastAPI(title="Simple File-backed Auth API (for logging tests)")

class RegisterIn(BaseModel):
    name: str
    email: EmailStr

class User(BaseModel):
    id: str
    name: str
    email: EmailStr
    created_at: datetime

def ensure_users_file():
    if not os.path.exists(USERS_FILE):
        with open(USERS_FILE, "w", encoding="utf-8") as f:
            json.dump([], f)

@app.on_event("startup")
def startup_event():
    ensure_users_file()
    logger.info("app_startup", extra={"request_id": None, "email": None})

def read_users() -> List[dict]:
    with open(USERS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def write_users_atomic(users: List[dict]):
    lock = FileLock(LOCK_FILE, timeout=10)
    with lock:
        tmp = USERS_FILE + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(users, f, default=str, ensure_ascii=False, indent=2)
        os.replace(tmp, USERS_FILE)

@app.post("/register", status_code=201)
async def register(payload: RegisterIn, request: Request):
    req_id = str(uuid.uuid4())
    extra_base = {"request_id": req_id, "email": payload.email}

    logger.info("register_attempt", extra=extra_base)

    lock = FileLock(LOCK_FILE, timeout=10)
    with lock:
        users = read_users()
        if any(u.get("email") == payload.email for u in users):
            logger.warning("register_conflict", extra=extra_base)
            raise HTTPException(status_code=409, detail="email already registered")
        user = {
            "id": str(uuid.uuid4()),
            "name": payload.name,
            "email": payload.email,
            "created_at": datetime.utcnow().isoformat() + "Z"
        }
        users.append(user)
        write_users_atomic(users)

    logger.info("register_success", extra={**extra_base, "user_id": user["id"]})
    return {"status": "ok", "user": user}

@app.get("/health")
async def health():
    return {"status": "ok"}

@app.get("/users")
async def list_users():
    users = read_users()
    return {"count": len(users), "users": users}
