import os
from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPBasicCredentials
from utils.ingest import ingest_all_pdfs, ingest_one_pdf
from utils.vectordb import clear_all_pdf, clear_pdf_by_source, get_pdf_sources, clear_memory_by_user
from routes.user.user_auth import verify_user_credentials

router = APIRouter()

@router.post("/user/vectordb/ingest/all")
def ingest_all(credentials: HTTPBasicCredentials = Depends(verify_user_credentials)):
    # Ingest all PDFs for this user and public
    # (Assume ingest_all_pdfs handles user scoping or needs to be updated)
    try:
        result = ingest_all_pdfs()
        return {"ingested": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to ingest all PDFs: {str(e)}")

@router.post("/user/vectordb/ingest/{filename}")
def ingest_by_filename(filename: str, credentials: HTTPBasicCredentials = Depends(verify_user_credentials)):
    try:
        result = ingest_one_pdf(filename)
        return {"ingested": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to ingest PDF: {str(e)}")

@router.delete("/user/vectordb/pdf/{filename}")
def remove_pdf_data(filename: str, credentials: HTTPBasicCredentials = Depends(verify_user_credentials)):
    try:
        clear_pdf_by_source(filename)
        return {"removed": filename}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to remove PDF data: {str(e)}")

@router.delete("/user/vectordb/pdf/all")
def remove_all_pdf_data(credentials: HTTPBasicCredentials = Depends(verify_user_credentials)):
    try:
        clear_all_pdf()
        return {"removed": "all"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to remove all PDF data: {str(e)}")

@router.get("/user/vectordb/pdf")
def get_available_pdf_data(credentials: HTTPBasicCredentials = Depends(verify_user_credentials)):
    try:
        sources = get_pdf_sources()
        return {"sources": sources}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get PDF sources: {str(e)}")

@router.delete("/user/vectordb/memory")
def clear_my_memory(credentials: HTTPBasicCredentials = Depends(verify_user_credentials)):
    try:
        user_id = credentials.username
        clear_memory_by_user(user_id)
        return {"message": f"Memory cleared for user {user_id}."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to clear memory: {str(e)}")
