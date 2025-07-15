import os
from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPBasicCredentials
from typing import Optional
from utils.ingest import ingest_all_pdfs, ingest_one_pdf
from utils.vectordb import clear_all_pdf, clear_pdf_by_source, get_pdf_sources, clear_all_memory, clear_memory_by_user
from routes.admin.admin_auth import verify_admin_credentials

router = APIRouter()

@router.post("/admin/vectordb/ingest/all")
def ingest_all(credentials: HTTPBasicCredentials = Depends(verify_admin_credentials)):
    try:
        result = ingest_all_pdfs()
        return {"ingested": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to ingest all PDFs: {str(e)}")

@router.post("/admin/vectordb/ingest/{filename}")
def ingest_by_filename(filename: str, credentials: HTTPBasicCredentials = Depends(verify_admin_credentials)):
    try:
        result = ingest_one_pdf(filename)
        return {"ingested": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to ingest PDF: {str(e)}")

@router.delete("/admin/vectordb/pdf/{filename}")
def remove_pdf_data(filename: str, credentials: HTTPBasicCredentials = Depends(verify_admin_credentials)):
    try:
        clear_pdf_by_source(filename)
        return {"removed": filename}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to remove PDF data: {str(e)}")

@router.delete("/admin/vectordb/pdf/user/{owner}")
def remove_pdf_data_by_user(owner: str, credentials: HTTPBasicCredentials = Depends(verify_admin_credentials)):
    # This would require iterating all PDFs for the user and removing them
    # For now, just a placeholder
    return {"removed": f"All PDFs for user {owner} (not implemented)"}

@router.get("/admin/vectordb/pdf")
def get_available_pdf_data(credentials: HTTPBasicCredentials = Depends(verify_admin_credentials)):
    try:
        sources = get_pdf_sources()
        return {"sources": sources}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get PDF sources: {str(e)}")

@router.delete("/admin/vectordb/memory")
def clear_all_users_memory(credentials: HTTPBasicCredentials = Depends(verify_admin_credentials)):
    try:
        clear_all_memory()
        return {"message": "Memory cleared for all users."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to clear all memory: {str(e)}")

@router.delete("/admin/vectordb/memory/{user_id}")
def clear_user_memory(user_id: str, credentials: HTTPBasicCredentials = Depends(verify_admin_credentials)):
    try:
        clear_memory_by_user(user_id)
        return {"message": f"Memory cleared for user {user_id}."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to clear memory: {str(e)}")
