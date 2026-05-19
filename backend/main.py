from fastapi import FastAPI, Request, Depends, Body
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
import os
from database import engine, Base, get_db
import models

Base.metadata.create_all(bind=engine)

app = FastAPI(title="SkillMatch AI v4", version="4.0.0", docs_url="/api/docs")

app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
static_dir = os.path.join(BASE_DIR, "static")
templates_dir = os.path.join(BASE_DIR, "templates")
os.makedirs(static_dir, exist_ok=True)
os.makedirs(templates_dir, exist_ok=True)

app.mount("/static", StaticFiles(directory=static_dir), name="static")
templates = Jinja2Templates(directory=templates_dir)
templates.env.variable_start_string = '(('
templates.env.variable_end_string = '))'

# Routers
from .routers import candidates, positions, analytics, applications, interviews, offers, onboarding, auth
app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(candidates.router, prefix="/api/candidates", tags=["candidates"])
app.include_router(positions.router, prefix="/api/positions", tags=["positions"])
app.include_router(analytics.router, prefix="/api/analytics", tags=["analytics"])
app.include_router(applications.router, prefix="/api/applications", tags=["applications"])
app.include_router(interviews.router, prefix="/api/interviews", tags=["interviews"])
app.include_router(offers.router, prefix="/api/offers", tags=["offers"])
app.include_router(onboarding.router, prefix="/api/onboarding", tags=["onboarding"])

from .services.chatbot import chatbot_service
@app.post("/api/chat")
def chat_endpoint(message: str = Body(..., embed=True), db: Session = Depends(get_db)):
    return {"response": chatbot_service.chat(message, db)}

@app.get("/health")
def health(): return {"status": "ok", "version": "4.0.0"}

@app.get("/", response_class=HTMLResponse)
def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})
