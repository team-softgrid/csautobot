import os
import sys
from pathlib import Path
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

# Add current directory to path
HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

load_dotenv(HERE.parent / ".env")
load_dotenv(HERE / ".env")

app = FastAPI(
    title="CSAutobot API Server",
    description="AS RAG Search and EV Charger Inspection API",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Imports router after path setup
from app.routes.search import router as search_router
from app.routes.inspection import router as inspection_router
from app.routes.dashboard import router as dashboard_router
from app.routes.feedback import router as feedback_router
from app.routes.quotation import router as quotation_router
from app.routes.auth import router as auth_router
from auth_db import init_auth_db

app.include_router(search_router, prefix="/api/v1")
app.include_router(inspection_router, prefix="/api/v1")
app.include_router(dashboard_router, prefix="/api/v1")
app.include_router(feedback_router, prefix="/api/v1")
app.include_router(quotation_router, prefix="/api/v1")
app.include_router(auth_router, prefix="/api/v1")

@app.on_event("startup")
def on_startup():
    init_auth_db()

@app.get("/")
def read_root():
    return {"status": "online", "service": "CSAutobot API Server"}

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
