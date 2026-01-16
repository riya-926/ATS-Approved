"""
FastAPI main application entry point
"""
from fastapi import FastAPI

from app.api import jd, parse, test_roundtrip

app = FastAPI(title="ATS-Approved", version="0.1.0")

# Include routers
app.include_router(parse.router)
app.include_router(test_roundtrip.router)
app.include_router(jd.router)


@app.get("/")
async def root():
    return {"message": "ATS-Approved API", "status": "ok"}


@app.get("/health")
async def health():
    return {"status": "healthy"}

