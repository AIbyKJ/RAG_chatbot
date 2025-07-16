import os
from fastapi import Depends, HTTPException, status, APIRouter
from fastapi.security import HTTPBasic, HTTPBasicCredentials
import utils.sqlitedb as db

security = HTTPBasic()
router = APIRouter()

def verify_user_credentials(credentials: HTTPBasicCredentials = Depends(security)):
    print(f"Username: {repr(credentials.username)}, Password: {repr(credentials.password)}")
    if not db.authenticate_user(credentials.username, credentials.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Basic"},
        )
    return credentials

@router.get("/user/auth/check")
def user_auth_check(credentials: HTTPBasicCredentials = Depends(verify_user_credentials)):
    return {"success": True, "detail": "User authentication successful."}
