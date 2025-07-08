import os
import asyncio
from fastapi import FastAPI, UploadFile, File
from pydantic import BaseModel
from typing import List


from ingest import ingest_all_pdfs, ingest_one_pdf, DATA_DIR, get_available_pdfs
from vectordb import *
from vectordb import get_available_user_ids
from llm import LanguageModel

load_dotenv()
app = FastAPI()

chatmodel = LanguageModel(fake_model=True)

class ChatRequest(BaseModel):
    user_id: str
    message: str


# =====================================================================================

# Main chat endpoint
@app.post("/chat")
async def chat(req: ChatRequest):
    await asyncio.to_thread(save_user_message, req.user_id, req.message)
    mem_docs = await asyncio.to_thread(retrieve_user_memory, req.user_id, req.message, k=3)
    pdf_docs = await asyncio.to_thread(retrieve_pdf, req.message, k=3)

    mem_text = "\n".join([d.page_content for d in mem_docs]) if mem_docs else "No previous conversation found."
    pdf_text = "\n".join([d.page_content for d in pdf_docs]) if pdf_docs else "No relevant documents found."

    prompt = f"""
    Previous conversation:
    {mem_text}

    Relevant documents:
    {pdf_text}

    User: {req.message}
    Answer:
    """

    # print("*"*10, prompt, "*"*10)
    response = await asyncio.to_thread(chatmodel.predict, prompt)
    return {"response": response, "prompt": prompt}

# Get user message history by userid
@app.get("/chat/history/{user_id}")
async def get_history(user_id: str):
    docs = await asyncio.to_thread(get_all_history, user_id)
    return {"history": [doc.page_content if hasattr(doc, 'page_content') else str(doc) for doc in docs]}

# =====================================================================================

# 1. Clear all chat history memory
@app.delete("/vectordb/memory")
async def clear_all_memory_endpoint():
    """Clear all memory for all users."""
    try:
        await asyncio.to_thread(clear_all_memory)
        return {"message": "Memory cleared for all users."}
    except Exception as e:
        return {"error": f"Failed to clear all memory: {str(e)}"}

# 2. Clear chat history memory by userid
@app.delete("/vectordb/memory/{user_id}")
async def clear_memory(user_id: str):
    """Clear all memory for a specific user."""
    try:
        await asyncio.to_thread(clear_memory_by_user, user_id)
        return {"message": f"Memory cleared for user {user_id}."}
    except Exception as e:
        return {"error": f"Failed to clear memory: {str(e)}"}

# =====================================================================================

# 1. Clear all pdf data from vectordb
@app.delete("/vectordb/pdf")
async def clear_all_pdf_endpoint():
    """Clear all PDF data."""
    try:
        await asyncio.to_thread(clear_all_pdf)
        return {"message": "All PDF data cleared."}
    except Exception as e:
        return {"error": f"Failed to clear all PDF data: {str(e)}"}

# 2. Clear specific pdf by name from vectordb
@app.delete("/vectordb/pdf/{source_name}")
async def clear_pdf_by_source_endpoint(source_name: str):
    """Clear PDF data for a specific source name."""
    try:
        await asyncio.to_thread(clear_pdf_by_source, source_name)
        return {"message": f"PDF data cleared for source {source_name}."}
    except Exception as e:
        return {"error": f"Failed to clear PDF data for source {source_name}: {str(e)}"}

# =====================================================================================

# 1. Upload PDF(s) endpoint
@app.post("/pdf/upload")
async def upload_pdf(files: List[UploadFile] = File(...)):
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
async def ingest_all_pdfs_endpoint():
    result = await asyncio.to_thread(ingest_all_pdfs)
    return result

# 3. Ingest one file
@app.post("/pdf/ingest/{filename}")
async def ingest_pdf(filename: str):
    result = await asyncio.to_thread(ingest_one_pdf, filename)
    return result

# 4. Delete all PDF files in data
@app.delete("/pdf")
async def delete_all_pdfs():
    deleted = []
    for file in os.listdir(DATA_DIR):
        if file.lower().endswith(".pdf"):
            os.remove(os.path.join(DATA_DIR, file))
            deleted.append(file)
    return {"deleted": deleted}

# 5. Delete one PDF file in data
@app.delete("/pdf/{filename}")
async def delete_pdf(filename: str):
    file_path = os.path.join(DATA_DIR, filename)
    if os.path.isfile(file_path) and filename.lower().endswith(".pdf"):
        os.remove(file_path)
        return {"deleted": filename}
    else:
        return {"error": "File not found or not a PDF."}

# =====================================================================================

# 1. Get available user IDs
@app.get("/users")
async def get_available_users():
    user_ids = await asyncio.to_thread(get_available_user_ids)
    return {"user_ids": user_ids}

# 2. Get available PDFs in data folder
@app.get("/pdf")
async def get_available_pdfs_endpoint():
    pdfs = await asyncio.to_thread(get_available_pdfs)
    return {"pdfs": pdfs}
