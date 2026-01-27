"""
FastAPI main application entry point
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import apply, jd, parse, test_roundtrip

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
app.include_router(apply.router)

# Include evidence and rewrite routers
try:
    from app.api import evidence, rewrite
    app.include_router(evidence.router)
    app.include_router(rewrite.router)
    print("✓ Evidence and rewrite routers loaded")
except ImportError as e:
    print(f"⚠ Warning: Could not load evidence/rewrite routers: {e}")
except Exception as e:
    print(f"⚠ Warning: Error loading routers: {e}")


@app.get("/")
async def root():
    return {"message": "ATS-Approved API", "status": "ok"}


@app.get("/health")
async def health():
    return {"status": "healthy"}

