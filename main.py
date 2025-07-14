import os
import asyncio
from fastapi import FastAPI, UploadFile, File, Depends, HTTPException, status, Body
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from pydantic import BaseModel
from typing import List
from dotenv import load_dotenv


from ingest import ingest_all_pdfs, ingest_one_pdf, get_available_pdfs, DATA_DIR
from vectordb import *
from llm import LanguageModel
from userdb import (
    add_user, delete_user, authenticate_user, is_admin,
    add_pdf, associate_pdf_with_user, get_user_pdfs, get_all_pdfs_with_users, update_user_password,
    get_all_users, get_db_connection
)

load_dotenv()
app = FastAPI()

chatmodel = LanguageModel()

security = HTTPBasic()

def verify_password(credentials: HTTPBasicCredentials = Depends(security)):
    """Verify admin credentials from environment variables."""
    # Get the admin username and password from environment variable ADMIN_PASSWORD, ADMIN_USERNAME
    correct_username = os.environ.get("ADMIN_USERNAME", "admin")
    correct_password = os.environ.get("ADMIN_PASSWORD", "123123")

    if credentials.username != correct_username or credentials.password != correct_password:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Basic"},
        )

def verify_user_password(credentials: HTTPBasicCredentials = Depends(security)):
    """Verify user credentials from SQLite database."""
    # First check if it's the admin user
    correct_username = os.environ.get("ADMIN_USERNAME", "admin")
    correct_password = os.environ.get("ADMIN_PASSWORD", "123123")
    
    if credentials.username == correct_username and credentials.password == correct_password:
        return credentials  # Admin user is always valid
    
    # Check against SQLite database for regular users
    if not authenticate_user(credentials.username, credentials.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Basic"},
        )
    
    return credentials  # Return credentials for valid users

class ChatRequest(BaseModel):
    user_id: str
    message: str

class UserRequest(BaseModel):
    userid: str
    password: str
    is_admin: int = 0

class DeleteUserRequest(BaseModel):
    userid: str



class ChangePasswordRequest(BaseModel):
    userid: str
    current_password: str
    new_password: str

class AdminResetPasswordRequest(BaseModel):
    userid: str
    new_password: str

# =====================================================================================

# Main chat endpoint
@app.post("/chat")
async def chat(req: ChatRequest, credentials: HTTPBasicCredentials = Depends(verify_user_password)):
    # Ensure the authenticated user matches the user_id in the request
    if credentials.username != req.user_id:
        raise HTTPException(status_code=403, detail="You can only chat as yourself.")
    
    mem_docs = await asyncio.to_thread(retrieve_user_memory, req.user_id, req.message, k=3)
    pdf_docs = await asyncio.to_thread(retrieve_pdf_for_user, req.message, req.user_id, 3)

    mem_text = "\n".join([d.page_content for d in mem_docs]) if mem_docs else "No previous conversation found."
    pdf_text = "\n".join([d.page_content for d in pdf_docs]) if pdf_docs else "No relevant documents found."

    await asyncio.to_thread(save_user_message, req.user_id, req.message)
    
    prompt = f"""
    Previous conversation:
    {mem_text}

    Relevant documents:
    {pdf_text}

    User: {req.message}
    Answer:
    """

    response = await asyncio.to_thread(chatmodel.predict, prompt)
    return {"response": response, "prompt": prompt}

# Get user message history by userid
@app.get("/chat/history/{user_id}")
async def get_history(user_id: str, credentials: HTTPBasicCredentials = Depends(verify_user_password)):
    # Ensure the authenticated user matches the user_id in the request
    if credentials.username != user_id:
        raise HTTPException(status_code=403, detail="You can only view your own chat history.")
    docs = await asyncio.to_thread(get_all_history, user_id)
    return {"history": [doc.page_content if hasattr(doc, 'page_content') else str(doc) for doc in docs]}

# =====================================================================================

# 1. Clear all chat history memory
@app.delete("/vectordb/memory")
async def clear_all_memory_endpoint(credentials: HTTPBasicCredentials = Depends(verify_password)):
    """Clear all memory for all users."""
    try:
        await asyncio.to_thread(clear_all_memory)
        return {"message": "Memory cleared for all users."}
    except Exception as e:
        return {"error": f"Failed to clear all memory: {str(e)}"}

# 2. Clear chat history memory by userid
@app.delete("/vectordb/memory/{user_id}")
async def clear_memory(user_id: str, credentials: HTTPBasicCredentials = Depends(verify_password)):
    """Clear all memory for a specific user."""
    try:
        await asyncio.to_thread(clear_memory_by_user, user_id)
        return {"message": f"Memory cleared for user {user_id}."}
    except Exception as e:
        return {"error": f"Failed to clear memory: {str(e)}"}

# =====================================================================================

# 1. Clear all pdf data from vectordb
@app.delete("/vectordb/pdf")
async def clear_all_pdf_endpoint(credentials: HTTPBasicCredentials = Depends(verify_password)):
    """Clear all PDF data."""
    try:
        await asyncio.to_thread(clear_all_pdf)
        return {"message": "All PDF data cleared."}
    except Exception as e:
        return {"error": f"Failed to clear all PDF data: {str(e)}"}

# 2. Clear specific pdf by name from vectordb
@app.delete("/vectordb/pdf/{source_name}")
async def clear_pdf_by_source_endpoint(source_name: str, credentials: HTTPBasicCredentials = Depends(security)):
    # Admin can delete any, user can only delete their own
    user = credentials.username
    is_admin_user = user == os.environ.get("ADMIN_USERNAME", "admin")
    # Get PDF ownership info
    pdfs = get_all_pdfs_with_users()
    pdf_entry = next((p for p in pdfs if p[1] == source_name), None)
    if not pdf_entry:
        return {"error": "PDF not found."}
    if not is_admin_user:
        if user not in pdf_entry[2]:
            raise HTTPException(status_code=403, detail="You do not own this PDF.")
    try:
        await asyncio.to_thread(clear_pdf_by_source, source_name)
        return {"message": f"PDF data cleared for source {source_name}."}
    except Exception as e:
        return {"error": f"Failed to clear PDF data for source {source_name}: {str(e)}"}

@app.delete("/vectordb/pdf/user/{userid}")
async def clear_pdf_by_userid(userid: str, credentials: HTTPBasicCredentials = Depends(verify_password)):
    # Admin only - Clear vector embeddings for user's PDFs
    pdfs = get_all_pdfs_with_users()
    deleted_from_vectordb = []
    
    for pdf_id, filename, users, is_global in pdfs:
        if users == [userid] and not is_global:
            try:
                await asyncio.to_thread(clear_pdf_by_source, filename)
                deleted_from_vectordb.append(filename)
            except Exception as e:
                print(f"Warning: Could not clear PDF from vector database: {e}")
    
    return {
        "deleted_from_vectordb": deleted_from_vectordb,
        "message": f"Cleared {len(deleted_from_vectordb)} PDF embeddings from vector database for user {userid}"
    }

@app.delete("/vectordb/pdf/user/me")
async def clear_pdf_by_user_me(credentials: HTTPBasicCredentials = Depends(security)):
    user = credentials.username
    pdfs = get_all_pdfs_with_users()
    deleted_from_vectordb = []
    
    for pdf_id, filename, users, is_global in pdfs:
        if users == [user] and not is_global:
            try:
                await asyncio.to_thread(clear_pdf_by_source, filename)
                deleted_from_vectordb.append(filename)
            except Exception as e:
                print(f"Warning: Could not clear PDF from vector database: {e}")
    
    return {
        "deleted_from_vectordb": deleted_from_vectordb,
        "message": f"Cleared {len(deleted_from_vectordb)} PDF embeddings from vector database for user {user}"
    }

# List available PDF sources in vectordb
@app.get("/vectordb/pdf/sources")
async def get_pdf_sources_endpoint(credentials: HTTPBasicCredentials = Depends(verify_password)):
    sources = await asyncio.to_thread(get_pdf_sources)
    return {"sources": sources}

# =====================================================================================

# 1. Upload PDF(s) endpoint
@app.post("/pdf/upload")
async def upload_pdf(files: List[UploadFile] = File(...), credentials: HTTPBasicCredentials = Depends(verify_password)):
    os.makedirs(DATA_DIR, exist_ok=True)

    saved_files = []
    for file in files:
        if not file.filename.lower().endswith(".pdf"):
            continue
        file_path = os.path.join(DATA_DIR, file.filename)
        with open(file_path, "wb") as f:
            f.write(await file.read())
        saved_files.append(file.filename)
    return {"uploaded": saved_files}

# 2. Ingest all PDFs in data/
@app.post("/pdf/ingest")
async def ingest_all_pdfs_endpoint(credentials: HTTPBasicCredentials = Depends(verify_password)):
    result = await asyncio.to_thread(ingest_all_pdfs)
    return result

def user_exists(userid: str) -> bool:
    users = get_all_users()
    return any(u[0] == userid for u in users)

# 2b. Ingest all PDFs accessible to a specific user
@app.post("/pdf/ingest/user/{userid}")
async def ingest_pdfs_for_user(userid: str, credentials: HTTPBasicCredentials = Depends(verify_password)):
    if not user_exists(userid):
        raise HTTPException(status_code=404, detail=f"User {userid} does not exist.")
    result = await asyncio.to_thread(ingest_all_pdfs, user_id=userid)
    return result

# 3. Ingest one file
@app.post("/pdf/ingest/{filename}")
async def ingest_pdf(filename: str, credentials: HTTPBasicCredentials = Depends(verify_password)):
    result = await asyncio.to_thread(ingest_one_pdf, filename)
    return result

# 3b. Ingest one file for a specific user
@app.post("/pdf/ingest/{filename}/user/{userid}")
async def ingest_pdf_for_user(filename: str, userid: str, credentials: HTTPBasicCredentials = Depends(verify_password)):
    if not user_exists(userid):
        raise HTTPException(status_code=404, detail=f"User {userid} does not exist.")
    result = await asyncio.to_thread(ingest_one_pdf, filename, userid)
    return result

# 4. Delete all PDF files in data
@app.delete("/pdf")
async def delete_all_pdfs(credentials: HTTPBasicCredentials = Depends(verify_password)):
    deleted_files = []
    deleted_from_db = []
    
    # Delete files from filesystem
    for file in os.listdir(DATA_DIR):
        if file.lower().endswith(".pdf"):
            os.remove(os.path.join(DATA_DIR, file))
            deleted_files.append(file)
    
    # Delete from vector database
    try:
        await asyncio.to_thread(clear_all_pdf)
    except Exception as e:
        print(f"Warning: Could not clear all PDFs from vector database: {e}")
    
    # Delete from SQLite database
    try:
        conn = get_db_connection()
        c = conn.cursor()
        # Delete all user_pdfs associations
        c.execute('DELETE FROM user_pdfs')
        # Delete all pdfs
        c.execute('DELETE FROM pdfs')
        conn.commit()
        conn.close()
        deleted_from_db = deleted_files  # All files were deleted from DB
    except Exception as e:
        print(f"Warning: Could not delete PDFs from database: {e}")
    
    return {
        "deleted_files": deleted_files,
        "deleted_from_db": deleted_from_db,
        "message": f"Deleted {len(deleted_files)} files and {len(deleted_from_db)} database records"
    }

@app.delete("/pdf/user/{userid}")
async def delete_pdfs_by_userid(userid: str, credentials: HTTPBasicCredentials = Depends(verify_password)):
    if not user_exists(userid):
        raise HTTPException(status_code=404, detail=f"User {userid} does not exist.")
    pdfs = get_all_pdfs_with_users()
    deleted_files = []
    deleted_from_db = []
    
    for pdf_id, filename, users, is_global in pdfs:
        if users == [userid] and not is_global:
            # Delete file from filesystem
            file_path = os.path.join(DATA_DIR, filename)
            if os.path.isfile(file_path) and filename.lower().endswith(".pdf"):
                os.remove(file_path)
                deleted_files.append(filename)
            
            # Delete from vector database
            try:
                await asyncio.to_thread(clear_pdf_by_source, filename)
            except Exception as e:
                print(f"Warning: Could not clear PDF from vector database: {e}")
            
            # Delete from SQLite database
            try:
                conn = get_db_connection()
                c = conn.cursor()
                # Delete from user_pdfs association
                c.execute('DELETE FROM user_pdfs WHERE pdf_id = ?', (pdf_id,))
                # Delete from pdfs table
                c.execute('DELETE FROM pdfs WHERE pdf_id = ?', (pdf_id,))
                conn.commit()
                conn.close()
                deleted_from_db.append(filename)
            except Exception as e:
                print(f"Warning: Could not delete PDF from database: {e}")
    
    return {
        "deleted_files": deleted_files,
        "deleted_from_db": deleted_from_db,
        "message": f"Deleted {len(deleted_files)} files and {len(deleted_from_db)} database records for user {userid}"
    }

@app.delete("/pdf/user/me")
async def delete_pdfs_by_user_me(credentials: HTTPBasicCredentials = Depends(security)):
    user = credentials.username
    pdfs = get_all_pdfs_with_users()
    deleted_files = []
    deleted_from_db = []
    
    for pdf_id, filename, users, is_global in pdfs:
        if users == [user] and not is_global:
            # Delete file from filesystem
            file_path = os.path.join(DATA_DIR, filename)
            if os.path.isfile(file_path) and filename.lower().endswith(".pdf"):
                os.remove(file_path)
                deleted_files.append(filename)
            
            # Delete from vector database
            try:
                await asyncio.to_thread(clear_pdf_by_source, filename)
            except Exception as e:
                print(f"Warning: Could not clear PDF from vector database: {e}")
            
            # Delete from SQLite database
            try:
                conn = get_db_connection()
                c = conn.cursor()
                # Delete from user_pdfs association
                c.execute('DELETE FROM user_pdfs WHERE pdf_id = ?', (pdf_id,))
                # Delete from pdfs table
                c.execute('DELETE FROM pdfs WHERE pdf_id = ?', (pdf_id,))
                conn.commit()
                conn.close()
                deleted_from_db.append(filename)
            except Exception as e:
                print(f"Warning: Could not delete PDF from database: {e}")
    
    return {
        "deleted_files": deleted_files,
        "deleted_from_db": deleted_from_db,
        "message": f"Deleted {len(deleted_files)} files and {len(deleted_from_db)} database records for user {user}"
    }

# =====================================================================================

# 1. Get available user IDs (from vectordb)
@app.get("/users")
async def get_available_users(credentials: HTTPBasicCredentials = Depends(verify_password)):
    user_ids = await asyncio.to_thread(get_available_user_ids)
    return {"user_ids": user_ids}

# 2. Get all users from SQLite database
@app.get("/admin/users")
async def get_all_users_endpoint(credentials: HTTPBasicCredentials = Depends(security)):
    """Get all users from the SQLite database with their admin status."""
    if not is_env_admin(credentials):
        raise HTTPException(status_code=403, detail="Not authorized")
    users = await asyncio.to_thread(get_all_users)
    return {"users": [{"userid": userid, "is_admin": bool(is_admin)} for userid, is_admin in users]}

# 2. Get available PDFs in data folder
@app.get("/pdf")
async def get_available_pdfs_endpoint(credentials: HTTPBasicCredentials = Depends(verify_password)):
    pdfs = await asyncio.to_thread(get_available_pdfs)
    return {"pdfs": pdfs}

# =====================================================================================

@app.get("/auth/check")
async def auth_check(credentials: HTTPBasicCredentials = Depends(verify_user_password)):
    return {"success": True, "message": "Authentication successful."}

# Helper to check if current credentials are the .env admin

def is_env_admin(credentials: HTTPBasicCredentials):
    correct_username = os.environ.get("ADMIN_USERNAME", "admin")
    correct_password = os.environ.get("ADMIN_PASSWORD", "123123")
    return credentials.username == correct_username and credentials.password == correct_password

# Admin: Add user
@app.post("/admin/user/add")
async def admin_add_user(req: UserRequest, credentials: HTTPBasicCredentials = Depends(security)):
    if not is_env_admin(credentials):
        raise HTTPException(status_code=403, detail="Not authorized")
    if add_user(req.userid, req.password, req.is_admin):
        return {"message": f"User {req.userid} added."}
    else:
        return {"error": "User already exists."}

# Admin: Delete user
@app.delete("/admin/user/delete")
async def admin_delete_user(req: DeleteUserRequest, credentials: HTTPBasicCredentials = Depends(security)):
    if not is_env_admin(credentials):
        raise HTTPException(status_code=403, detail="Not authorized")
    if delete_user(req.userid):
        return {"message": f"User {req.userid} deleted."}
    else:
        return {"error": "User not found."}

# User: Authenticate
@app.post("/user/auth")
async def user_auth(req: UserRequest):
    if authenticate_user(req.userid, req.password):
        return {"message": "Authenticated"}
    else:
        return {"error": "Invalid credentials"}

# User: Upload PDF (user-specific)
@app.post("/user/pdf/upload")
async def user_upload_pdf(userid: str, files: List[UploadFile] = File(...)):
    if not user_exists(userid):
        raise HTTPException(status_code=404, detail=f"User {userid} does not exist.")
    os.makedirs(DATA_DIR, exist_ok=True)
    uploaded = []
    
    for file in files:
        if not file.filename.lower().endswith(".pdf"):
            continue
        file_path = os.path.join(DATA_DIR, file.filename)
        with open(file_path, "wb") as f:
            f.write(await file.read())
        pdf_id = add_pdf(file.filename, uploaded_by=userid, is_global=0)
        associate_pdf_with_user(userid, pdf_id)
        uploaded.append(file.filename)
    
    return {"uploaded": uploaded}

# Admin: Upload PDF for user or global
@app.post("/admin/pdf/upload")
async def admin_upload_pdf(userid: str = None, is_global: int = 0, files: List[UploadFile] = File(...), credentials: HTTPBasicCredentials = Depends(security)):
    if not is_env_admin(credentials):
        raise HTTPException(status_code=403, detail="Not authorized")
    if userid and not user_exists(userid):
        raise HTTPException(status_code=404, detail=f"User {userid} does not exist.")
    os.makedirs(DATA_DIR, exist_ok=True)
    uploaded = []
    
    for file in files:
        if not file.filename.lower().endswith(".pdf"):
            continue
        file_path = os.path.join(DATA_DIR, file.filename)
        with open(file_path, "wb") as f:
            f.write(await file.read())
        pdf_id = add_pdf(file.filename, uploaded_by=userid, is_global=is_global)
        if userid:
            associate_pdf_with_user(userid, pdf_id)
        uploaded.append(file.filename)
    
    return {"uploaded": uploaded}

# Admin: List all PDFs with user associations
@app.get("/admin/pdf/list")
async def admin_list_pdfs(credentials: HTTPBasicCredentials = Depends(security)):
    if not is_env_admin(credentials):
        raise HTTPException(status_code=403, detail="Not authorized")
    pdfs = get_all_pdfs_with_users()
    return {"pdfs": [
        {"pdf_id": pdf_id, "filename": filename, "users": users, "is_global": is_global}
        for pdf_id, filename, users, is_global in pdfs
    ]}

# User: List their available PDFs
@app.get("/user/pdf/list/{userid}")
async def user_list_pdfs(userid: str):
    pdfs = get_user_pdfs(userid)
    return {"pdfs": [
        {"pdf_id": pdf_id, "filename": filename}
        for pdf_id, filename in pdfs
    ]}

@app.post("/user/change_password")
async def user_change_password(req: ChangePasswordRequest = Body(...)):
    # Authenticate current password
    if not authenticate_user(req.userid, req.current_password):
        raise HTTPException(status_code=401, detail="Current password is incorrect.")
    # Update password
    if update_user_password(req.userid, req.new_password):
        return {"message": "Password changed successfully."}
    else:
        return {"error": "Failed to change password."}

@app.post("/admin/user/reset_password")
async def admin_reset_user_password(req: AdminResetPasswordRequest, credentials: HTTPBasicCredentials = Depends(security)):
    if not is_env_admin(credentials):
        raise HTTPException(status_code=403, detail="Not authorized")
    if update_user_password(req.userid, req.new_password):
        return {"message": f"Password for user {req.userid} reset successfully."}
    else:
        return {"error": "Failed to reset password (user may not exist)."}
