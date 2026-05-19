from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, Body
from sqlalchemy.orm import Session
from typing import List
import json
import models, schemas, database
fromservices import pdf_parser, ai_analyzer

router = APIRouter()

def _log(db: Session, action: str, target_type: str, target_id: int, details: dict = {}):
    log = models.Log(action=action, target_type=target_type, target_id=target_id, details=details)
    db.add(log)
    db.commit()

@router.post("/upload", response_model=schemas.Candidate)
async def upload_cv(file: UploadFile = File(...), db: Session = Depends(database.get_db)):
    content = await file.read()
    text = pdf_parser.extract_text_from_pdf(content)
    
    if not text or not text.strip():
        # Fallback logic / Error logging
        print(f"[Upload] CV {file.filename} parse failed. Text is empty.")
        raise HTTPException(status_code=400, detail="CV içeriği okunamadı veya dosya boş/sadece resimden oluşuyor.")
        
    analysis = ai_analyzer.analyze_cv(text)
    
    email = analysis.get("email")
    phone = analysis.get("phone")
    
    # Blacklist check
    if email or phone:
        bl = db.query(models.Candidate).filter(
            ((models.Candidate.email == email) & (models.Candidate.is_blacklisted == True)) |
            ((models.Candidate.phone == phone) & (models.Candidate.is_blacklisted == True))
        ).first()
        if bl:
            raise HTTPException(status_code=403, detail=f"Aday kara listededir: {bl.blacklist_reason or 'Sebep belirtilmemiş'}")

    db_candidate = models.Candidate(
        name=analysis.get("name", "Bilinmiyor"),
        original_filename=file.filename,
        upload_status="Completed",
        email=email,
        phone=phone,
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
    )
    db.add(db_candidate)
    db.commit()
    db.refresh(db_candidate)
    
    _log(db, "candidate_added", "candidate", db_candidate.id, {"name": db_candidate.name})
    
    return db_candidate

@router.get("/", response_model=List[schemas.Candidate])
def read_candidates(skip: int = 0, limit: int = 200, db: Session = Depends(database.get_db)):
    from sqlalchemy.orm import joinedload
    return db.query(models.Candidate).options(joinedload(models.Candidate.applications).joinedload(models.Application.position)).offset(skip).limit(limit).all()

@router.get("/{candidate_id}", response_model=schemas.Candidate)
def read_candidate(candidate_id: int, db: Session = Depends(database.get_db)):
    from sqlalchemy.orm import joinedload
    c = db.query(models.Candidate).options(joinedload(models.Candidate.applications).joinedload(models.Application.position)).filter(models.Candidate.id == candidate_id).first()
    if not c:
        raise HTTPException(status_code=404, detail="Aday bulunamadı")
    return c

@router.patch("/{candidate_id}/rating")
def update_rating(candidate_id: int, data: schemas.CandidateRatingUpdate, db: Session = Depends(database.get_db)):
    c = db.query(models.Candidate).filter(models.Candidate.id == candidate_id).first()
    if not c:
        raise HTTPException(status_code=404, detail="Aday bulunamadı")
    c.rating = max(1, min(5, data.rating))
    db.commit()
    return {"rating": c.rating}

@router.patch("/{candidate_id}/notes")
def update_notes(candidate_id: int, data: schemas.CandidateNotesUpdate, db: Session = Depends(database.get_db)):
    c = db.query(models.Candidate).filter(models.Candidate.id == candidate_id).first()
    if not c:
        raise HTTPException(status_code=404, detail="Aday bulunamadı")
    c.notes = data.notes
    db.commit()
    return {"notes": c.notes}

@router.patch("/{candidate_id}/favorite")
def toggle_favorite(candidate_id: int, db: Session = Depends(database.get_db)):
    c = db.query(models.Candidate).filter(models.Candidate.id == candidate_id).first()
    if not c:
        raise HTTPException(status_code=404, detail="Aday bulunamadı")
    c.is_favorite = not c.is_favorite
    db.commit()
    return {"is_favorite": c.is_favorite}

@router.patch("/{candidate_id}/blacklist")
def toggle_blacklist(candidate_id: int, reason: str = Body(None, embed=True), db: Session = Depends(database.get_db)):
    c = db.query(models.Candidate).filter(models.Candidate.id == candidate_id).first()
    if not c: raise HTTPException(status_code=404, detail="Aday bulunamadı")
    c.is_blacklisted = not c.is_blacklisted
    c.blacklist_reason = reason if c.is_blacklisted else None
    db.commit()
    return {"is_blacklisted": c.is_blacklisted, "reason": c.blacklist_reason}

@router.delete("/{candidate_id}")
def delete_candidate(candidate_id: int, db: Session = Depends(database.get_db)):
    c = db.query(models.Candidate).filter(models.Candidate.id == candidate_id).first()
    if not c:
        raise HTTPException(status_code=404, detail="Aday bulunamadı")
    db.delete(c)
    db.commit()
    return {"ok": True}

@router.post("/compare", response_model=schemas.CandidateComparisonResponse)
def compare_candidates(request: schemas.CandidateComparisonRequest, db: Session = Depends(database.get_db)):
    if len(request.candidate_ids) != 2:
        raise HTTPException(status_code=400, detail="Tam 2 aday ID gerekli")
    c1 = db.query(models.Candidate).filter(models.Candidate.id == request.candidate_ids[0]).first()
    c2 = db.query(models.Candidate).filter(models.Candidate.id == request.candidate_ids[1]).first()
    if not c1 or not c2:
        raise HTTPException(status_code=404, detail="Aday bulunamadı")
    position = None
    if request.position_id:
        pos = db.query(models.Position).filter(models.Position.id == request.position_id).first()
        if pos:
            position = {"title": pos.title, "department": pos.department, "description": pos.description, "required_skills": pos.required_skills}
    def safe(v): return v if isinstance(v, list) else (json.loads(v) if isinstance(v, str) else [])
    cand1 = {"name": c1.name, "summary": c1.summary or "", "skills": safe(c1.skills), "experience": safe(c1.experience)}
    cand2 = {"name": c2.name, "summary": c2.summary or "", "skills": safe(c2.skills), "experience": safe(c2.experience)}
    return ai_analyzer.compare_candidates(cand1, cand2, position)
