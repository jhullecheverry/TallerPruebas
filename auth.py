from fastapi import Depends, HTTPException, status, Header
from jose import JWTError, jwt
from datetime import datetime, timedelta
from typing import Optional
import os
from db import get_session
from crud import get_user_by_id as crud_get_user_by_id
from passlib.context import CryptContext

SECRET = os.environ.get("JWT_SECRET", "dev_secret")
EXPIRES_SECONDS = int(os.environ.get("JWT_EXPIRES_SECONDS", 7200))

pwd_ctx = CryptContext(schemes=["bcrypt"], deprecated="auto")

def create_access_token(sub: int, username: str, expires_seconds: int = EXPIRES_SECONDS):
    expire = datetime.utcnow() + timedelta(seconds=expires_seconds)
    payload = {"sub": sub, "username": username, "exp": expire}
    token = jwt.encode(payload, SECRET, algorithm="HS256")
    return token

def verify_password(plain_password, hashed_password):
    return pwd_ctx.verify(plain_password, hashed_password)

def get_current_user(authorization: Optional[str] = Header(None)):
    if authorization is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="missing token")
    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid auth header")
    token = parts[1]
    try:
        payload = jwt.decode(token, SECRET, algorithms=["HS256"])
        user_id = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid token")
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid token")
    db = get_session()
    # Access the User model via db query
    user = db.query(crud_get_user_by_id.__globals__['User']).get(user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="user not found")
    return user
