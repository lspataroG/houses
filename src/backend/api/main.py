"""FastAPI application for HouseHunter."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .routes import listings, images, user_state

app = FastAPI(
    title="HouseHunter API",
    description="Real estate listing API",
    version="1.0.0"
)

# CORS middleware for frontend development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(listings.router)
app.include_router(images.router)
app.include_router(user_state.router)


@app.get("/")
async def root():
    """Health check endpoint."""
    return {"status": "ok", "service": "HouseHunter API"}
