from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app import crud, schemas
from app.database import get_db

router = APIRouter()

@router.post("", response_model=schemas.Offer)
def create_offer_for_card(offer: schemas.OfferCreate, db: Session = Depends(get_db)):
    if not crud.get_card_by_id(db, card_id=offer.card_id):
        raise HTTPException(status_code=404, detail="Card not found")
    return crud.create_card_offer(db=db, offer=offer)

# --- REPLACE THIS ENDPOINT ---
@router.patch("/{offer_id}/status", response_model=schemas.Offer)
def update_offer_status_endpoint(offer_id: int, status_update: schemas.OfferStatusUpdate, db: Session = Depends(get_db)):
    db_offer = crud.get_offer_by_id(db, offer_id=offer_id)
    if not db_offer:
        raise HTTPException(status_code=404, detail="Offer not found")
    
    # Pass the amount_saved from the request body to the CRUD function
    return crud.update_offer_status(
        db=db, 
        offer_id=offer_id, 
        status=status_update.status, 
        amount_saved=status_update.amount_saved
    )