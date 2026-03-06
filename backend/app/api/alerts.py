from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app import crud, schemas
from app.database import get_db

router = APIRouter()

@router.get("/{user_id}", response_model=List[schemas.AlertOffer])
def read_expiring_offers(user_id: int, db: Session = Depends(get_db)):
    """
    Retrieve all offers for a specific user that are expiring within the next 7 days.
    """
    alerts = crud.get_expiring_offers_for_user(db, user_id=user_id)
    return alerts

