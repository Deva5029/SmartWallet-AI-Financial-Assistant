from pydantic import BaseModel, ConfigDict, Field, validator
from datetime import datetime
from typing import List, Optional, Dict, Any

# --- A simple schema for nested card data in alerts ---
class CardForAlert(BaseModel):
    card_nickname: str
    bank_name: str
    model_config = ConfigDict(from_attributes=True)

# --- Offer Schemas ---
class OfferBase(BaseModel):
    description: str = Field(..., min_length=1, max_length=500, description="Offer description")
    expiry_date: datetime = Field(..., description="Offer expiry date")
    status: str
    amount_saved: Optional[float] = None
    category: str = Field("General", max_length=50) # NEW FIELD

    @validator('description')
    def description_must_not_be_empty(cls, v):
        if not v.strip():
            raise ValueError('Description cannot be empty')
        return v.strip()

class OfferCreate(OfferBase):
    card_id: int = Field(..., gt=0, description="Card ID must be positive")
    status: str = "available"
    category: str = "General" # NEW FIELD with default

    @validator('expiry_date', pre=True)
    def parse_expiry_date(cls, v):
        if isinstance(v, str):
            try:
                return datetime.strptime(v, "%Y-%m-%d")
            except ValueError:
                raise ValueError(f"Invalid date format: {v}. Please use YYYY-MM-DD.")
        return v

    @validator('expiry_date')
    def expiry_date_must_be_future(cls, v):
        if v.date() < datetime.now().date():
            raise ValueError('Expiry date must be today or in the future')
        return v

class Offer(OfferBase):
    offer_id: int
    card_id: int
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)

class OfferStatusUpdate(BaseModel):
    status: str
    amount_saved: Optional[float] = None

    @validator('status')
    def status_must_be_valid(cls, v):
        valid_statuses = ["available", "used", "dismissed"]
        if v not in valid_statuses:
            raise ValueError(f"Status must be one of: {', '.join(valid_statuses)}")
        return v

# --- Alert Schema ---
class AlertOffer(OfferBase):
    offer_id: int
    card: CardForAlert
    model_config = ConfigDict(from_attributes=True)

# --- Card Schemas ---
class CardBase(BaseModel):
    card_nickname: str = Field(..., min_length=1, max_length=50, description="Card nickname")
    bank_name: str = Field(..., min_length=1, max_length=100, description="Bank name")
    last_four_digits: str = Field(..., pattern=r'^\d{4}$')
    
    @validator('card_nickname', 'bank_name')
    def names_must_not_be_empty(cls, v):
        if not v.strip():
            raise ValueError('Field cannot be empty')
        return v.strip()

class CardCreate(CardBase):
    user_id: int = Field(..., gt=0, description="The ID of the user who owns the card")

class Card(CardBase):
    card_id: int
    owner_id: int
    created_at: datetime
    updated_at: datetime
    offers: List[Offer] = []
    model_config = ConfigDict(from_attributes=True)

# --- Preferences Schemas ---
class PreferencesBase(BaseModel):
    digest_day: str = Field(..., pattern=r'^(Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday)$')
    
    @validator('digest_day')
    def validate_day(cls, v):
        valid_days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        if v not in valid_days:
            raise ValueError(f'Day must be one of: {", ".join(valid_days)}')
        return v

class PreferencesUpdate(PreferencesBase):
    pass

class Preferences(PreferencesBase):
    pref_id: int
    user_id: int
    model_config = ConfigDict(from_attributes=True)

# --- User Schemas ---
class UserBase(BaseModel):
    email: str = Field(..., pattern=r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
    username: str = Field(..., min_length=3, max_length=30, pattern=r'^[a-zA-Z0-9_]+$')
    
    @validator('email')
    def validate_email_format(cls, v):
        if not v.strip():
            raise ValueError('Email cannot be empty')
        return v.lower().strip()
    
    @validator('username')
    def validate_username(cls, v):
        if not v.strip():
            raise ValueError('Username cannot be empty')
        return v.strip()

class UserCreate(UserBase):
    firebase_uid: str = Field(..., min_length=1, max_length=128)
    
    @validator('firebase_uid')
    def validate_firebase_uid(cls, v):
        if not v.strip():
            raise ValueError('Firebase UID cannot be empty')
        return v.strip()

class User(UserBase):
    user_id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime
    cards: List[Card] = []
    preferences: Optional[Preferences] = None
    model_config = ConfigDict(from_attributes=True)

# --- Smart Spend Analytics Schemas ---
class AnalyticsUser(BaseModel):
    user_id: int
    username: str
    total_cards: int

class TopMerchant(BaseModel):
    merchant: str
    total: float

class Recommendation(BaseModel):
    action: str
    message: str
    merchant: Optional[str] = None
    total_spent: Optional[float] = None

class SmartSpendAnalytics(BaseModel):
    user: AnalyticsUser
    top_merchants: List[TopMerchant]
    recommendations: List[Recommendation]
    preferences: Dict[str, Any]

# --- Additional Response Schemas ---
class SuccessResponse(BaseModel):
    message: str
    data: Optional[Dict[Any, Any]] = None

class ErrorResponse(BaseModel):
    detail: str
    error_code: Optional[str] = None

# --- Bulk Operations Schemas ---
class BulkOfferCreate(BaseModel):
    offers: List[OfferCreate] = Field(..., min_items=1, max_items=50)
    
    @validator('offers')
    def validate_offers_not_empty(cls, v):
        if not v:
            raise ValueError('At least one offer is required')
        return v

# --- Smart Spend Schemas ---
class SmartSpendQuery(BaseModel):
    user_id: int
    query: str = Field(..., min_length=3, max_length=200)

class SmartSpendResponse(BaseModel):
    recommendation: str
    explanation: str
