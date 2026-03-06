from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app import crud, schemas
from app.database import get_db

router = APIRouter()

@router.post("", response_model=schemas.Card)
def create_card_for_user(card: schemas.CardCreate, db: Session = Depends(get_db)):
    if not crud.get_user(db, user_id=card.user_id):
        raise HTTPException(status_code=404, detail="User not found")
    return crud.create_user_card(db=db, card=card, user_id=card.user_id)
