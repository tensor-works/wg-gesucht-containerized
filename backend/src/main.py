from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.v1 import settings

app = FastAPI(
    title="WG Gesucht Backend",
    description="Backend for WG Gesucht application",
    version="1.0.0",
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust for production (e.g., allow specific origins only)
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routes
app.include_router(settings.router, prefix="/api/v1/settings")

# Root endpoint
@app.get("/")
def health_check():
    return {"message": "Backend is running!"}

# Run the application using: uvicorn src.main:app --reload
