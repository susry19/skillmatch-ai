from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.orm import Session
from typing import List
from .. import models, schemas, database

router = APIRouter()

@router.post("/", response_model=schemas.Position)
def create_position(position: schemas.PositionCreate, db: Session = Depends(database.get_db)):
    db_position = models.Position(**position.dict())
    db.add(db_position)
    db.commit()
    db.refresh(db_position)
    return db_position

@router.get("/", response_model=List[schemas.Position])
def read_positions(skip: int = 0, limit: int = 100, db: Session = Depends(database.get_db)):
    positions = db.query(models.Position).offset(skip).limit(limit).all()
    return positions

@router.get("/{position_id}", response_model=schemas.Position)
def read_position(position_id: int, db: Session = Depends(database.get_db)):
    position = db.query(models.Position).filter(models.Position.id == position_id).first()
    if position is None:
        raise HTTPException(status_code=404, detail="Position not found")
    return position

@router.get("/{position_id}/matches", response_model=List[schemas.CandidateMatch])
def match_candidates(position_id: int, db: Session = Depends(database.get_db)):
    from ..services.matcher import matcher_service
    matches = matcher_service.match_candidates(position_id, db)
    return matches

@router.post("/feedback")
def receive_feedback(feedback: schemas.FeedbackCreate, db: Session = Depends(database.get_db)):
    """Receives feedback signals for the learning engine."""
    from ..services.semantic_matcher import semantic_matcher
    
    # Verify existence (optional but accurate)
    candidate = db.query(models.Candidate).filter(models.Candidate.id == feedback.candidate_id).first()
    position = db.query(models.Position).filter(models.Position.id == feedback.position_id).first()
    
    if not candidate or not position:
        raise HTTPException(status_code=404, detail="Candidate or Position not found")
        
    if feedback.signal_type == "positive":
        # Learn from Skills
        for skill in (candidate.skills or []):
            semantic_matcher.update_signal("positive", "skill", skill)
        # Learn from Seniority
        if candidate.seniority_level:
            semantic_matcher.update_signal("positive", "seniority", candidate.seniority_level)
            
    elif feedback.signal_type == "negative":
        # Negative reinforcement is tricky, maybe just don't boost these next time?
        # For now, let's just record it potentially.
        if candidate.seniority_level:
            semantic_matcher.update_signal("negative", "seniority", candidate.seniority_level)
            
    return {"status": "success", "message": "Feedback received"}

@router.get("/salary-suggestion")
def get_salary_suggestion(title: str, location: str = "Türkiye"):
    from ..services.salary_service import salary_service
    return salary_service.get_market_salary(title, location)

@router.post("/analyze")
def analyze_position(payload: dict = Body(...)):
    """
    Consolidated endpoint to generate Job Specs (Desc/Skills) AND Salary Suggestion.
    """
    title = payload.get("title")
    if not title:
        return {"error": "Title is required"}
        
    # 1. Generate Content (Description, Skills, AND Salary)
    from ..services.ai_job_generator import ai_job_generator
    specs = ai_job_generator.generate_job_specs(title)
        
    return {
        "description": specs.get("description", ""),
        "skills": specs.get("skills", []),
        "salary": specs.get("salary", None)
    }
