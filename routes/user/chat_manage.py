import os
from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPBasicCredentials
from pydantic import BaseModel
from utils.vectordb import get_all_history, save_user_message, retrieve_user_memory, retrieve_pdf
from utils.llm import LanguageModel
import asyncio
from routes.user.user_auth import verify_user_credentials

router = APIRouter()
chatmodel = LanguageModel()

class ChatRequest(BaseModel):
    user_id: str
    message: str

@router.post("/user/chat")
async def chat(req: ChatRequest, credentials: HTTPBasicCredentials = Depends(verify_user_credentials)):
    # TODO: check user credentials match req.user_id
    mem_docs = await asyncio.to_thread(retrieve_user_memory, req.user_id, req.message, 3)
    pdf_docs = await asyncio.to_thread(retrieve_pdf, req.message, req.user_id, 3)
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

@router.get("/user/chat/history")
async def get_my_history(credentials: HTTPBasicCredentials = Depends(verify_user_credentials)):
    # TODO: extract user_id from credentials
    user_id = credentials.username
    docs = await asyncio.to_thread(get_all_history, user_id)
    return {"history": [doc.page_content if hasattr(doc, 'page_content') else str(doc) for doc in docs]}
