import os
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .routers import auth, diagnosis, reports

load_dotenv()
app = FastAPI(title="AI Scaling Up Advisor")

# CORS for local dev frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router, prefix="/api/auth", tags=["auth"]) 
app.include_router(diagnosis.router, prefix="/api/diagnosis", tags=["diagnosis"]) 
app.include_router(reports.router, prefix="/api/reports", tags=["reports"]) 

@app.get("/api/health")
def health():
    return {"status": "ok"}

@app.get("/")
def index():
    return {"message": "AI Scaling Up Advisor API. Usa /docs para explorar los endpoints."}
