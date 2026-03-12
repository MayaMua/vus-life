"""
FastAPI application entry point.

Configures CORS for Electron desktop app compatibility.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.endpoints import settings, vus

app = FastAPI(
    title="VUS Life Backend API",
    description="Backend API for VUS Life desktop application",
    version="1.0.0",
)

# Configure CORS for Electron compatibility
# Electron runs on localhost:5173 (dev) or file:// (prod)
# FastAPI runs on localhost:18000
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for Electron compatibility
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routers
app.include_router(settings.router, prefix="/api/settings", tags=["settings"])
app.include_router(vus.router, prefix="/api/vus", tags=["vus"])



@app.get("/")
async def root():
    """Root endpoint."""
    return {"message": "VUS Life Backend API", "version": "1.0.0"}


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "ok"}
