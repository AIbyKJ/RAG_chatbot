import os
import sqlite3
from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.security import HTTPBasicCredentials
from pydantic import BaseModel
from typing import List
from routes.admin.admin_auth import verify_admin_credentials

PERSIST_DIR = os.getenv("PERSIST_DIR", "./chroma")
DB_PATH = os.path.join(PERSIST_DIR, "users.db")

router = APIRouter()

def get_db():
    os.makedirs(PERSIST_DIR, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_user_table():
    conn = get_db()
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL
    )''')
    conn.commit()
    conn.close()

init_user_table()

class UserCreate(BaseModel):
    username: str
    password: str

class UserOut(BaseModel):
    id: int
    username: str

@router.post("/admin/users", response_model=UserOut)
def add_user(user: UserCreate, credentials: HTTPBasicCredentials = Depends(verify_admin_credentials)):
    conn = get_db()
    c = conn.cursor()
    try:
        c.execute("INSERT INTO users (username, password) VALUES (?, ?)", (user.username, user.password))
        conn.commit()
        user_id = c.lastrowid
    except sqlite3.IntegrityError:
        conn.close()
        raise HTTPException(status_code=400, detail="Username already exists.")
    conn.close()
    return {"id": user_id, "username": user.username}

@router.delete("/admin/users/{username}")
def delete_user(username: str, credentials: HTTPBasicCredentials = Depends(verify_admin_credentials)):
    conn = get_db()
    c = conn.cursor()
    c.execute("DELETE FROM users WHERE username = ?", (username,))
    conn.commit()
    if c.rowcount == 0:
        conn.close()
        raise HTTPException(status_code=404, detail="User not found.")
    conn.close()
    return {"deleted": username}

class ResetPasswordRequest(BaseModel):
    password: str

@router.post("/admin/users/{username}/reset_password")
def reset_password(username: str, req: ResetPasswordRequest, credentials: HTTPBasicCredentials = Depends(verify_admin_credentials)):
    conn = get_db()
    c = conn.cursor()
    c.execute("UPDATE users SET password = ? WHERE username = ?", (req.password, username))
    conn.commit()
    if c.rowcount == 0:
        conn.close()
        raise HTTPException(status_code=404, detail="User not found.")
    conn.close()
    return {"reset": username}

@router.get("/admin/users", response_model=List[UserOut])
def list_users(credentials: HTTPBasicCredentials = Depends(verify_admin_credentials)):
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT id, username FROM users")
    users = c.fetchall()
    conn.close()
    return [{"id": row["id"], "username": row["username"]} for row in users]
