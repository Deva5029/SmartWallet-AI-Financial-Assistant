We built this using a Microservices-lite architecture. Here is what we used for every layer of the stack:

1. The Infrastructure (Docker & Docker Compose)
Instead of installing Python and Node directly on your computer (which can cause "it works on my machine" errors), we used Docker.

Dockerfile: We created two of these—one for the backend and one for the frontend. They act as "recipes" to build an isolated environment.

Docker Compose: This is the "Conductor." It coordinates the three separate containers (Frontend, Backend, and Database) so they can talk to each other over a private virtual network.

2. The Database (PostgreSQL)
We chose PostgreSQL because it is a professional-grade relational database.

Persistence: We used "Docker Volumes" so that even if you turn off the app, your users and credit cards are saved.

SQLAlchemy (ORM): In the backend, we used SQLAlchemy. This allowed us to write Python code to interact with the database instead of raw SQL queries.

3. The Backend (FastAPI & Python 3.10)
This is the "brain" of your application.

FastAPI: A high-performance web framework. We used this to create the REST API endpoints (/users, /cards, /ocr, etc.).

Pydantic: This was used for Data Validation. It ensured that when the frontend sent a "date," it was actually a date, or the backend would reject it with a 422 error.

Uvicorn: The lightning-fast server that runs the Python code inside the container.

4. The AI Intelligence (Google Gemini API)
This is the "killer feature" of your wallet.

Gemini 1.5 Flash: We integrated Google's latest model.

OCR Logic: Instead of old-fashioned text extraction, Gemini looks at your Bank of America screenshots, understands the visual layout, and extracts merchant names and expiry dates automatically.

Smart Spend Co-Pilot: Gemini reads your entire wallet and compares it against your purchase intent (e.g., "I'm buying groceries") to find the best reward.

5. The Frontend (React.js)
The "face" of the application.

React: Used to build a "Single Page Application" (SPA). This makes the app feel fast because the page never fully reloads.

Axios: The library used to send data to your FastAPI backend.

CSS Animations: We used @keyframes to create the "Cyberpunk" glowing UI and the smooth slide-in panels for the AI Co-Pilot.
