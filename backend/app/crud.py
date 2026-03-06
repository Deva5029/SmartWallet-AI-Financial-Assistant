from sqlalchemy.orm import Session, joinedload
from typing import Optional # <<< --- THIS IS THE FIX ---
from . import models, schemas
from datetime import datetime, timedelta

# --- User CRUD ---
def get_user(db: Session, user_id: int):
    # Eagerly load cards and preferences to prevent extra database calls
    return db.query(models.User).options(
        joinedload(models.User.cards).joinedload(models.CreditCard.offers), 
        joinedload(models.User.preferences)
    ).filter(models.User.user_id == user_id).first()

def get_user_by_email(db: Session, email: str):
    return db.query(models.User).filter(models.User.email == email).first()

def get_user_by_firebase_uid(db: Session, firebase_uid: str):
    return db.query(models.User).options(
        joinedload(models.User.cards).joinedload(models.CreditCard.offers),
        joinedload(models.User.preferences)
    ).filter(models.User.firebase_uid == firebase_uid).first()

def get_user_by_username(db: Session, username: str):
    return db.query(models.User).filter(models.User.username == username).first()

def create_user(db: Session, user: schemas.UserCreate):
    db_user = models.User(
        firebase_uid=user.firebase_uid,
        email=user.email,
        username=user.username,
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)

    # After creating a user, also create their default preferences
    db_prefs = models.UserPreferences(user_id=db_user.user_id)
    db.add(db_prefs)
    db.commit()
    db.refresh(db_user) # Refresh the user object again to load the new preferences relationship
    return db_user

# --- Preferences CRUD ---
def get_user_preferences(db: Session, user_id: int):
    db_prefs = db.query(models.UserPreferences).filter(models.UserPreferences.user_id == user_id).first()
    
    if not db_prefs:
        db_prefs = models.UserPreferences(user_id=user_id, digest_day="Monday")
        db.add(db_prefs)
        db.commit()
        db.refresh(db_prefs)
    
    return db_prefs


def update_user_preferences(db: Session, user_id: int, prefs: schemas.PreferencesUpdate):
    db_prefs = get_user_preferences(db, user_id)
    
    if hasattr(prefs, "digest_day") and prefs.digest_day is not None:
        db_prefs.digest_day = prefs.digest_day

    db.add(db_prefs)
    db.commit()
    db.refresh(db_prefs)
    return db_prefs


# --- Card CRUD ---
def get_card_by_id(db: Session, card_id: int):
    return db.query(models.CreditCard).filter(models.CreditCard.card_id == card_id).first()

def create_user_card(db: Session, card: schemas.CardCreate, user_id: int):
    card_data = card.model_dump(exclude={'user_id'})
    db_card = models.CreditCard(**card_data, owner_id=user_id)
    db.add(db_card)
    db.commit()
    db.refresh(db_card)
    return db_card

# --- Offer CRUD ---
def get_offer_by_id(db: Session, offer_id: int) -> Optional[models.CardOffer]:
    return db.query(models.CardOffer).filter(models.CardOffer.offer_id == offer_id).first()

def update_offer_status(db: Session, offer_id: int, status: str, amount_saved: Optional[float] = None) -> Optional[models.CardOffer]:
    db_offer = get_offer_by_id(db, offer_id=offer_id)
    if db_offer:
        db_offer.status = status
        db_offer.updated_at = datetime.utcnow()
        
        # If the offer is marked as 'used', save the amount.
        # If it's changed to any other status, clear the saved amount.
        if status == "used":
            db_offer.amount_saved = amount_saved
        else:
            db_offer.amount_saved = None
            
        db.add(db_offer)
        db.commit()
        db.refresh(db_offer)
    return db_offer

    
def get_expiring_offers_for_user(db: Session, user_id: int):
    seven_days_from_now = datetime.utcnow() + timedelta(days=7)
    return (
        db.query(models.CardOffer)
        .join(models.CreditCard)
        .filter(
            models.CreditCard.owner_id == user_id,
            models.CardOffer.expiry_date <= seven_days_from_now,
            models.CardOffer.expiry_date >= datetime.utcnow(),
        )
        .options(joinedload(models.CardOffer.card))
        .order_by(models.CardOffer.expiry_date.asc())
        .all()
    )

def create_card_offer(db: Session, offer: schemas.OfferCreate):
    db_offer = models.CardOffer(
        description=offer.description,
        expiry_date=offer.expiry_date,
        card_id=offer.card_id,
        status=offer.status
    )
    db.add(db_offer)
    db.commit()
    db.refresh(db_offer)
    return db_offer