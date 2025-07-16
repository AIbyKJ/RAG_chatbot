import os
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import utils.sqlitedb as db

router = APIRouter()

class UserLogin(BaseModel):
    username: str
    password: str

@router.post("/user/login")
def user_login(user: UserLogin):
    if db.authenticate_user(user.username, user.password):
        return {"success": True, "user_id": user.username}
    else:
        raise HTTPException(status_code=401, detail="Invalid username or password.") 