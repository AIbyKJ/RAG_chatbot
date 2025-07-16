import os
from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.security import HTTPBasicCredentials
from pydantic import BaseModel
from typing import List
from routes.admin.admin_auth import verify_admin_credentials
import utils.sqlitedb as db

router = APIRouter()

class UserCreate(BaseModel):
    username: str
    password: str

class UserOut(BaseModel):
    id: int
    username: str

@router.post("/admin/users", response_model=UserOut)
def add_user(user: UserCreate, credentials: HTTPBasicCredentials = Depends(verify_admin_credentials)):
    success = db.add_user(user.username, user.password)
    if not success:
        raise HTTPException(status_code=400, detail="User already exists.")
    # Fetch the user to get the id
    users = db.get_all_users()
    for u in users:
        if u['userid'] == user.username:
            return UserOut(id=u['id'], username=u['userid'])
    raise HTTPException(status_code=500, detail="User creation failed.")

@router.delete("/admin/users/{username}")
def delete_user(username: str, credentials: HTTPBasicCredentials = Depends(verify_admin_credentials)):
    success = db.delete_user(username)
    if not success:
        raise HTTPException(status_code=404, detail="User not found.")
    return {"detail": "User deleted."}

class ResetPasswordRequest(BaseModel):
    password: str

@router.post("/admin/users/{username}/reset_password")
def reset_password(username: str, req: ResetPasswordRequest, credentials: HTTPBasicCredentials = Depends(verify_admin_credentials)):
    success = db.update_user_password(username, req.password)
    if not success:
        raise HTTPException(status_code=404, detail="User not found.")
    return {"detail": "Password reset successful."}

@router.get("/admin/users", response_model=List[UserOut])
def list_users(credentials: HTTPBasicCredentials = Depends(verify_admin_credentials)):
    users = db.get_all_users()
    return [UserOut(id=u['id'], username=u['userid']) for u in users]
