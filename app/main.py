"""
FastAPI main application entry point
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import apply, evidence, jd, parse, rewrite, test_roundtrip

app = FastAPI(title="ATS-Approved", version="0.1.0")

# Add CORS middleware for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Next.js dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(parse.router)
app.include_router(test_roundtrip.router)
app.include_router(jd.router)
app.include_router(evidence.router)
app.include_router(rewrite.router)
app.include_router(apply.router)  


@app.get("/")
async def root():
    return {"message": "ATS-Approved API", "status": "ok"}


@app.get("/health")
async def health():
    return {"status": "healthy"}

