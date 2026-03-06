from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.database import engine, Base
from app.api import users, cards, offers, ocr, smart_spend, alerts, digest, preferences

# This command ensures that all tables are created in the database
Base.metadata.create_all(bind=engine)

app = FastAPI(title="AI-SmartWallet API")

# Configure CORS (your new configuration is better and more secure)
origins = ["http://localhost:3000"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include the API routers
app.include_router(users.router, prefix="/users", tags=["Users"])
app.include_router(cards.router, prefix="/cards", tags=["Cards"])
app.include_router(offers.router, prefix="/offers", tags=["Offers"])
app.include_router(alerts.router, prefix="/alerts", tags=["Alerts"])
app.include_router(ocr.router, prefix="/ocr", tags=["OCR"])
app.include_router(smart_spend.router, prefix="/smart_spend", tags=["Smart Spend"]) # Minor change for consistency
app.include_router(digest.router, prefix="/digest", tags=["Digest"])
app.include_router(preferences.router, prefix="/preferences", tags=["Preferences"])

@app.get("/")
def read_root():
    return {"message": "Welcome to the AI-SmartWallet API"}