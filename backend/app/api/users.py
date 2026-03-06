from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app import crud, schemas
from app.database import get_db

router = APIRouter()

@router.post("", response_model=schemas.User)
def create_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    if crud.get_user_by_email(db, email=user.email):
        raise HTTPException(status_code=400, detail="Email already registered")
    if crud.get_user_by_username(db, username=user.username):
        raise HTTPException(status_code=400, detail="Username is already taken")
    if crud.get_user_by_firebase_uid(db, firebase_uid=user.firebase_uid):
        raise HTTPException(status_code=400, detail="Firebase UID already registered")
    return crud.create_user(db=db, user=user)

@router.get("/{user_id}", response_model=schemas.User)
def read_user(user_id: int, db: Session = Depends(get_db)):
    db_user = crud.get_user(db, user_id=user_id)
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return db_user

@router.get("/by_firebase/{firebase_uid}", response_model=schemas.User)
def read_user_by_firebase_uid(firebase_uid: str, db: Session = Depends(get_db)):
    db_user = crud.get_user_by_firebase_uid(db, firebase_uid=firebase_uid)
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return db_user
