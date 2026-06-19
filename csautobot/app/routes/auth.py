from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel, Field
import sqlite3
from typing import List, Literal, Optional
import time

# Use absolute imports if needed, or relative
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from auth_service import (
    verify_password,
    create_access_token,
    ACCESS_TOKEN_EXPIRE_MINUTES,
    get_current_user,
    get_current_admin_user,
    get_password_hash
)
from auth_db import get_auth_db
from datetime import timedelta

router = APIRouter(tags=["auth"])

class UserResponse(BaseModel):
    id: int
    username: str
    role: str
    created_at: float

class UserCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=64, pattern=r"^[a-zA-Z0-9_\-]+$")
    password: str = Field(..., min_length=8)
    role: Literal["user", "admin"] = "user"

class UserUpdate(BaseModel):
    password: Optional[str] = Field(None, min_length=8)
    role: Optional[Literal["user", "admin"]] = None

class Token(BaseModel):
    access_token: str
    token_type: str

@router.post("/auth/login", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: sqlite3.Connection = Depends(get_auth_db)):
    user = db.execute("SELECT * FROM users WHERE username = ?", (form_data.username,)).fetchone()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not verify_password(form_data.password, user["password_hash"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user["username"], "role": user["role"]}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/auth/me", response_model=UserResponse)
async def read_users_me(current_user: dict = Depends(get_current_user)):
    return UserResponse(**current_user)

@router.get("/users", response_model=List[UserResponse])
async def list_users(current_user: dict = Depends(get_current_admin_user), db: sqlite3.Connection = Depends(get_auth_db)):
    users = db.execute("SELECT id, username, role, created_at FROM users").fetchall()
    return [UserResponse(**u) for u in users]

@router.post("/users", response_model=UserResponse)
async def create_user(user: UserCreate, current_user: dict = Depends(get_current_admin_user), db: sqlite3.Connection = Depends(get_auth_db)):
    existing_user = db.execute("SELECT id FROM users WHERE username = ?", (user.username,)).fetchone()
    if existing_user:
        raise HTTPException(status_code=400, detail="Username already registered")
        
    pwd_hash = get_password_hash(user.password)
    now = time.time()
    cursor = db.cursor()
    cursor.execute(
        "INSERT INTO users (username, password_hash, role, created_at) VALUES (?, ?, ?, ?)",
        (user.username, pwd_hash, user.role, now)
    )
    db.commit()
    new_user_id = cursor.lastrowid
    new_user = db.execute("SELECT id, username, role, created_at FROM users WHERE id = ?", (new_user_id,)).fetchone()
    return UserResponse(**new_user)

@router.put("/users/{user_id}", response_model=UserResponse)
async def update_user(user_id: int, user_update: UserUpdate, current_user: dict = Depends(get_current_admin_user), db: sqlite3.Connection = Depends(get_auth_db)):
    target_user = db.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    if not target_user:
        raise HTTPException(status_code=404, detail="User not found")
        
    updates = []
    params = []
    
    if user_update.password:
        updates.append("password_hash = ?")
        params.append(get_password_hash(user_update.password))
        
    if user_update.role:
        updates.append("role = ?")
        params.append(user_update.role)
        
    if updates:
        params.append(user_id)
        query = f"UPDATE users SET {', '.join(updates)} WHERE id = ?"
        db.execute(query, params)
        db.commit()
        
    updated_user = db.execute("SELECT id, username, role, created_at FROM users WHERE id = ?", (user_id,)).fetchone()
    return UserResponse(**updated_user)

@router.delete("/users/{user_id}", status_code=204)
async def delete_user(user_id: int, current_user: dict = Depends(get_current_admin_user), db: sqlite3.Connection = Depends(get_auth_db)):
    if user_id == current_user["id"]:
        raise HTTPException(status_code=400, detail="Cannot delete your own account")
        
    target_user = db.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    if not target_user:
        raise HTTPException(status_code=404, detail="User not found")
        
    db.execute("DELETE FROM users WHERE id = ?", (user_id,))
    db.commit()
    return None
