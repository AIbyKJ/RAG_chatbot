import os
import sqlite3
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from fastapi.security import HTTPBasicCredentials
from typing import List
from datetime import datetime
from routes.user.user_auth import verify_user_credentials

PERSIST_DIR = os.getenv("PERSIST_DIR", "./chroma")
DB_PATH = os.path.join(PERSIST_DIR, "users.db")
DATA_DIR = os.getenv("DATA_DIR", "./data")

router = APIRouter()

def get_db():
    os.makedirs(PERSIST_DIR, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

@router.post("/user/pdf/upload")
def upload_pdf(files: List[UploadFile] = File(...), credentials: HTTPBasicCredentials = Depends(verify_user_credentials)):
    user_id = credentials.username
    folder = os.path.join(DATA_DIR, user_id)
    os.makedirs(folder, exist_ok=True)
    saved_files = []
    conn = get_db()
    c = conn.cursor()
    for file in files:
        if not file.filename.lower().endswith(".pdf"):
            continue
        file_path = os.path.join(folder, file.filename)
        with open(file_path, "wb") as f:
            f.write(file.file.read())
        c.execute("INSERT INTO pdfs (filename, owner, upload_time) VALUES (?, ?, ?)", (file.filename, user_id, datetime.utcnow().isoformat()))
        saved_files.append(file.filename)
    conn.commit()
    conn.close()
    return {"uploaded": saved_files}

@router.delete("/user/pdf/{filename}")
def delete_pdf(filename: str, credentials: HTTPBasicCredentials = Depends(verify_user_credentials)):
    user_id = credentials.username
    folder = os.path.join(DATA_DIR, user_id)
    file_path = os.path.join(folder, filename)
    conn = get_db()
    c = conn.cursor()
    if os.path.isfile(file_path):
        os.remove(file_path)
        c.execute("DELETE FROM pdfs WHERE filename = ? AND owner = ?", (filename, user_id))
        conn.commit()
        conn.close()
        return {"deleted": filename}
    else:
        conn.close()
        raise HTTPException(status_code=404, detail="File not found.")

@router.get("/user/pdf")
def list_pdfs(credentials: HTTPBasicCredentials = Depends(verify_user_credentials)):
    user_id = credentials.username
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT filename FROM pdfs WHERE owner = ?", (user_id,))
    pdfs = c.fetchall()
    conn.close()
    return [row["filename"] for row in pdfs]
