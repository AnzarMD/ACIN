"""ACIN Backend — FastAPI Main Application.

Amazon Circular Intelligence Network
AI-Powered Multi-Agent Returns & Sustainable Resale Platform
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api import returns, products, analytics, buyers

app = FastAPI(
    title="ACIN API",
    version="1.0.0",
    description="Amazon Circular Intelligence Network — Multi-Agent Returns Platform",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://acin.vercel.app",
        "http://localhost:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(returns.router, prefix="/v1/returns", tags=["Returns"])
app.include_router(products.router, prefix="/v1/products", tags=["Products"])
app.include_router(analytics.router, prefix="/v1/analytics", tags=["Analytics"])
app.include_router(buyers.router, prefix="/v1/buyers", tags=["Buyers"])


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "ok", "service": "acin-backend", "version": "1.0.0"}


@app.get("/")
async def root():
    """API root — service info."""
    return {
        "service": "Amazon Circular Intelligence Network (ACIN)",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health",
    }
