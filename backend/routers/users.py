from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from uuid import UUID
from pydantic import BaseModel, EmailStr
from database.models import User
from database.config import get_db
from backend.services.auth import get_current_user

router = APIRouter(tags=["Users"])

class UserUpdate(BaseModel):
    username: str
    email: EmailStr

@router.get("/", response_model=list[UserUpdate])
async def list_users(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    users = db.query(User).all()
    return [UserUpdate(username=user.username, email=user.email) for user in users]

@router.get("/{id}", response_model=UserUpdate)
async def get_user(id: UUID, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    user = db.query(User).filter(User.id == id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return UserUpdate(username=user.username, email=user.email)

@router.put("/{id}", response_model=UserUpdate)
async def update_user(id: UUID, user_data: UserUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    user = db.query(User).filter(User.id == id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    
    user.username = user_data.username
    user.email = user_data.email
    db.commit()
    db.refresh(user)
    return UserUpdate(username=user.username, email=user.email)

@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(id: UUID, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    user = db.query(User).filter(User.id == id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    
    db.delete(user)
    db.commit()