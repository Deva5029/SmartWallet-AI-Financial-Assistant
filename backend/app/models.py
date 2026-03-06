from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, DateTime, Numeric
from sqlalchemy.orm import relationship
from .database import Base
from datetime import datetime

class User(Base):
    __tablename__ = "app_users"

    user_id = Column(Integer, primary_key=True, index=True)
    firebase_uid = Column(String, unique=True, index=True, nullable=False)
    username = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active = Column(Boolean, default=True)

    cards = relationship("CreditCard", back_populates="owner", cascade="all, delete-orphan")
    preferences = relationship("UserPreferences", back_populates="user", uselist=False, cascade="all, delete-orphan")

class UserPreferences(Base):
    __tablename__ = "user_preferences"

    pref_id = Column(Integer, primary_key=True, index=True)
    digest_day = Column(String, default="Sunday")
    user_id = Column(Integer, ForeignKey("app_users.user_id"), unique=True, nullable=False)
    user = relationship("User", back_populates="preferences")

class CreditCard(Base):
    __tablename__ = "credit_cards"

    card_id = Column(Integer, primary_key=True, index=True)
    card_nickname = Column(String, index=True, nullable=False)
    bank_name = Column(String, nullable=False)
    last_four_digits = Column(String(4), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    owner_id = Column(Integer, ForeignKey("app_users.user_id"), nullable=False)
    owner = relationship("User", back_populates="cards")
    offers = relationship("CardOffer", back_populates="card", cascade="all, delete-orphan")

class CardOffer(Base):
    __tablename__ = "card_offers"

    offer_id = Column(Integer, primary_key=True, index=True)
    description = Column(String, nullable=False)
    expiry_date = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    status = Column(String(50), default="available", nullable=False)
    
    # --- MODIFIED: This column stores the currency value of the savings ---
    amount_saved = Column(Numeric(10, 2), nullable=True)

    card_id = Column(Integer, ForeignKey("credit_cards.card_id"), nullable=False)
    card = relationship("CreditCard", back_populates="offers")

