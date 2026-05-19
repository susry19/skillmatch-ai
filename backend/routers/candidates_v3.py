from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List
import json
import models, schemas, database
fromservices import pdf_parser, ai_analyzer

router = APIRouter()

def process_cv_background(file_content: bytes, filename: str, db: Session):
    # 1. Extract Text
    text = pdf_parser.extract_text_from_pdf(file_content)
    
    # 2. AI Analysis
    analysis = ai_analyzer.analyze_cv(text)
    
    # 3. Save to DB
    db_candidate = models.Candidate(
        name=analysis.get("name", "Unknown"),
        email=analysis.get("email"),
        phone=analysis.get("phone"),
        summary=analysis.get("summary"),
        skills=analysis.get("skills", []),
        experience=analysis.get("experience", []),
        education=analysis.get("education", []),
        certifications=analysis.get("certifications", []),
        projects=analysis.get("projects", []),
        seniority_level=analysis.get("seniority_level"),
        seniority_score=analysis.get("seniority_score"),
        strengths=analysis.get("strengths", []),
        areas_for_improvement=analysis.get("areas_for_improvement", []),
        original_filename=filename,
        upload_status="Completed"
    )
    db.add(db_candidate)
    db.commit()
    db.refresh(db_candidate)

@router.post("/upload", response_model=schemas.Candidate)
async def upload_cv(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...), 
    db: Session = Depends(database.get_db)
):
    content = await file.read()
    
    # Create initial record
    db_candidate = models.Candidate(
        name="Processing...",
        original_filename=file.filename,
        upload_status="Processing"
    )
    db.add(db_candidate)
    db.commit()
    db.refresh(db_candidate)
    
    # Run processing in background (simulated for now, but ideally we'd pass the ID to update)
    # Since we can't easily pass the DB session to background task in this simple setup without scope issues,
    # we will do it synchronously for this demo or use a better pattern.
    # For "Pro" feel, let's do synchronous for immediate feedback on small files, 
    # or better: update the record we just created.
    
    # Re-implementing synchronously for simplicity and reliability in this demo context
    # In a real app, use Celery or proper background task with new DB session.
    
    text = pdf_parser.extract_text_from_pdf(content)
    analysis = ai_analyzer.analyze_cv(text)
    
    db_candidate.name = analysis.get("name", "Unknown")
    db_candidate.email = analysis.get("email")
    db_candidate.phone = analysis.get("phone")
    db_candidate.summary = analysis.get("summary")
    db_candidate.skills = analysis.get("skills", [])
    db_candidate.experience = analysis.get("experience", [])
    db_candidate.education = analysis.get("education", [])
    db_candidate.certifications = analysis.get("certifications", [])
    db_candidate.projects = analysis.get("projects", [])
    db_candidate.seniority_level = analysis.get("seniority_level")
    db_candidate.seniority_score = analysis.get("seniority_score")
    db_candidate.strengths = analysis.get("strengths", [])
    db_candidate.areas_for_improvement = analysis.get("areas_for_improvement", [])
    db_candidate.upload_status = "Completed"
    
    db.commit()
    db.refresh(db_candidate)
    
    return db_candidate

@router.get("/", response_model=List[schemas.Candidate])
def read_candidates(skip: int = 0, limit: int = 100, db: Session = Depends(database.get_db)):
    candidates = db.query(models.Candidate).offset(skip).limit(limit).all()
    return candidates

@router.get("/{candidate_id}", response_model=schemas.Candidate)
def read_candidate(candidate_id: int, db: Session = Depends(database.get_db)):
    candidate = db.query(models.Candidate).filter(models.Candidate.id == candidate_id).first()
    if candidate is None:
        raise HTTPException(status_code=404, detail="Candidate not found")
    return candidate

@router.post("/compare", response_model=schemas.CandidateComparisonResponse)
def compare_candidates(request: schemas.CandidateComparisonRequest, db: Session = Depends(database.get_db)):
    if len(request.candidate_ids) != 2:
        raise HTTPException(status_code=400, detail="Exactly two candidate IDs are required")
    
    c1 = db.query(models.Candidate).filter(models.Candidate.id == request.candidate_ids[0]).first()
    c2 = db.query(models.Candidate).filter(models.Candidate.id == request.candidate_ids[1]).first()
    
    if not c1 or not c2:
        raise HTTPException(status_code=404, detail="One or both candidates not found")

    position = None
    if request.position_id:
        position_obj = db.query(models.Position).filter(models.Position.id == request.position_id).first()
        if position_obj:
            position = {
                "title": position_obj.title,
                "department": position_obj.department,
                "description": position_obj.description,
                "required_skills": json.loads(position_obj.required_skills)
            }

    cand1_data = {
        "name": c1.name,
        "summary": c1.summary,
        "skills": json.loads(c1.skills),
        "experience": json.loads(c1.experience)
    }
    
    cand2_data = {
        "name": c2.name,
        "summary": c2.summary,
        "skills": json.loads(c2.skills),
        "experience": json.loads(c2.experience)
    }
    
    result = ai_analyzer.compare_candidates(cand1_data, cand2_data, position)
    return result
