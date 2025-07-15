import os
import sqlite3
from fastapi import Depends, HTTPException, status, APIRouter
from fastapi.security import HTTPBasic, HTTPBasicCredentials

PERSIST_DIR = os.getenv("PERSIST_DIR", "./chroma")
DB_PATH = os.path.join(PERSIST_DIR, "users.db")
security = HTTPBasic()
router = APIRouter()

def verify_user_credentials(credentials: HTTPBasicCredentials = Depends(security)):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT password FROM users WHERE username = ?", (credentials.username,))
    row = c.fetchone()
    conn.close()
    if not row or row[0] != credentials.password:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Basic"},
        )
    return credentials

@router.get("/user/auth/check")
def user_auth_check(credentials: HTTPBasicCredentials = Depends(verify_user_credentials)):
    return {"success": True, "message": "User authentication successful."}
