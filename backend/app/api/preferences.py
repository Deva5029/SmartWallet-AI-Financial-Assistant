from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app import crud, schemas
from app.database import get_db

router = APIRouter()

@router.get("/{user_id}", response_model=schemas.Preferences)
def get_user_preferences(user_id: int, db: Session = Depends(get_db)):
    preferences = crud.get_user_preferences(db, user_id=user_id)
    if not preferences:
        raise HTTPException(status_code=404, detail="Preferences not found for this user.")
    return preferences

@router.put("/{user_id}", response_model=schemas.Preferences)
def update_user_preferences(user_id: int, preferences: schemas.PreferencesUpdate, db: Session = Depends(get_db)):
    if not crud.get_user(db, user_id=user_id):
        raise HTTPException(status_code=404, detail="User not found")
    return crud.update_user_preferences(db, user_id=user_id, prefs=preferences)
