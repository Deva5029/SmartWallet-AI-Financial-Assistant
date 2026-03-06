from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app import crud, schemas
from app.database import get_db
import os
import google.generativeai as genai
import json

router = APIRouter()

# Check if the Gemini API key is available
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

@router.post("/analyze", response_model=schemas.SmartSpendResponse)
async def analyze_spend_and_recommend(query: schemas.SmartSpendQuery, db: Session = Depends(get_db)):
    """
    Analyzes a user's spending query and recommends the best card to use using Gemini.
    """
    if not GEMINI_API_KEY:
        raise HTTPException(status_code=500, detail="Gemini API key not configured on server.")

    user = crud.get_user(db, user_id=query.user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")
    
    if not user.cards:
        return schemas.SmartSpendResponse(
            recommendation="Add a card first!",
            explanation="You don't have any cards in your wallet. Add one to get started."
        )

    wallet_summary = ""
    for card in user.cards:
        wallet_summary += f"Card: '{card.card_nickname}' ({card.bank_name} **** {card.last_four_digits})\n"
        if card.offers:
            for offer in card.offers:
                wallet_summary += f"- Offer: {offer.description}\n"
        else:
            wallet_summary += "- No active offers.\n"
        wallet_summary += "\n"

    model = genai.GenerativeModel('gemini-1.5-flash')
    prompt = f"""
    You are a "Smart Spend AI Co-Pilot". Your goal is to help a user choose the best credit card from their wallet for a specific purchase.

    Here is the user's current wallet summary:
    ---
    {wallet_summary}
    ---

    The user wants to make the following purchase: "{query.query}"

    Analyze the user's query and their available cards and offers. Your task is to provide a recommendation in a clean JSON format.

    Your response MUST be a JSON object with two keys:
    1. "recommendation": A short, direct recommendation of which card to use (e.g., "Use your Bofa Rewards card.").
    2. "explanation": A one or two-sentence explanation for your choice, highlighting the specific offer or benefit that makes it the best option.

    Do not include any other text or markdown formatting.
    """

    safety_settings = {
        'HARM_CATEGORY_HARASSMENT': 'BLOCK_NONE',
        'HARM_CATEGORY_HATE_SPEECH': 'BLOCK_NONE',
        'HARM_CATEGORY_SEXUALLY_EXPLICIT': 'BLOCK_NONE',
        'HARM_CATEGORY_DANGEROUS_CONTENT': 'BLOCK_NONE',
    }

    try:
        response = await model.generate_content_async(prompt, safety_settings=safety_settings)

        if not response.parts:
            print(f"Gemini response was blocked. Feedback: {response.prompt_feedback}")
            raise HTTPException(status_code=500, detail="The AI's response was blocked by safety filters.")

        # --- THIS IS THE FIX ---
        # This new logic robustly extracts the JSON from the AI's response,
        # even if it's wrapped in markdown code blocks.
        raw_text = response.text
        json_start_index = raw_text.find('{')
        json_end_index = raw_text.rfind('}') + 1

        if json_start_index != -1 and json_end_index != 0:
            json_string = raw_text[json_start_index:json_end_index]
            result = json.loads(json_string)
            return result
        else:
            # This will be triggered if no JSON object is found in the response
            raise json.JSONDecodeError("Could not find a valid JSON object in the AI response.", raw_text, 0)
        
    except json.JSONDecodeError:
        print(f"Gemini returned non-JSON response: {response.text}")
        raise HTTPException(status_code=500, detail="AI returned an invalid format.")
    except Exception as e:
        print(f"An unhandled error occurred calling Gemini: {e}")
        raise HTTPException(status_code=500, detail="Failed to get a recommendation from the AI.")

# --- We are keeping your existing analytics endpoint ---
@router.get("/{user_id}", response_model=schemas.SmartSpendAnalytics)
def get_smart_spend_analytics(user_id: int, db: Session = Depends(get_db)):
    user = crud.get_user(db, user_id=user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    top_merchants = [] 
    recommendations = [{"action": "review_offers", "message": "Regularly check for new offers to maximize rewards."}]
    
    preferences = {}
    if user.preferences:
        preferences["digest_day"] = user.preferences.digest_day

    return schemas.SmartSpendAnalytics(
        user={"user_id": user.user_id, "username": user.username, "total_cards": len(user.cards)},
        top_merchants=top_merchants,
        recommendations=recommendations,
        preferences=preferences
    )