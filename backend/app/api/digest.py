from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app import crud, schemas
from app.database import get_db
from pydantic import BaseModel
import os
import json
import httpx
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import random

router = APIRouter()

# Response model that matches frontend expectations
class WeeklyDigest(BaseModel):
    subject: str
    body: str
    generated_at: datetime = None
    user_id: int = None

# Optional: external AI configuration
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "").strip()
GEMINI_API_URL = os.getenv("GEMINI_API_URL", "").strip()

@router.get("/{user_id}", response_model=WeeklyDigest)
async def get_user_digest(user_id: int, db: Session = Depends(get_db)):
    """
    Generate a personalized weekly digest for the user.
    Returns formatted digest with subject and body that frontend expects.
    """
    try:
        # Get user data
        user = crud.get_user(db, user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        # Get user preferences for personalization
        preferences = None
        if hasattr(crud, "get_user_preferences"):
            try:
                preferences = crud.get_user_preferences(db, user_id)
            except:
                preferences = None

        # Get expiring offers
        expiring_offers = []
        try:
            expiring_offers = crud.get_expiring_offers_for_user(db, user_id)
        except:
            pass

        # Generate digest content
        if GEMINI_API_KEY and GEMINI_API_URL:
            digest_content = await _generate_ai_digest(user, expiring_offers, preferences)
        else:
            digest_content = _generate_local_digest(user, expiring_offers, preferences)

        # Create subject line
        current_date = datetime.now()
        week_of = current_date.strftime("%B %d, %Y")
        subject = f"Your SmartWallet Weekly Digest - Week of {week_of}"

        return WeeklyDigest(
            subject=subject,
            body=digest_content,
            generated_at=current_date,
            user_id=user_id
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating digest: {str(e)}")

async def _generate_ai_digest(user, expiring_offers: List, preferences) -> str:
    """Generate digest using external AI service"""
    
    # Prepare context for AI
    context = {
        "user": {
            "username": user.username,
            "total_cards": len(user.cards) if user.cards else 0,
            "total_offers": sum(len(card.offers) for card in user.cards) if user.cards else 0
        },
        "expiring_offers": [],
        "preferences": {}
    }

    # Add expiring offers
    for offer in expiring_offers[:5]:  # Limit to top 5
        context["expiring_offers"].append({
            "description": getattr(offer, "description", "Unknown offer"),
            "expiry_date": getattr(offer, "expiry_date", datetime.now()).strftime("%B %d, %Y"),
            "card_name": getattr(offer.card, "card_nickname", "Unknown card") if hasattr(offer, "card") else "Unknown card"
        })

    # Add preferences
    if preferences:
        context["preferences"]["digest_day"] = getattr(preferences, "digest_day", "Sunday")

    # Prepare AI prompt
    prompt = f"""
    Create a personalized weekly digest for {user.username}. Here's their data:
    
    Cards: {context['user']['total_cards']} cards with {context['user']['total_offers']} total offers
    
    Expiring offers: {json.dumps(context['expiring_offers'], indent=2) if context['expiring_offers'] else 'None'}
    
    Please create a friendly, helpful digest that includes:
    1. A warm greeting
    2. Summary of their wallet status
    3. Urgent expiring offers (if any)
    4. Best current offers by card
    5. A practical weekly tip
    6. Encouraging closing
    
    Keep it under 300 words and format as plain text paragraphs.
    """

    try:
        payload = {
            "prompt": prompt,
            "max_tokens": 500,
            "temperature": 0.7
        }
        headers = {
            "Authorization": f"Bearer {GEMINI_API_KEY}",
            "Content-Type": "application/json"
        }

        async with httpx.AsyncClient(timeout=20.0) as client:
            resp = await client.post(GEMINI_API_URL, json=payload, headers=headers)
            
            if resp.status_code == 200:
                result = resp.json()
                # Extract content based on common AI response formats
                if isinstance(result, dict):
                    content = (
                        result.get("content") or
                        result.get("text") or
                        result.get("generated_text") or
                        str(result)
                    )
                else:
                    content = str(result)
                
                return content.strip()
            else:
                # Fallback to local generation
                return _generate_local_digest(user, expiring_offers, preferences)

    except Exception as e:
        print(f"AI digest generation failed: {e}")
        # Fallback to local generation
        return _generate_local_digest(user, expiring_offers, preferences)

def _generate_local_digest(user, expiring_offers: List, preferences) -> str:
    """Generate digest using local templates and logic"""
    
    content_parts = []
    
    # Greeting
    greetings = [
        f"Hello {user.username}! Here's your weekly SmartWallet summary.",
        f"Hi {user.username}! Time for your weekly wallet check-in.",
        f"Hey {user.username}! Let's review your week in smart spending."
    ]
    content_parts.append(random.choice(greetings))
    content_parts.append("")

    # Wallet overview
    total_cards = len(user.cards) if user.cards else 0
    total_offers = sum(len(card.offers) for card in user.cards) if user.cards else 0
    
    content_parts.append("WALLET OVERVIEW")
    content_parts.append(f"You currently have {total_cards} card(s) in your wallet with {total_offers} active offer(s) ready to use.")
    content_parts.append("")

    # Expiring offers section
    if expiring_offers:
        content_parts.append("EXPIRING SOON - ACTION NEEDED!")
        for offer in expiring_offers[:3]:  # Top 3 most urgent
            card_name = getattr(offer.card, "card_nickname", "Unknown card") if hasattr(offer, "card") else "Unknown card"
            expiry = getattr(offer, "expiry_date", datetime.now())
            days_left = (expiry - datetime.now()).days
            
            if days_left <= 0:
                urgency = "expires today!"
            elif days_left == 1:
                urgency = "expires tomorrow!"
            else:
                urgency = f"expires in {days_left} days"
            
            content_parts.append(f"• {getattr(offer, 'description', 'Offer')} on your {card_name} - {urgency}")
        content_parts.append("")

    # Best offers by card
    if user.cards:
        content_parts.append("YOUR BEST ACTIVE OFFERS")
        for card in user.cards[:3]:  # Top 3 cards
            if card.offers:
                best_offer = card.offers[0]  # First offer (could be sorted by value in production)
                content_parts.append(f"• {card.card_nickname}: {best_offer.description}")
        content_parts.append("")

    # Weekly tip
    content_parts.append("WEEKLY SMART TIP")
    tips = [
        "Check your offers before making any purchase to maximize rewards.",
        "Set phone reminders for offers that expire within the next week.",
        "Use different cards for different spending categories to optimize rewards.",
        "Review your monthly credit card statements to track your reward earnings.",
        "Take a photo of new offers immediately so you don't forget about them.",
        "Consider setting up automatic payments to never miss earning rewards due to late fees.",
        "Check for limited-time promotional offers from your credit card companies monthly."
    ]
    content_parts.append(random.choice(tips))
    content_parts.append("")

    # Personalized preference note
    if preferences and hasattr(preferences, "digest_day"):
        day = preferences.digest_day
        content_parts.append(f"Your digest is currently scheduled for {day}s. You can change this in your settings anytime.")
        content_parts.append("")

    # Closing
    closings = [
        "Happy saving!",
        "Make every purchase count!",
        "Here's to smarter spending!",
        "Your AI co-pilot is always here to help!"
    ]
    content_parts.append(random.choice(closings))
    content_parts.append("")
    content_parts.append("- Your SmartWallet Team")

    return "\n".join(content_parts)

# Additional endpoint for digest preview (useful for testing)
@router.get("/{user_id}/preview")
async def preview_digest(user_id: int, db: Session = Depends(get_db)):
    """Generate a digest preview without full AI processing"""
    try:
        user = crud.get_user(db, user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        expiring_offers = []
        try:
            expiring_offers = crud.get_expiring_offers_for_user(db, user_id)
        except:
            pass

        preview_content = _generate_local_digest(user, expiring_offers, None)
        
        return {
            "preview": preview_content[:200] + "...",  # First 200 chars
            "full_length": len(preview_content),
            "expiring_offers_count": len(expiring_offers),
            "total_cards": len(user.cards) if user.cards else 0
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating preview: {str(e)}")