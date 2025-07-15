import os
import sqlite3
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

PERSIST_DIR = os.getenv("PERSIST_DIR", "./chroma")
DB_PATH = os.path.join(PERSIST_DIR, "users.db")

router = APIRouter()

class UserLogin(BaseModel):
    username: str
    password: str

@router.post("/user/login")
def user_login(user: UserLogin):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT password FROM users WHERE username = ?", (user.username,))
    row = c.fetchone()
    conn.close()
    if row and row[0] == user.password:
        return {"success": True, "message": "Login successful."}
    else:
        raise HTTPException(status_code=401, detail="Invalid username or password.") 