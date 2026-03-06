from fastapi import APIRouter, UploadFile, File, HTTPException
from pydantic import BaseModel, ValidationError
from typing import List
from datetime import datetime, timedelta
import os
import google.generativeai as genai
import json
from dotenv import load_dotenv

# --- Configuration & Setup ---
load_dotenv()
router = APIRouter()

try:
    genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
except Exception as e:
    print(f"WARNING: Gemini API key not configured. The OCR endpoint will fail. {e}")

# --- Pydantic Models ---
class ScannedOffer(BaseModel):
    description: str
    expiry_date: str
    category: str # NEW FIELD

class ScanOffersResponse(BaseModel):
    offers: List[ScannedOffer]

# --- Self-Correction Function for Dates ---
async def correct_invalid_date(invalid_date_str: str, model):
    """Asks the AI to correct a date string it previously generated incorrectly."""
    try:
        correction_prompt = f"""
        The date '{invalid_date_str}' is invalid. Please correct this date to a valid calendar date in 'YYYY-MM-DD' format. 
        For example, if the month does not have the specified day, provide the last valid day of that month.
        Only return the corrected date string, with no other text.
        """
        response = await model.generate_content_async(correction_prompt)
        corrected_date = response.text.strip()
        datetime.strptime(corrected_date, "%Y-%m-%d")
        return corrected_date
    except (ValueError, Exception) as e:
        print(f"Failed to correct date '{invalid_date_str}': {e}. Defaulting to 30 days from now.")
        return (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d")

# --- API Endpoint ---
@router.post("/scan-offers", response_model=ScanOffersResponse)
async def scan_offers_with_gemini(files: List[UploadFile] = File(...)):
    if not os.getenv("GEMINI_API_KEY"):
        raise HTTPException(status_code=500, detail="GEMINI_API_KEY environment variable not set.")

    model = genai.GenerativeModel('gemini-1.5-flash')
    
    # --- PROMPT MODIFIED ---
    prompt_parts = [
        f"""
        You are an expert financial data extraction assistant. Analyze the provided screenshots of credit card offers.
        For each distinct offer, extract the following information:
        1.  'description': The full text of the offer.
        2.  'expiry_date': The date the offer expires.
        3.  'category': Classify the offer into one of the following categories: "Food & Dining", "Shopping", "Travel", "Entertainment", "Services", or "General".

        Instructions for 'expiry_date':
        - If you see "X days left", calculate the future date from today ({datetime.now().strftime("%Y-%m-%d")}) and format as 'YYYY-MM-DD'.
        - If a specific date is mentioned, normalize it to 'YYYY-MM-DD'.
        - If no date is found, calculate a date 30 days from today.

        Compile a single list of all unique offers. Provide the output as a single, clean JSON object with one key "offers".
        """
    ]

    for file in files:
        if not file.content_type or not file.content_type.startswith("image/"):
            raise HTTPException(status_code=400, detail=f"File '{file.filename}' is not a valid image.")
        
        image_bytes = await file.read()
        prompt_parts.append({"mime_type": file.content_type, "data": image_bytes})

    try:
        response = await model.generate_content_async(prompt_parts)
        
        raw_text = response.text
        json_start_index = raw_text.find('{')
        json_end_index = raw_text.rfind('}') + 1

        if json_start_index != -1 and json_end_index != 0:
            json_string = raw_text[json_start_index:json_end_index]
            parsed_response = json.loads(json_string)

            validated_offers = []
            for offer_data in parsed_response.get("offers", []):
                try:
                    datetime.strptime(offer_data["expiry_date"], "%Y-%m-%d")
                    # Ensure a category exists, defaulting if not provided by the AI
                    offer_data.setdefault("category", "General")
                    validated_offers.append(offer_data)
                except ValueError:
                    print(f"Invalid date '{offer_data['expiry_date']}' found. Attempting self-correction...")
                    corrected_date = await correct_invalid_date(offer_data["expiry_date"], model)
                    offer_data["expiry_date"] = corrected_date
                    offer_data.setdefault("category", "General")
                    validated_offers.append(offer_data)
            
            parsed_response["offers"] = validated_offers
            return ScanOffersResponse(**parsed_response)
        else:
            raise json.JSONDecodeError("Could not find a valid JSON object in the AI response.", raw_text, 0)

    except (json.JSONDecodeError, ValidationError, Exception) as e:
        print(f"An error occurred processing the Gemini API response: {e}")
        raise HTTPException(status_code=500, detail="Failed to process offers from scanned images.")

