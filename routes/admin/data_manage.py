import os
import sqlite3
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from fastapi.security import HTTPBasicCredentials
from typing import List, Optional
from datetime import datetime
from routes.admin.admin_auth import verify_admin_credentials

PERSIST_DIR = os.getenv("PERSIST_DIR", "./chroma")
DB_PATH = os.path.join(PERSIST_DIR, "users.db")
DATA_DIR = os.getenv("DATA_DIR", "./data")

router = APIRouter()

def get_db():
    os.makedirs(PERSIST_DIR, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_pdf_table():
    conn = get_db()
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS pdfs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        filename TEXT NOT NULL,
        owner TEXT,
        upload_time TEXT
    )''')
    conn.commit()
    conn.close()

init_pdf_table()

@router.post("/admin/pdf/upload")
def upload_pdf(files: List[UploadFile] = File(...), owner: Optional[str] = None, credentials: HTTPBasicCredentials = Depends(verify_admin_credentials)):
    os.makedirs(DATA_DIR, exist_ok=True)
    saved_files = []
    conn = get_db()
    c = conn.cursor()
    for file in files:
        if not file.filename.lower().endswith(".pdf"):
            continue
        if owner:
            folder = os.path.join(DATA_DIR, owner)
        else:
            folder = os.path.join(DATA_DIR, "public")
        os.makedirs(folder, exist_ok=True)
        file_path = os.path.join(folder, file.filename)
        with open(file_path, "wb") as f:
            f.write(file.file.read())
        c.execute("INSERT INTO pdfs (filename, owner, upload_time) VALUES (?, ?, ?)", (file.filename, owner or "public", datetime.utcnow().isoformat()))
        saved_files.append(file.filename)
    conn.commit()
    conn.close()
    return {"uploaded": saved_files}

@router.delete("/admin/pdf/{filename}")
def delete_pdf(filename: str, owner: Optional[str] = None, credentials: HTTPBasicCredentials = Depends(verify_admin_credentials)):
    conn = get_db()
    c = conn.cursor()
    if owner:
        folder = os.path.join(DATA_DIR, owner)
    else:
        folder = os.path.join(DATA_DIR, "public")
    file_path = os.path.join(folder, filename)
    if os.path.isfile(file_path):
        os.remove(file_path)
        c.execute("DELETE FROM pdfs WHERE filename = ? AND owner = ?", (filename, owner or "public"))
        conn.commit()
        conn.close()
        return {"deleted": filename}
    else:
        conn.close()
        raise HTTPException(status_code=404, detail="File not found.")

@router.delete("/admin/pdf/user/{owner}")
def delete_pdfs_by_user(owner: str, credentials: HTTPBasicCredentials = Depends(verify_admin_credentials)):
    conn = get_db()
    c = conn.cursor()
    folder = os.path.join(DATA_DIR, owner)
    deleted = []
    if os.path.isdir(folder):
        for file in os.listdir(folder):
            if file.lower().endswith(".pdf"):
                os.remove(os.path.join(folder, file))
                deleted.append(file)
        c.execute("DELETE FROM pdfs WHERE owner = ?", (owner,))
        conn.commit()
    conn.close()
    return {"deleted": deleted}

@router.get("/admin/pdf")
def list_pdfs(credentials: HTTPBasicCredentials = Depends(verify_admin_credentials)):
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT filename, owner FROM pdfs")
    pdfs = c.fetchall()
    conn.close()
    return [{"filename": row["filename"], "owner": row["owner"]} for row in pdfs]
