import os
from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPBasicCredentials
from utils.vectordb import get_all_history
from routes.admin.admin_auth import verify_admin_credentials

router = APIRouter()

@router.get("/admin/chat/history/{user_id}")
def get_chat_history(user_id: str, credentials: HTTPBasicCredentials = Depends(verify_admin_credentials)):
    try:
        docs = get_all_history(user_id)
        return {"history": [doc if isinstance(doc, str) else str(doc) for doc in docs]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get chat history: {str(e)}")
