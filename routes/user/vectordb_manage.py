import os
from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPBasicCredentials
from routes.user.user_auth import verify_user_credentials
import utils.ingest as ingest
import utils.vectordb as vectordb
from utils.sqlitedb import get_ingested_pdfs_by_user, delete_ingested_pdf_by_id

router = APIRouter()

@router.post("/user/vectordb/ingest/all")
def ingest_all(credentials: HTTPBasicCredentials = Depends(verify_user_credentials)):
    try:
        ingest.ingest_my_all_pdfs(user_id=credentials.username)
        return {"detail": "All your PDFs ingested."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/user/vectordb/ingest/one/{filename}")
def ingest_by_filename(filename: str, credentials: HTTPBasicCredentials = Depends(verify_user_credentials)):
    try:
        ingest.ingest_one_pdf_user(filename, user_id=credentials.username)
        return {"detail": f"PDF '{filename}' ingested."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/user/vectordb/pdf/one/{filename}")
def remove_pdf_data(filename: str, credentials: HTTPBasicCredentials = Depends(verify_user_credentials)):
    try:
        vectordb.clear_pdf_by_source(filename, credentials.username)
        return {"detail": f"PDF data for '{filename}' removed from vectordb."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/user/vectordb/pdf/all")
def remove_all_pdf_data(credentials: HTTPBasicCredentials = Depends(verify_user_credentials)):
    try:
        vectordb.clear_pdf_by_user(credentials.username)
        # Also clear ingest_state table for this user
        ingested = get_ingested_pdfs_by_user(credentials.username)
        for pdf in ingested:
            delete_ingested_pdf_by_id(pdf["id"])
        return {"detail": "All your PDF data removed from vectordb."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/user/vectordb/pdf")
def get_available_pdf_data(credentials: HTTPBasicCredentials = Depends(verify_user_credentials)):
    try:
        sources = vectordb.get_pdf_sources()
        # Only show sources belonging to this user or public
        filtered = [s for s in sources if s["ingested_by"] == credentials.username or s["ingested_by"] == "public"]
        return {"sources": filtered}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/user/vectordb/memory")
def clear_my_memory(credentials: HTTPBasicCredentials = Depends(verify_user_credentials)):
    try:
        vectordb.clear_history_by_user(credentials.username)
        return {"detail": "Your chat history cleared from vectordb."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
