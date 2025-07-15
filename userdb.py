import sqlite3
from typing import Optional, List, Tuple
import os

# DB_PATH = os.path.join(os.path.dirname(__file__), 'user_data.db')

PERSIST_DIR = os.getenv("PERSIST_DIR", ".\\sqlite")
# Ensure the directory exists
os.makedirs(PERSIST_DIR, exist_ok=True)
DB_PATH = os.path.join(PERSIST_DIR, "user_data.db")

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    c = conn.cursor()
    # Users table
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            userid TEXT PRIMARY KEY,
            password TEXT NOT NULL,
            is_admin INTEGER DEFAULT 0
        )
    ''')
    # PDFs table
    c.execute('''
        CREATE TABLE IF NOT EXISTS pdfs (
            pdf_id INTEGER PRIMARY KEY AUTOINCREMENT,
            filename TEXT NOT NULL,
            uploaded_by TEXT,
            is_global INTEGER DEFAULT 0,
            FOREIGN KEY(uploaded_by) REFERENCES users(userid)
        )
    ''')
    # User-PDF association table
    c.execute('''
        CREATE TABLE IF NOT EXISTS user_pdfs (
            userid TEXT,
            pdf_id INTEGER,
            PRIMARY KEY(userid, pdf_id),
            FOREIGN KEY(userid) REFERENCES users(userid),
            FOREIGN KEY(pdf_id) REFERENCES pdfs(pdf_id)
        )
    ''')
    conn.commit()
    conn.close()

# User management

def add_user(userid: str, password: str, is_admin: int = 0) -> bool:
    try:
        conn = get_db_connection()
        c = conn.cursor()
        c.execute('INSERT INTO users (userid, password, is_admin) VALUES (?, ?, ?)', (userid, password, is_admin))
        conn.commit()
        conn.close()
        return True
    except sqlite3.IntegrityError:
        return False

def delete_user(userid: str) -> bool:
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('DELETE FROM users WHERE userid = ?', (userid,))
    conn.commit()
    conn.close()
    return c.rowcount > 0

def authenticate_user(userid: str, password: str) -> bool:
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('SELECT * FROM users WHERE userid = ? AND password = ?', (userid, password))
    user = c.fetchone()
    conn.close()
    return user is not None

def is_admin(userid: str) -> bool:
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('SELECT is_admin FROM users WHERE userid = ?', (userid,))
    user = c.fetchone()
    conn.close()
    return user and user['is_admin'] == 1

def update_user_password(userid: str, new_password: str) -> bool:
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('UPDATE users SET password = ? WHERE userid = ?', (new_password, userid))
    conn.commit()
    updated = c.rowcount > 0
    conn.close()
    return updated

def get_all_users() -> List[Tuple[str, int]]:
    """Get all users from the database with their admin status."""
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('SELECT userid, is_admin FROM users')
    users = c.fetchall()
    conn.close()
    return [(row['userid'], row['is_admin']) for row in users]

# PDF management

def add_pdf(filename: str, uploaded_by: Optional[str], is_global: int = 0) -> int:
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('INSERT INTO pdfs (filename, uploaded_by, is_global) VALUES (?, ?, ?)', (filename, uploaded_by, is_global))
    pdf_id = c.lastrowid
    conn.commit()
    conn.close()
    return pdf_id

def associate_pdf_with_user(userid: str, pdf_id: int):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('INSERT OR IGNORE INTO user_pdfs (userid, pdf_id) VALUES (?, ?)', (userid, pdf_id))
    conn.commit()
    conn.close()

def get_user_pdfs(userid: str) -> List[Tuple[int, str]]:
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('''
        SELECT pdfs.pdf_id, pdfs.filename FROM pdfs
        JOIN user_pdfs ON pdfs.pdf_id = user_pdfs.pdf_id
        WHERE user_pdfs.userid = ?
        UNION
        SELECT pdf_id, filename FROM pdfs WHERE is_global = 1
    ''', (userid,))
    pdfs = c.fetchall()
    conn.close()
    return [(row['pdf_id'], row['filename']) for row in pdfs]

def get_all_pdfs_with_users() -> List[Tuple[int, str, List[str], int]]:
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('SELECT pdf_id, filename, is_global FROM pdfs')
    pdfs = c.fetchall()
    result = []
    for pdf in pdfs:
        c.execute('SELECT userid FROM user_pdfs WHERE pdf_id = ?', (pdf['pdf_id'],))
        users = [row['userid'] for row in c.fetchall()]
        result.append((pdf['pdf_id'], pdf['filename'], users, pdf['is_global']))
    conn.close()
    return result



# Initialize DB on import
init_db() 